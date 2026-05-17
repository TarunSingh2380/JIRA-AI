"""Write Jira tickets into the Neo4j graph database.

Node labels created:
  :JiraProject  {key, name}
  :JiraTicket   {key, summary, description, status, issue_type, priority,
                 project_key, created, updated, labels, url}
  :JiraUser     {account_id, display_name}

Relationships:
  (:JiraTicket)-[:IN_PROJECT]->(:JiraProject)
  (:JiraTicket)-[:ASSIGNED_TO]->(:JiraUser)
  (:JiraTicket)-[:REPORTED_BY]->(:JiraUser)
  (:JiraTicket)-[:SUBTASK_OF]->(:JiraTicket)   (parent→child links)
"""
from __future__ import annotations

import logging
from typing import Any

from neo4j import AsyncDriver

log = logging.getLogger(__name__)

# ─── Cypher templates ────────────────────────────────────────────────────────

_CYPHER_UPSERT_TICKETS_BATCH = """
UNWIND $tickets AS t
MERGE (jt:JiraTicket {key: t.key})
SET
    jt.summary     = t.summary,
    jt.description = t.description,
    jt.status      = t.status,
    jt.issue_type  = t.issue_type,
    jt.priority    = t.priority,
    jt.project_key = t.project_key,
    jt.created     = t.created,
    jt.updated     = t.updated,
    jt.labels      = t.labels,
    jt.url         = t.url,
    jt.ingested_at = datetime()
WITH jt, t
MERGE (p:JiraProject {key: t.project_key})
MERGE (jt)-[:IN_PROJECT]->(p)
WITH jt, t
FOREACH (u IN t.assignees |
    MERGE (user:JiraUser {account_id: u.account_id})
    ON CREATE SET user.display_name = u.display_name
    MERGE (jt)-[:ASSIGNED_TO]->(user)
)
WITH jt, t
FOREACH (u IN t.reporters |
    MERGE (user:JiraUser {account_id: u.account_id})
    ON CREATE SET user.display_name = u.display_name
    MERGE (jt)-[:REPORTED_BY]->(user)
)
"""

_CYPHER_LINK_SUBTASKS = """
UNWIND $links AS l
MATCH (parent:JiraTicket {key: l.parent_key})
MATCH (child:JiraTicket  {key: l.child_key})
MERGE (child)-[:SUBTASK_OF]->(parent)
"""

_CYPHER_CLEAR_JIRA = """
MATCH (n) WHERE n:JiraTicket OR n:JiraProject OR n:JiraUser
DETACH DELETE n
"""


# ─── ADF / text helpers ──────────────────────────────────────────────────────

def _adf_to_text(node: Any, _depth: int = 0) -> str:
    """Recursively extract plain text from Atlassian Document Format."""
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        parts = [_adf_to_text(child, _depth + 1) for child in node.get("content", [])]
        sep = "\n" if node.get("type") in ("paragraph", "heading", "listItem") else " "
        return sep.join(p for p in parts if p)
    return ""


def _ticket_row(ticket: dict[str, Any], jira_base_url: str) -> dict[str, Any]:
    fields = ticket.get("fields", {}) or {}
    key = ticket.get("key", "")
    project_key = key.rsplit("-", 1)[0] if "-" in key else key

    assignee = fields.get("assignee") or {}
    reporter = fields.get("reporter") or {}

    return {
        "key": key,
        "summary": (fields.get("summary") or "")[:500],
        "description": _adf_to_text(fields.get("description"))[:2000],
        "status": (fields.get("status") or {}).get("name", ""),
        "issue_type": (fields.get("issuetype") or {}).get("name", ""),
        "priority": (fields.get("priority") or {}).get("name", ""),
        "project_key": project_key,
        "created": (fields.get("created") or "")[:19],
        "updated": (fields.get("updated") or "")[:19],
        "labels": fields.get("labels") or [],
        "url": f"{jira_base_url}/browse/{key}",
        "assignees": (
            [{"account_id": assignee["accountId"], "display_name": assignee.get("displayName", "")}]
            if assignee.get("accountId") else []
        ),
        "reporters": (
            [{"account_id": reporter["accountId"], "display_name": reporter.get("displayName", "")}]
            if reporter.get("accountId") else []
        ),
    }


def _subtask_links(tickets: list[dict[str, Any]]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for ticket in tickets:
        fields = ticket.get("fields", {}) or {}
        child_key = ticket.get("key", "")
        parent = fields.get("parent")
        if parent and parent.get("key"):
            links.append({"parent_key": parent["key"], "child_key": child_key})
        for sub in fields.get("subtasks", []) or []:
            sub_key = sub.get("key", "")
            if sub_key:
                links.append({"parent_key": child_key, "child_key": sub_key})
    return [l for l in links if l["parent_key"] and l["child_key"]]


# ─── Public API ──────────────────────────────────────────────────────────────

async def upsert_jira_tickets(
    driver: AsyncDriver,
    tickets: list[dict[str, Any]],
    jira_base_url: str,
    database: str = "neo4j",
    batch_size: int = 200,
    clear_first: bool = False,
) -> int:
    """Merge all tickets into Neo4j. Returns the number of tickets written."""
    if not tickets:
        return 0

    rows = [_ticket_row(t, jira_base_url) for t in tickets]

    async with driver.session(database=database) as session:
        if clear_first:
            await session.run(_CYPHER_CLEAR_JIRA)
            log.info("Cleared existing Jira nodes from Neo4j")

        for i in range(0, len(rows), batch_size):
            chunk = rows[i : i + batch_size]
            await session.run(_CYPHER_UPSERT_TICKETS_BATCH, tickets=chunk)
            log.debug("Wrote Jira batch %d-%d", i, i + len(chunk))

        links = _subtask_links(tickets)
        if links:
            await session.run(_CYPHER_LINK_SUBTASKS, links=links)
            log.debug("Wrote %d subtask links", len(links))

    log.info("Upserted %d Jira tickets to Neo4j", len(rows))
    return len(rows)


def make_neo4j_driver(uri: str, user: str, password: str):
    """Create an async Neo4j driver. Import lazily to avoid hard dep at import time."""
    from neo4j import AsyncGraphDatabase
    return AsyncGraphDatabase.driver(uri, auth=(user, password))
