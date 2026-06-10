"""Review of PRD / Tech-design docs linked in a Jira ticket — with change
detection (MoM follow-up).

Behaviour:
  * Extract labelled links ("PRD: <url>", "TechDoc: <url>") from the ticket.
  * For each link, fetch the document text and hash it (sha256).
  * Compare against the last-stored hash in `doc_reviews (jira_ticket_id, doc_url)`:
      - hash unchanged AND a prior review exists  -> SKIP the LLM, reuse the
        stored review (so the consolidated comment stays complete).
      - hash changed / new                        -> re-review with the LLM.
  * Only re-post the Jira comment if at least one document actually changed.
  * Persist the new hash + review + comment id per (ticket, doc_url) via upsert.

This means ordinary ticket edits (status, assignee, labels, etc.) no longer
trigger a re-review — only a real change to the linked document does.

Requires the `content_hash` column + `(jira_ticket_id, doc_url)` unique key from
`migrations/2026_doc_reviews_content_hash.sql`.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

import requests

log = logging.getLogger(__name__)

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "https://ramfincorp.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_TIMEOUT = 30
DATABASE_URL = os.environ.get("DATABASE_URL", "")

COMMENT_MARKER = "AI-GOVERNOR-DOCREVIEW-V1"

LINK_PATTERN = re.compile(
    r"(?P<label>PRD|Tech\s*Doc|Technical\s*Design(?:\s*Doc)?|Design\s*Doc)"
    r"\s*[:\-]\s*(?P<url>https?://\S+)",
    re.IGNORECASE,
)

REVIEW_SYSTEM_PROMPT = (
    "You are a senior engineering reviewer at a fintech company. You are given the "
    "text of a product or technical design document linked from a Jira ticket. "
    "Review it concisely and concretely. Cover: completeness, clarity, missing "
    "edge cases / NFRs, security & compliance gaps, testability, and any "
    "ambiguous requirements. Output Jira wiki markup with these sections: "
    "*Summary* (2-3 lines), *Strengths* (bullets), *Gaps & Risks* (bullets, most "
    "important first), *Recommended changes* (numbered, actionable). Do not invent "
    "facts not present in the document; if a critical section is absent, say so."
)


@dataclass
class DocLink:
    label: str
    url: str
    text: str = ""
    error: str = ""
    content_hash: str = ""
    review: str = ""
    changed: bool = False          # content differs from last stored hash
    reviewed_now: bool = False     # LLM was actually called this run


# ─────────────────────────────────────────────────────────────────────────────
# Link extraction
# ─────────────────────────────────────────────────────────────────────────────
def extract_doc_links(description: Any) -> list[DocLink]:
    text = _description_to_text(description)
    links: list[DocLink] = []
    seen: set[str] = set()
    for m in LINK_PATTERN.finditer(text):
        url = m.group("url").rstrip(").,;>]")
        if url in seen:
            continue
        seen.add(url)
        raw = m.group("label").lower().replace(" ", "")
        label = "PRD" if raw.startswith("prd") else "TechDoc"
        links.append(DocLink(label=label, url=url))
    return links


def _description_to_text(description: Any) -> str:
    if isinstance(description, str):
        return description
    if isinstance(description, dict):
        parts: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "text":
                    parts.append(node.get("text", ""))
                for mark in node.get("marks", []) or []:
                    href = (mark.get("attrs") or {}).get("href")
                    if href:
                        parts.append(href)
                for child in node.get("content", []) or []:
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)

        walk(description)
        return "\n".join(parts)
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Document fetch + hashing
# ─────────────────────────────────────────────────────────────────────────────
def _normalise_gdoc(url: str) -> str:
    m = re.search(r"docs\.google\.com/document/d/([A-Za-z0-9_-]+)", url)
    if m:
        return f"https://docs.google.com/document/d/{m.group(1)}/export?format=txt"
    return url


def fetch_doc_text(url: str, limit_chars: int = 60_000) -> tuple[str, str]:
    fetch_url = _normalise_gdoc(url)
    try:
        resp = requests.get(fetch_url, timeout=JIRA_TIMEOUT, allow_redirects=True)
    except requests.RequestException as exc:
        return "", f"fetch failed: {exc}"
    if resp.status_code in (401, 403):
        return "", "document is not publicly accessible (auth required)"
    if resp.status_code >= 400:
        return "", f"fetch failed: HTTP {resp.status_code}"
    ctype = resp.headers.get("Content-Type", "")
    if "html" in ctype and "google.com" in fetch_url:
        return "", "document is not publicly accessible (auth required)"
    text = resp.text
    if "html" in ctype:
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
    return text.strip()[:limit_chars], ""


def _hash_text(text: str) -> str:
    # Normalise whitespace so trivial reflow doesn't read as a change.
    normalised = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# doc_reviews persistence (change-detection cache)
# ─────────────────────────────────────────────────────────────────────────────
def _connect():
    import psycopg  # local import: module is usable without a DB present

    return psycopg.connect(DATABASE_URL)


def ensure_doc_reviews_schema() -> None:
    """Idempotent guard so the app can self-heal if the migration didn't run."""
    if not DATABASE_URL:
        return
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("ALTER TABLE doc_reviews ADD COLUMN IF NOT EXISTS content_hash text")
            cur.execute("ALTER TABLE doc_reviews ADD COLUMN IF NOT EXISTS review_count integer NOT NULL DEFAULT 0")
            cur.execute("ALTER TABLE doc_reviews ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT now()")
            cur.execute(
                "DO $$ BEGIN "
                "IF NOT EXISTS (SELECT 1 FROM pg_constraint "
                "WHERE conname = 'doc_reviews_ticket_url_key') THEN "
                "ALTER TABLE doc_reviews ADD CONSTRAINT doc_reviews_ticket_url_key "
                "UNIQUE (jira_ticket_id, doc_url); END IF; END $$;"
            )
            conn.commit()
    except Exception:  # noqa: BLE001 - never block a review on schema self-heal
        log.exception("ensure_doc_reviews_schema failed; run the SQL migration manually")


def _load_existing(ticket: str, urls: list[str]) -> dict[str, dict[str, Any]]:
    """url -> {content_hash, llm_review, comment_id} for prior reviews."""
    if not DATABASE_URL or not urls:
        return {}
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT doc_url, content_hash, llm_review, comment_id "
                "FROM doc_reviews WHERE jira_ticket_id = %s AND doc_url = ANY(%s)",
                (ticket, urls),
            )
            return {
                row[0]: {"content_hash": row[1], "llm_review": row[2], "comment_id": row[3]}
                for row in cur.fetchall()
            }
    except Exception:  # noqa: BLE001
        log.exception("_load_existing failed")
        return {}


def _upsert_review(ticket: str, link: DocLink, comment_id: str | None) -> None:
    if not DATABASE_URL:
        return
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO doc_reviews
                    (jira_ticket_id, doc_url, doc_type, llm_review, comment_id,
                     content_hash, review_count, scanned_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, 1, now(), now())
                ON CONFLICT (jira_ticket_id, doc_url) DO UPDATE SET
                    doc_type     = EXCLUDED.doc_type,
                    llm_review   = EXCLUDED.llm_review,
                    comment_id   = EXCLUDED.comment_id,
                    content_hash = EXCLUDED.content_hash,
                    review_count = doc_reviews.review_count + 1,
                    scanned_at   = now(),
                    updated_at   = now()
                """,
                (ticket, link.url, link.label, link.review, comment_id, link.content_hash),
            )
            conn.commit()
    except Exception:  # noqa: BLE001
        log.exception("_upsert_review failed for %s %s", ticket, link.url)


def _touch_scanned(ticket: str, url: str) -> None:
    """Mark an unchanged doc as checked-now without bumping review_count."""
    if not DATABASE_URL:
        return
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE doc_reviews SET scanned_at = now() "
                "WHERE jira_ticket_id = %s AND doc_url = %s",
                (ticket, url),
            )
            conn.commit()
    except Exception:  # noqa: BLE001
        log.exception("_touch_scanned failed")


# ─────────────────────────────────────────────────────────────────────────────
# Reviewer
# ─────────────────────────────────────────────────────────────────────────────
class DocReviewer:
    def __init__(self, settings: Any = None, prompt_store: Any = None, llm_client: Any = None):
        self._llm = llm_client
        self._settings = settings

    def _llm_complete(self, system: str, user: str) -> str:
        if self._llm is not None:
            return self._llm.complete(system, user).strip()
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        model = os.environ.get("DOC_REVIEW_MODEL", "claude-sonnet-4-5")
        msg = client.messages.create(
            model=model, max_tokens=2000, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()

    def review(self, issue_key: str, description: Any) -> dict[str, Any]:
        ensure_doc_reviews_schema()
        links = extract_doc_links(description)
        if not links:
            return {"issueKey": issue_key, "reviewed": 0, "unchanged": 0,
                    "commentPosted": False, "reason": "no PRD/TechDoc links found"}

        existing = _load_existing(issue_key, [l.url for l in links])

        # 1. Fetch + classify each link as changed / unchanged / error.
        for link in links:
            link.text, link.error = fetch_doc_text(link.url)
            if link.error:
                continue  # leave cache untouched; surface the error in the comment
            link.content_hash = _hash_text(link.text)
            prior = existing.get(link.url)
            if prior and prior.get("content_hash") == link.content_hash and prior.get("llm_review"):
                # Unchanged: reuse the stored review, no LLM call.
                link.changed = False
                link.review = prior["llm_review"]
                _touch_scanned(issue_key, link.url)
            else:
                link.changed = True  # new doc or content differs -> review below

        changed = [l for l in links if l.changed]
        errored = [l for l in links if l.error]

        # 2. If nothing changed, skip the LLM and the comment entirely.
        if not changed:
            return {
                "issueKey": issue_key,
                "reviewed": 0,
                "unchanged": len([l for l in links if not l.error and not l.changed]),
                "skipped": [{"url": l.url, "error": l.error} for l in errored],
                "commentPosted": False,
                "reason": "no document changes since last review",
            }

        # 3. Review only the changed docs.
        for link in changed:
            user_prompt = (
                f"Ticket: {issue_key}\nDocument type: {link.label}\nSource URL: {link.url}\n\n"
                f"--- DOCUMENT TEXT START ---\n{link.text}\n--- DOCUMENT TEXT END ---"
            )
            link.review = self._llm_complete(REVIEW_SYSTEM_PROMPT, user_prompt)
            link.reviewed_now = True

        # 4. Rebuild the consolidated comment from ALL links (fresh + cached).
        blocks: list[str] = []
        for link in links:
            if link.error:
                blocks.append(
                    f"h4. {link.label} review — [link|{link.url}]\n"
                    f"{{panel:bgColor=#FFEBE6}}Could not review automatically: {link.error}.{{panel}}"
                )
            else:
                tag = " _(updated)_" if link.reviewed_now else " _(unchanged)_"
                blocks.append(f"h4. {link.label} review{tag} — [link|{link.url}]\n{link.review}")

        comment_body = (
            f"h3. 📝 AI Governor — Document Review ({len(links)})\n"
            f"_Automated review of PRD / Tech-design docs linked on {issue_key}._\n"
            f"{{anchor:{COMMENT_MARKER}}}\n\n" + "\n\n----\n\n".join(blocks)
        )
        comment_id = _upsert_comment(issue_key, comment_body)

        # 5. Persist new hash + review for the changed docs.
        for link in changed:
            _upsert_review(issue_key, link, comment_id)

        return {
            "issueKey": issue_key,
            "reviewed": len(changed),
            "unchanged": len([l for l in links if not l.error and not l.changed]),
            "skipped": [{"url": l.url, "error": l.error} for l in errored],
            "commentPosted": bool(comment_id),
        }


def _upsert_comment(issue_key: str, body: str) -> str | None:
    """Create or update the marker-anchored review comment; return its id."""
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    base = f"{JIRA_BASE_URL}/rest/api/2/issue/{issue_key}/comment"
    existing_id = None
    try:
        listing = requests.get(f"{base}?maxResults=100", auth=auth,
                               headers={"Accept": "application/json"}, timeout=JIRA_TIMEOUT)
        if listing.status_code < 400:
            for c in listing.json().get("comments", []):
                if COMMENT_MARKER in (c.get("body") or ""):
                    existing_id = c.get("id")
                    break
        method = requests.put if existing_id else requests.post
        url = f"{base}/{existing_id}" if existing_id else base
        resp = method(url, auth=auth,
                      headers={"Accept": "application/json", "Content-Type": "application/json"},
                      json={"body": body}, timeout=JIRA_TIMEOUT)
        if resp.status_code < 400:
            return (resp.json().get("id") if resp.content else None) or existing_id
        return existing_id
    except requests.RequestException:
        return existing_id
