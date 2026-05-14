import os
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv


load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")    

# Keep using same .env key.
# Change only this value in .env to export another Jira space/project.
JIRA_PROJECT_KEY = os.getenv("JIRA_TEST_PROJECT_KEY", "")

OUTPUT_DIR = "jira_ticket_exports"
OUTPUT_FILE = f"{JIRA_PROJECT_KEY}_tickets_export_nested.json"

AUTH = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


# --------------------------------------------------
# Basic helpers
# --------------------------------------------------

def validate_env() -> None:
    missing = []

    if not JIRA_BASE_URL:
        missing.append("JIRA_BASE_URL")

    if not JIRA_EMAIL:
        missing.append("JIRA_EMAIL")

    if not JIRA_API_TOKEN:
        missing.append("JIRA_API_TOKEN")

    if not JIRA_PROJECT_KEY:
        missing.append("JIRA_TEST_PROJECT_KEY")

    if missing:
        raise RuntimeError(f"Missing .env values: {', '.join(missing)}")


def save_json(filename: str, data: Any) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved export: {path}")


def jira_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{JIRA_BASE_URL}{path}"

    response = requests.get(
        url,
        headers=HEADERS,
        auth=AUTH,
        params=params,
        timeout=60,
    )

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", "5"))
        print(f"Rate limited. Sleeping for {retry_after} seconds...")
        time.sleep(retry_after)
        return jira_get(path, params)

    if response.status_code >= 400:
        print("Jira API request failed")
        print("URL:", url)
        print("Params:", params)
        print("Status:", response.status_code)
        print("Response:", response.text)
        response.raise_for_status()

    if not response.text:
        return {}

    return response.json()


# --------------------------------------------------
# Jira fetch functions
# --------------------------------------------------

def get_myself() -> Dict[str, Any]:
    return jira_get("/rest/api/3/myself")


def get_project(project_key: str) -> Dict[str, Any]:
    return jira_get(f"/rest/api/3/project/{project_key}")


def get_all_fields_map() -> Dict[str, Dict[str, Any]]:
    fields = jira_get("/rest/api/3/field")

    field_map = {}

    for field in fields:
        field_map[field.get("id")] = {
            "id": field.get("id"),
            "name": field.get("name"),
            "custom": field.get("custom", False),
            "schema": field.get("schema", {}),
        }

    return field_map


def fetch_all_project_issues(project_key: str) -> List[Dict[str, Any]]:
    """
    Fetches all issues/work items from one Jira space/project.

    Important:
    This includes main tickets and subtasks.

    We fetch all first, then nest subtasks under their parents.
    """
    all_issues = []
    next_page_token = None
    max_results = 100

    while True:
        params = {
            "jql": f'project = "{project_key}" ORDER BY created ASC',
            "maxResults": max_results,
            "fields": "*all",
            "expand": "names,schema,renderedFields",
        }

        if next_page_token:
            params["nextPageToken"] = next_page_token

        data = jira_get("/rest/api/3/search/jql", params=params)

        issues = data.get("issues", [])
        all_issues.extend(issues)

        print(f"Fetched {len(all_issues)} Jira items so far...")

        next_page_token = data.get("nextPageToken")

        if not next_page_token:
            break

    return all_issues


def fetch_comments(issue_key: str) -> List[Dict[str, Any]]:
    comments = []
    start_at = 0
    max_results = 100

    while True:
        data = jira_get(
            f"/rest/api/3/issue/{issue_key}/comment",
            params={
                "startAt": start_at,
                "maxResults": max_results,
                "orderBy": "created",
            },
        )

        batch = data.get("comments", [])
        comments.extend(batch)

        if start_at + max_results >= data.get("total", 0):
            break

        start_at += max_results

    return comments


def fetch_worklogs(issue_key: str) -> List[Dict[str, Any]]:
    worklogs = []
    start_at = 0
    max_results = 100

    while True:
        data = jira_get(
            f"/rest/api/3/issue/{issue_key}/worklog",
            params={
                "startAt": start_at,
                "maxResults": max_results,
            },
        )

        batch = data.get("worklogs", [])
        worklogs.extend(batch)

        if start_at + max_results >= data.get("total", 0):
            break

        start_at += max_results

    return worklogs


def fetch_changelog(issue_key: str) -> List[Dict[str, Any]]:
    changelog = []
    start_at = 0
    max_results = 100

    while True:
        data = jira_get(
            f"/rest/api/3/issue/{issue_key}/changelog",
            params={
                "startAt": start_at,
                "maxResults": max_results,
            },
        )

        batch = data.get("values", [])
        changelog.extend(batch)

        if data.get("isLast", True):
            break

        start_at += max_results

    return changelog


# --------------------------------------------------
# Simplification helpers
# --------------------------------------------------

def simple_user(user: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(user, dict):
        return None

    return {
        "account_id": user.get("accountId"),
        "display_name": user.get("displayName"),
        "email": user.get("emailAddress"),
        "active": user.get("active"),
    }


def simple_named_obj(obj: Any) -> Any:
    if not isinstance(obj, dict):
        return obj

    return {
        "id": obj.get("id"),
        "name": obj.get("name"),
        "key": obj.get("key"),
        "value": obj.get("value"),
    }


def simplify_adf(value: Any) -> Any:
    """
    Keeps Jira ADF as-is so we do not lose description/comment formatting.
    """
    return value


def simplify_comments(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    simplified = []

    for comment in comments:
        simplified.append({
            "id": comment.get("id"),
            "author": simple_user(comment.get("author")),
            "created": comment.get("created"),
            "updated": comment.get("updated"),
            "body": simplify_adf(comment.get("body")),
        })

    return simplified


def simplify_worklogs(worklogs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    simplified = []

    for worklog in worklogs:
        simplified.append({
            "id": worklog.get("id"),
            "author": simple_user(worklog.get("author")),
            "created": worklog.get("created"),
            "updated": worklog.get("updated"),
            "started": worklog.get("started"),
            "time_spent": worklog.get("timeSpent"),
            "time_spent_seconds": worklog.get("timeSpentSeconds"),
            "comment": simplify_adf(worklog.get("comment")),
        })

    return simplified


def simplify_changelog(changelog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    simplified = []

    for change in changelog:
        simplified.append({
            "id": change.get("id"),
            "author": simple_user(change.get("author")),
            "created": change.get("created"),
            "items": [
                {
                    "field": item.get("field"),
                    "field_type": item.get("fieldtype"),
                    "from": item.get("fromString"),
                    "to": item.get("toString"),
                }
                for item in change.get("items", [])
            ],
        })

    return simplified


def simplify_attachments(attachments: Any) -> List[Dict[str, Any]]:
    if not isinstance(attachments, list):
        return []

    simplified = []

    for attachment in attachments:
        simplified.append({
            "id": attachment.get("id"),
            "filename": attachment.get("filename"),
            "mime_type": attachment.get("mimeType"),
            "size": attachment.get("size"),
            "created": attachment.get("created"),
            "author": simple_user(attachment.get("author")),
            "content_url": attachment.get("content"),
            "thumbnail_url": attachment.get("thumbnail"),
        })

    return simplified


def simplify_issue_links(issue_links: Any) -> List[Dict[str, Any]]:
    if not isinstance(issue_links, list):
        return []

    simplified = []

    for link in issue_links:
        inward = link.get("inwardIssue")
        outward = link.get("outwardIssue")

        simplified.append({
            "id": link.get("id"),
            "type": link.get("type", {}).get("name"),
            "inward_issue": {
                "key": inward.get("key"),
                "summary": inward.get("fields", {}).get("summary"),
                "status": inward.get("fields", {}).get("status", {}).get("name"),
            } if isinstance(inward, dict) else None,
            "outward_issue": {
                "key": outward.get("key"),
                "summary": outward.get("fields", {}).get("summary"),
                "status": outward.get("fields", {}).get("status", {}).get("name"),
            } if isinstance(outward, dict) else None,
        })

    return simplified


def simplify_custom_fields(
    fields: Dict[str, Any],
    names: Dict[str, str],
    field_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Keeps only non-empty custom fields.
    """
    custom_fields = {}

    for field_id, value in fields.items():
        if not field_id.startswith("customfield_"):
            continue

        if value in [None, "", [], {}]:
            continue

        field_name = names.get(field_id) or field_map.get(field_id, {}).get("name") or field_id

        custom_fields[field_id] = {
            "name": field_name,
            "value": value,
        }

    return custom_fields


def get_issue_type_name(issue: Dict[str, Any]) -> str:
    issue_type = issue.get("type") or {}

    if isinstance(issue_type, dict):
        return issue_type.get("name", "")

    return ""


def is_subtask(issue: Dict[str, Any]) -> bool:
    """
    Detects whether normalized issue is a subtask.

    We check both:
    1. Issue type name = Subtask / Sub-task
    2. parent exists
    """
    issue_type_name = get_issue_type_name(issue).lower()
    has_parent = bool(issue.get("parent"))

    return issue_type_name in ["subtask", "sub-task"] or has_parent


# --------------------------------------------------
# Normalization
# --------------------------------------------------

def normalize_issue(issue: Dict[str, Any], field_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    fields = issue.get("fields", {})
    names = issue.get("names", {})
    rendered_fields = issue.get("renderedFields", {})

    issue_key = issue.get("key")

    comments = fetch_comments(issue_key)
    worklogs = fetch_worklogs(issue_key)
    changelog = fetch_changelog(issue_key)

    project = fields.get("project") if isinstance(fields.get("project"), dict) else {}
    status = fields.get("status") if isinstance(fields.get("status"), dict) else {}
    parent = fields.get("parent") if isinstance(fields.get("parent"), dict) else None

    normalized = {
        "id": issue.get("id"),
        "key": issue_key,
        "url": f"{JIRA_BASE_URL}/browse/{issue_key}",

        "project": {
            "id": project.get("id"),
            "key": project.get("key"),
            "name": project.get("name"),
        },

        "title": fields.get("summary"),
        "description": simplify_adf(fields.get("description")),
        "description_rendered": rendered_fields.get("description"),

        "type": simple_named_obj(fields.get("issuetype")),
        "status": simple_named_obj(fields.get("status")),
        "status_category": simple_named_obj(status.get("statusCategory")),
        "priority": simple_named_obj(fields.get("priority")),
        "resolution": simple_named_obj(fields.get("resolution")),

        "assignee": simple_user(fields.get("assignee")),
        "reporter": simple_user(fields.get("reporter")),
        "creator": simple_user(fields.get("creator")),

        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "due_date": fields.get("duedate"),
        "resolution_date": fields.get("resolutiondate"),

        "labels": fields.get("labels") or [],
        "components": [
            simple_named_obj(component)
            for component in fields.get("components", []) or []
        ],
        "fix_versions": [
            simple_named_obj(version)
            for version in fields.get("fixVersions", []) or []
        ],
        "affected_versions": [
            simple_named_obj(version)
            for version in fields.get("versions", []) or []
        ],

        "parent": {
            "id": parent.get("id"),
            "key": parent.get("key"),
            "summary": parent.get("fields", {}).get("summary"),
        } if parent else None,

        # This will be replaced later for main tickets.
        # For subtasks, this remains empty unless Jira has nested subtasks.
        "subtasks": [],

        "issue_links": simplify_issue_links(fields.get("issuelinks")),
        "attachments": simplify_attachments(fields.get("attachment")),

        "comments": simplify_comments(comments),
        "worklogs": simplify_worklogs(worklogs),
        "changelog": simplify_changelog(changelog),

        "watch_count": (
            fields.get("watches", {}).get("watchCount")
            if isinstance(fields.get("watches"), dict)
            else None
        ),
        "vote_count": (
            fields.get("votes", {}).get("votes")
            if isinstance(fields.get("votes"), dict)
            else None
        ),

        "time_tracking": fields.get("timetracking"),
        "progress": fields.get("progress"),
        "aggregate_progress": fields.get("aggregateprogress"),

        "custom_fields": simplify_custom_fields(fields, names, field_map),
    }

    return normalized


# --------------------------------------------------
# Main ticket / subtask nesting
# --------------------------------------------------

def make_subtask_summary(subtask: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keeps subtask information simple but useful.

    We do not remove important metadata; we just avoid repeating unnecessary project-level fields.
    """
    return {
        "id": subtask.get("id"),
        "key": subtask.get("key"),
        "url": subtask.get("url"),
        "title": subtask.get("title"),
        "description": subtask.get("description"),
        "description_rendered": subtask.get("description_rendered"),
        "type": subtask.get("type"),
        "status": subtask.get("status"),
        "status_category": subtask.get("status_category"),
        "priority": subtask.get("priority"),
        "assignee": subtask.get("assignee"),
        "reporter": subtask.get("reporter"),
        "creator": subtask.get("creator"),
        "created": subtask.get("created"),
        "updated": subtask.get("updated"),
        "due_date": subtask.get("due_date"),
        "resolution": subtask.get("resolution"),
        "resolution_date": subtask.get("resolution_date"),
        "labels": subtask.get("labels"),
        "comments": subtask.get("comments"),
        "worklogs": subtask.get("worklogs"),
        "changelog": subtask.get("changelog"),
        "attachments": subtask.get("attachments"),
        "custom_fields": subtask.get("custom_fields"),
        "parent": subtask.get("parent"),
    }


def nest_subtasks_under_parents(
    normalized_issues: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns:
    1. main_tickets: tickets that are not subtasks, with their subtasks nested
    2. subtasks: all detected subtasks
    3. orphan_subtasks: subtasks whose parent was not present in export
    """
    main_tickets = []
    subtasks = []

    for issue in normalized_issues:
        if is_subtask(issue):
            subtasks.append(issue)
        else:
            main_tickets.append(issue)

    main_ticket_by_key = {
        ticket.get("key"): ticket
        for ticket in main_tickets
    }

    orphan_subtasks = []

    for subtask in subtasks:
        parent_key = (subtask.get("parent") or {}).get("key")

        if parent_key and parent_key in main_ticket_by_key:
            main_ticket_by_key[parent_key].setdefault("subtasks", [])
            main_ticket_by_key[parent_key]["subtasks"].append(make_subtask_summary(subtask))
        else:
            orphan_subtasks.append(subtask)

    for ticket in main_tickets:
        ticket["subtask_count"] = len(ticket.get("subtasks", []))

    return main_tickets, subtasks, orphan_subtasks


def build_status_summary(main_tickets: List[Dict[str, Any]], subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    main_status_count = {}
    subtask_status_count = {}

    for ticket in main_tickets:
        status_name = (ticket.get("status") or {}).get("name") or "Unknown"
        main_status_count[status_name] = main_status_count.get(status_name, 0) + 1

    for subtask in subtasks:
        status_name = (subtask.get("status") or {}).get("name") or "Unknown"
        subtask_status_count[status_name] = subtask_status_count.get(status_name, 0) + 1

    return {
        "main_tickets_by_status": main_status_count,
        "subtasks_by_status": subtask_status_count,
    }


# --------------------------------------------------
# Runner
# --------------------------------------------------

def main() -> None:
    validate_env()

    print("Starting Jira space/project ticket export...")
    print(f"Base URL: {JIRA_BASE_URL}")
    print(f"Space/project key: {JIRA_PROJECT_KEY}")
    print("Mode: READ ONLY. This script will not create/update/delete anything.")

    myself = get_myself()
    print(f"Authenticated as: {myself.get('displayName')} / {myself.get('emailAddress')}")

    project = get_project(JIRA_PROJECT_KEY)
    print(f"Exporting from: {project.get('name')} / {project.get('key')}")

    print("Fetching Jira field map...")
    field_map = get_all_fields_map()
    print(f"Fields found: {len(field_map)}")

    print("Fetching all Jira items from this space/project...")
    raw_issues = fetch_all_project_issues(JIRA_PROJECT_KEY)

    print(f"Total Jira items found, including subtasks: {len(raw_issues)}")

    normalized_issues = []

    for index, issue in enumerate(raw_issues, start=1):
        issue_key = issue.get("key")
        print(f"Normalizing {index}/{len(raw_issues)}: {issue_key}")
        normalized_issues.append(normalize_issue(issue, field_map))

    main_tickets, subtasks, orphan_subtasks = nest_subtasks_under_parents(normalized_issues)
    status_summary = build_status_summary(main_tickets, subtasks)

    export_data = {
        "source": "jira",
        "base_url": JIRA_BASE_URL,
        "project": {
            "id": project.get("id"),
            "key": project.get("key"),
            "name": project.get("name"),
            "project_type_key": project.get("projectTypeKey"),
            "style": project.get("style"),
            "simplified": project.get("simplified"),
        },

        # Realistic counts
        "total_items_in_jira": len(normalized_issues),
        "main_tickets_count": len(main_tickets),
        "subtasks_count": len(subtasks),
        "orphan_subtasks_count": len(orphan_subtasks),

        "status_summary": status_summary,

        # Main tickets only, with subtasks nested inside parent ticket
        "tickets": main_tickets,

        # Usually this should be empty.
        # If parent ticket is not visible/exported, its subtask appears here.
        "orphan_subtasks": [
            make_subtask_summary(subtask)
            for subtask in orphan_subtasks
        ],
    }

    save_json(OUTPUT_FILE, export_data)

    print("Done.")
    print(f"Total Jira items: {len(normalized_issues)}")
    print(f"Main tickets: {len(main_tickets)}")
    print(f"Subtasks: {len(subtasks)}")
    print(f"Orphan subtasks: {len(orphan_subtasks)}")
    print(f"Output file: {os.path.join(OUTPUT_DIR, OUTPUT_FILE)}")


if __name__ == "__main__":
    main()