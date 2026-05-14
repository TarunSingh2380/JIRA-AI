import os
import json
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv


load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_TEST_PROJECT_KEY = os.getenv("JIRA_TEST_PROJECT_KEY", "")
JIRA_TARGET_TRANSITION_NAME = os.getenv("JIRA_TARGET_TRANSITION_NAME", "").strip()
JIRA_CLEANUP_CREATED_ISSUES = os.getenv("JIRA_CLEANUP_CREATED_ISSUES", "false").lower() == "true"

OUTPUT_DIR = "jira_api_poc_outputs"

AUTH = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


# -----------------------------
# Utility helpers
# -----------------------------

def validate_env() -> None:
    missing = []

    if not JIRA_BASE_URL:
        missing.append("JIRA_BASE_URL")

    if not JIRA_EMAIL:
        missing.append("JIRA_EMAIL")

    if not JIRA_API_TOKEN:
        missing.append("JIRA_API_TOKEN")

    if not JIRA_TEST_PROJECT_KEY:
        missing.append("JIRA_TEST_PROJECT_KEY")

    if missing:
        raise RuntimeError(f"Missing required .env values: {', '.join(missing)}")


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_json(filename: str, data: Any) -> None:
    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved: {path}")


def jira_request(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
    expected_statuses: Optional[set] = None,
    allow_fail: bool = False,
) -> Tuple[bool, Any, int]:
    """
    Returns:
        success: bool
        data: parsed JSON or error object
        status_code: int
    """

    url = f"{JIRA_BASE_URL}{path}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=HEADERS,
            auth=AUTH,
            params=params,
            json=payload,
            timeout=60,
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "5"))
            print(f"Rate limited by Jira. Sleeping {retry_after} seconds...")
            time.sleep(retry_after)

            response = requests.request(
                method=method,
                url=url,
                headers=HEADERS,
                auth=AUTH,
                params=params,
                json=payload,
                timeout=60,
            )

        if response.text:
            try:
                data = response.json()
            except json.JSONDecodeError:
                data = {"raw_response": response.text}
        else:
            data = {}

        if expected_statuses and response.status_code not in expected_statuses:
            error_data = {
                "success": False,
                "method": method,
                "url": url,
                "params": params,
                "payload": payload,
                "status_code": response.status_code,
                "response": data,
            }

            if allow_fail:
                return False, error_data, response.status_code

            raise RuntimeError(json.dumps(error_data, indent=2, ensure_ascii=False))

        return True, data, response.status_code

    except requests.RequestException as exc:
        error_data = {
            "success": False,
            "method": method,
            "url": url,
            "params": params,
            "payload": payload,
            "error": str(exc),
        }

        if allow_fail:
            return False, error_data, 0

        raise


def adf_text(text: str) -> Dict[str, Any]:
    """
    Jira Cloud rich-text description/comment format.
    """
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                    }
                ],
            }
        ],
    }


# -----------------------------
# Read tests
# -----------------------------

def test_authentication() -> Dict[str, Any]:
    success, data, status = jira_request(
        "GET",
        "/rest/api/3/myself",
        expected_statuses={200},
    )

    return {
        "test": "authentication",
        "success": success,
        "status": status,
        "data": data,
    }


def get_visible_projects() -> List[Dict[str, Any]]:
    all_projects = []
    start_at = 0
    max_results = 50

    while True:
        success, data, _ = jira_request(
            "GET",
            "/rest/api/3/project/search",
            params={
                "startAt": start_at,
                "maxResults": max_results,
            },
            expected_statuses={200},
        )

        values = data.get("values", [])
        all_projects.extend(values)

        if data.get("isLast", True):
            break

        start_at += max_results

    return all_projects


def get_project_permissions(project_key: str) -> Dict[str, Any]:
    success, data, status = jira_request(
        "GET",
        "/rest/api/3/mypermissions",
        params={
            "projectKey": project_key,
        },
        expected_statuses={200},
        allow_fail=True,
    )

    return {
        "test": "project_permissions",
        "success": success,
        "status": status,
        "data": data,
    }


def get_all_fields() -> List[Dict[str, Any]]:
    success, data, _ = jira_request(
        "GET",
        "/rest/api/3/field",
        expected_statuses={200},
    )

    return data


def search_issues_jql(
    jql: str,
    max_results: int = 20,
    fields: str = "*all",
) -> Dict[str, Any]:
    """
    Uses enhanced JQL search endpoint.
    Good for checking whether your account can fetch tickets/work items.
    """
    all_issues = []
    next_page_token = None

    while True:
        params = {
            "jql": jql,
            "maxResults": min(max_results, 100),
            "fields": fields,
            "expand": "names,schema,renderedFields",
        }

        if next_page_token:
            params["nextPageToken"] = next_page_token

        success, data, status = jira_request(
            "GET",
            "/rest/api/3/search/jql",
            params=params,
            expected_statuses={200},
            allow_fail=True,
        )

        if not success:
            return {
                "success": False,
                "status": status,
                "error": data,
                "issues": all_issues,
            }

        batch = data.get("issues", [])
        all_issues.extend(batch)

        next_page_token = data.get("nextPageToken")

        if not next_page_token:
            break

        if len(all_issues) >= max_results:
            break

    return {
        "success": True,
        "jql": jql,
        "total_fetched": len(all_issues),
        "issues": all_issues[:max_results],
    }


def get_create_metadata(project_key: str) -> Dict[str, Any]:
    """
    Used to find available issue/work-item types and required fields.
    """
    success, data, status = jira_request(
        "GET",
        "/rest/api/3/issue/createmeta",
        params={
            "projectKeys": project_key,
            "expand": "projects.issuetypes.fields",
        },
        expected_statuses={200},
        allow_fail=True,
    )

    return {
        "success": success,
        "status": status,
        "data": data,
    }


def pick_issue_type(create_meta: Dict[str, Any]) -> Dict[str, Any]:
    projects = create_meta.get("data", {}).get("projects", [])

    if not projects:
        raise RuntimeError(
            "No create metadata found for this test space/project. "
            "Check that your account has Create Issues permission."
        )

    issue_types = projects[0].get("issuetypes", [])

    if not issue_types:
        raise RuntimeError("No issue types found in create metadata.")

    preferred_names = [
        "Task",
        "Story",
        "Bug",
        "Improvement",
        "Sub-task",
    ]

    for name in preferred_names:
        for issue_type in issue_types:
            if issue_type.get("name", "").lower() == name.lower():
                return issue_type

    return issue_types[0]


def extract_required_fields(issue_type_meta: Dict[str, Any]) -> Dict[str, Any]:
    fields = issue_type_meta.get("fields", {})
    required_fields = {}

    for field_id, field_data in fields.items():
        if field_data.get("required"):
            required_fields[field_id] = {
                "name": field_data.get("name"),
                "schema": field_data.get("schema"),
                "allowedValues": field_data.get("allowedValues"),
            }

    return required_fields


# -----------------------------
# Write tests inside test space only
# -----------------------------

def create_test_issue(
    project_key: str,
    issue_type_id: str,
    summary: str,
    description: str,
) -> Dict[str, Any]:
    payload = {
        "fields": {
            "project": {
                "key": project_key,
            },
            "issuetype": {
                "id": issue_type_id,
            },
            "summary": summary,
            "description": adf_text(description),
            "labels": [
                "ai-governor-test",
                "api-poc",
            ],
        }
    }

    success, data, status = jira_request(
        "POST",
        "/rest/api/3/issue",
        payload=payload,
        expected_statuses={201},
        allow_fail=True,
    )

    return {
        "test": "create_issue",
        "success": success,
        "status": status,
        "data": data,
        "payload_used": payload,
    }


def get_issue_full(issue_key: str) -> Dict[str, Any]:
    success, data, status = jira_request(
        "GET",
        f"/rest/api/3/issue/{issue_key}",
        params={
            "fields": "*all",
            "expand": "names,schema,renderedFields,changelog",
        },
        expected_statuses={200},
        allow_fail=True,
    )

    return {
        "test": "get_issue_full",
        "success": success,
        "status": status,
        "data": data,
    }


def add_comment(issue_key: str, comment_text: str) -> Dict[str, Any]:
    payload = {
        "body": adf_text(comment_text),
    }

    success, data, status = jira_request(
        "POST",
        f"/rest/api/3/issue/{issue_key}/comment",
        payload=payload,
        expected_statuses={201},
        allow_fail=True,
    )

    return {
        "test": "add_comment",
        "success": success,
        "status": status,
        "data": data,
        "payload_used": payload,
    }


def update_issue_fields(issue_key: str) -> Dict[str, Any]:
    due_date = (date.today() + timedelta(days=7)).isoformat()

    payload = {
        "fields": {
            "summary": "AI Governor API POC Ticket - Updated by Script",
            "duedate": due_date,
            "labels": [
                "ai-governor-test",
                "api-poc",
                "ai-validation-pending",
            ],
        }
    }

    success, data, status = jira_request(
        "PUT",
        f"/rest/api/3/issue/{issue_key}",
        payload=payload,
        expected_statuses={204},
        allow_fail=True,
    )

    return {
        "test": "update_issue_fields",
        "success": success,
        "status": status,
        "data": data,
        "payload_used": payload,
    }


def assign_issue_to_self(issue_key: str, account_id: str) -> Dict[str, Any]:
    payload = {
        "accountId": account_id,
    }

    success, data, status = jira_request(
        "PUT",
        f"/rest/api/3/issue/{issue_key}/assignee",
        payload=payload,
        expected_statuses={204},
        allow_fail=True,
    )

    return {
        "test": "assign_issue_to_self",
        "success": success,
        "status": status,
        "data": data,
        "payload_used": payload,
    }


def add_worklog(issue_key: str) -> Dict[str, Any]:
    payload = {
        "comment": adf_text("AI Governor API POC: test worklog entry."),
        "started": f"{date.today().isoformat()}T10:00:00.000+0530",
        "timeSpentSeconds": 900,
    }

    success, data, status = jira_request(
        "POST",
        f"/rest/api/3/issue/{issue_key}/worklog",
        payload=payload,
        expected_statuses={201},
        allow_fail=True,
    )

    return {
        "test": "add_worklog",
        "success": success,
        "status": status,
        "data": data,
        "payload_used": payload,
    }


def add_self_as_watcher(issue_key: str, account_id: str) -> Dict[str, Any]:
    """
    Jira watcher API expects the accountId as JSON string body.
    This can fail if watchers are disabled or permission is restricted.
    """

    success, data, status = jira_request(
        "POST",
        f"/rest/api/3/issue/{issue_key}/watchers",
        payload=account_id,
        expected_statuses={204},
        allow_fail=True,
    )

    return {
        "test": "add_self_as_watcher",
        "success": success,
        "status": status,
        "data": data,
        "payload_used": account_id,
    }


def get_issue_transitions(issue_key: str) -> Dict[str, Any]:
    success, data, status = jira_request(
        "GET",
        f"/rest/api/3/issue/{issue_key}/transitions",
        expected_statuses={200},
        allow_fail=True,
    )

    return {
        "test": "get_transitions",
        "success": success,
        "status": status,
        "data": data,
    }


def transition_issue(issue_key: str, transitions_response: Dict[str, Any]) -> Dict[str, Any]:
    if not transitions_response.get("success"):
        return {
            "test": "transition_issue",
            "success": False,
            "reason": "Cannot transition because transition fetch failed.",
        }

    transitions = transitions_response.get("data", {}).get("transitions", [])

    if not transitions:
        return {
            "test": "transition_issue",
            "success": False,
            "reason": "No available transitions for this issue/user/workflow.",
        }

    selected_transition = None

    if JIRA_TARGET_TRANSITION_NAME:
        for transition in transitions:
            if transition.get("name", "").lower() == JIRA_TARGET_TRANSITION_NAME.lower():
                selected_transition = transition
                break

        if not selected_transition:
            return {
                "test": "transition_issue",
                "success": False,
                "reason": f"Transition '{JIRA_TARGET_TRANSITION_NAME}' not found.",
                "available_transitions": [
                    transition.get("name") for transition in transitions
                ],
            }

    if not selected_transition:
        selected_transition = transitions[0]

    payload = {
        "transition": {
            "id": selected_transition["id"],
        }
    }

    success, data, status = jira_request(
        "POST",
        f"/rest/api/3/issue/{issue_key}/transitions",
        payload=payload,
        expected_statuses={204},
        allow_fail=True,
    )

    return {
        "test": "transition_issue",
        "success": success,
        "status": status,
        "data": data,
        "transition_used": selected_transition,
        "payload_used": payload,
    }


def get_changelog(issue_key: str) -> Dict[str, Any]:
    all_values = []
    start_at = 0
    max_results = 100

    while True:
        success, data, status = jira_request(
            "GET",
            f"/rest/api/3/issue/{issue_key}/changelog",
            params={
                "startAt": start_at,
                "maxResults": max_results,
            },
            expected_statuses={200},
            allow_fail=True,
        )

        if not success:
            return {
                "test": "get_changelog",
                "success": False,
                "status": status,
                "data": data,
                "values": all_values,
            }

        values = data.get("values", [])
        all_values.extend(values)

        if data.get("isLast", True):
            break

        start_at += max_results

    return {
        "test": "get_changelog",
        "success": True,
        "issue_key": issue_key,
        "total_changelog_items": len(all_values),
        "values": all_values,
    }


def get_issue_link_types() -> Dict[str, Any]:
    success, data, status = jira_request(
        "GET",
        "/rest/api/3/issueLinkType",
        expected_statuses={200},
        allow_fail=True,
    )

    return {
        "test": "get_issue_link_types",
        "success": success,
        "status": status,
        "data": data,
    }


def link_issues(inward_issue_key: str, outward_issue_key: str, link_types_response: Dict[str, Any]) -> Dict[str, Any]:
    if not link_types_response.get("success"):
        return {
            "test": "link_issues",
            "success": False,
            "reason": "Could not fetch issue link types.",
        }

    link_types = link_types_response.get("data", {}).get("issueLinkTypes", [])

    if not link_types:
        return {
            "test": "link_issues",
            "success": False,
            "reason": "No issue link types available.",
        }

    selected_link_type = None

    for link_type in link_types:
        if link_type.get("name", "").lower() in ["relates", "relates to"]:
            selected_link_type = link_type
            break

    if not selected_link_type:
        selected_link_type = link_types[0]

    payload = {
        "type": {
            "name": selected_link_type["name"],
        },
        "inwardIssue": {
            "key": inward_issue_key,
        },
        "outwardIssue": {
            "key": outward_issue_key,
        },
        "comment": {
            "body": adf_text("AI Governor API POC: test issue link created by script."),
        },
    }

    success, data, status = jira_request(
        "POST",
        "/rest/api/3/issueLink",
        payload=payload,
        expected_statuses={201},
        allow_fail=True,
    )

    return {
        "test": "link_issues",
        "success": success,
        "status": status,
        "data": data,
        "link_type_used": selected_link_type,
        "payload_used": payload,
    }


def delete_issue(issue_key: str) -> Dict[str, Any]:
    success, data, status = jira_request(
        "DELETE",
        f"/rest/api/3/issue/{issue_key}",
        expected_statuses={204},
        allow_fail=True,
    )

    return {
        "test": "delete_issue",
        "success": success,
        "status": status,
        "data": data,
    }


# -----------------------------
# Summary
# -----------------------------

def make_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    checks = []

    def add_check(name: str, value: Any) -> None:
        if isinstance(value, dict):
            checks.append({
                "name": name,
                "success": bool(value.get("success")),
                "status": value.get("status"),
                "reason": value.get("reason"),
            })
        else:
            checks.append({
                "name": name,
                "success": value is not None,
            })

    add_check("authentication", results.get("01_authentication"))
    add_check("project_permissions", results.get("03_project_permissions"))
    add_check("global_jql_search", results.get("06_global_recent_issues"))
    add_check("test_project_jql_search", results.get("07_test_project_recent_issues"))
    add_check("create_main_issue", results.get("10_create_main_issue"))
    add_check("create_linked_issue", results.get("11_create_linked_issue"))
    add_check("read_main_issue_full", results.get("12_read_main_issue_full"))
    add_check("add_comment", results.get("13_add_comment"))
    add_check("update_issue_fields", results.get("14_update_issue_fields"))
    add_check("assign_issue_to_self", results.get("15_assign_issue_to_self"))
    add_check("add_worklog", results.get("16_add_worklog"))
    add_check("add_self_as_watcher", results.get("17_add_self_as_watcher"))
    add_check("get_transitions", results.get("18_get_transitions"))
    add_check("transition_issue", results.get("19_transition_issue"))
    add_check("get_changelog", results.get("20_get_changelog"))
    add_check("get_issue_link_types", results.get("21_get_issue_link_types"))
    add_check("link_issues", results.get("22_link_issues"))

    passed = sum(1 for check in checks if check["success"])
    failed = len(checks) - passed

    return {
        "total_checks": len(checks),
        "passed": passed,
        "failed": failed,
        "checks": checks,
        "important_notes": [
            "Read APIs can safely be used across visible Jira spaces/projects.",
            "Write tests in this script are intended only for your configured test space/project.",
            "Some tests may fail because of Jira workflow, field config, watcher settings, or permissions.",
            "Failure of watcher/worklog/linking does not mean Jira API auth is broken.",
            "Transition depends on the current workflow status and available transitions.",
        ],
    }


# -----------------------------
# Main runner
# -----------------------------

def main() -> None:
    validate_env()
    ensure_output_dir()

    print("Starting Jira API full POC test...")
    print(f"Base URL: {JIRA_BASE_URL}")
    print(f"Test space/project key: {JIRA_TEST_PROJECT_KEY}")
    print("Write actions will only target the configured test space/project.")

    results = {}
    created_issue_keys = []

    # 1. Authentication
    print("\n1. Testing authentication...")
    auth_result = test_authentication()
    results["01_authentication"] = auth_result
    save_json("01_authentication.json", auth_result)

    if not auth_result.get("success"):
        raise RuntimeError("Authentication failed. Check JIRA_EMAIL and JIRA_API_TOKEN.")

    myself = auth_result["data"]
    account_id = myself.get("accountId")
    print(f"Authenticated as: {myself.get('displayName')} / {myself.get('emailAddress')}")

    # 2. Visible projects/spaces
    print("\n2. Fetching visible spaces/projects...")
    visible_projects = get_visible_projects()
    results["02_visible_projects"] = visible_projects
    save_json("02_visible_projects.json", visible_projects)

    visible_project_keys = [project.get("key") for project in visible_projects]
    print(f"Visible spaces/projects: {len(visible_projects)}")

    if JIRA_TEST_PROJECT_KEY not in visible_project_keys:
        raise RuntimeError(
            f"Your test space/project key '{JIRA_TEST_PROJECT_KEY}' was not found in visible projects. "
            f"Check the key in .env or your Browse Project permission."
        )

    # 3. Permissions
    print("\n3. Checking permissions for test space/project...")
    permissions = get_project_permissions(JIRA_TEST_PROJECT_KEY)
    results["03_project_permissions"] = permissions
    save_json("03_project_permissions.json", permissions)

    # 4. Fields
    print("\n4. Fetching Jira fields...")
    fields = get_all_fields()
    results["04_fields"] = fields
    save_json("04_fields.json", fields)
    print(f"Fields fetched: {len(fields)}")

    # 5. Create metadata
    print("\n5. Fetching create metadata...")
    create_meta = get_create_metadata(JIRA_TEST_PROJECT_KEY)
    results["05_create_metadata"] = create_meta
    save_json("05_create_metadata.json", create_meta)

    if not create_meta.get("success"):
        raise RuntimeError(
            "Could not fetch create metadata. Your account may not have Create Issues permission "
            "in the test space/project."
        )

    issue_type = pick_issue_type(create_meta)
    required_fields = extract_required_fields(issue_type)

    results["05b_selected_issue_type_and_required_fields"] = {
        "selected_issue_type": issue_type,
        "required_fields": required_fields,
    }
    save_json("05b_selected_issue_type_and_required_fields.json", results["05b_selected_issue_type_and_required_fields"])

    print(f"Selected issue type: {issue_type.get('name')} / {issue_type.get('id')}")
    print(f"Required fields found: {list(required_fields.keys())}")

    # 6. Global recent issues read-only
    print("\n6. Searching recent visible issues globally, read-only...")
    global_recent = search_issues_jql("ORDER BY updated DESC", max_results=20)
    results["06_global_recent_issues"] = global_recent
    save_json("06_global_recent_issues.json", global_recent)
    print(f"Global recent issues fetched: {global_recent.get('total_fetched', 0)}")

    # 7. Test project recent issues read-only
    print("\n7. Searching recent issues in test space/project, read-only...")
    test_project_recent = search_issues_jql(
        f'project = "{JIRA_TEST_PROJECT_KEY}" ORDER BY updated DESC',
        max_results=20,
    )
    results["07_test_project_recent_issues"] = test_project_recent
    save_json("07_test_project_recent_issues.json", test_project_recent)
    print(f"Test project recent issues fetched: {test_project_recent.get('total_fetched', 0)}")

    # 8. Create main issue
    print("\n8. Creating main test issue...")
    main_issue = create_test_issue(
        project_key=JIRA_TEST_PROJECT_KEY,
        issue_type_id=issue_type["id"],
        summary="AI Governor API POC Ticket",
        description=(
            "This ticket was created by the Jira API POC script. "
            "It is used to test create, read, update, comment, transition, changelog, "
            "worklog, watcher, and issue linking capabilities."
        ),
    )
    results["10_create_main_issue"] = main_issue
    save_json("10_create_main_issue.json", main_issue)

    if not main_issue.get("success"):
        raise RuntimeError(
            "Main issue creation failed. Check required fields in "
            "05b_selected_issue_type_and_required_fields.json"
        )

    main_issue_key = main_issue["data"]["key"]
    created_issue_keys.append(main_issue_key)
    print(f"Created main issue: {main_issue_key}")

    # 9. Create linked issue
    print("\n9. Creating second test issue for issue-linking test...")
    linked_issue = create_test_issue(
        project_key=JIRA_TEST_PROJECT_KEY,
        issue_type_id=issue_type["id"],
        summary="AI Governor API POC Linked Ticket",
        description="This second ticket is created only to test Jira issue linking through API.",
    )
    results["11_create_linked_issue"] = linked_issue
    save_json("11_create_linked_issue.json", linked_issue)

    linked_issue_key = None

    if linked_issue.get("success"):
        linked_issue_key = linked_issue["data"]["key"]
        created_issue_keys.append(linked_issue_key)
        print(f"Created linked issue: {linked_issue_key}")
    else:
        print("Linked issue creation failed. Continuing other tests.")

    # 10. Read full issue
    print("\n10. Reading full issue details...")
    read_main = get_issue_full(main_issue_key)
    results["12_read_main_issue_full"] = read_main
    save_json("12_read_main_issue_full.json", read_main)

    # 11. Add comment
    print("\n11. Adding validation-style comment...")
    comment = add_comment(
        main_issue_key,
        (
            "AI Governor validation test:\n"
            "Score: 72/100. Missing: acceptance criteria, impact, and testing evidence."
        ),
    )
    results["13_add_comment"] = comment
    save_json("13_add_comment.json", comment)

    # 12. Update fields
    print("\n12. Updating summary, labels, and due date...")
    update_result = update_issue_fields(main_issue_key)
    results["14_update_issue_fields"] = update_result
    save_json("14_update_issue_fields.json", update_result)

    # 13. Assign to self
    print("\n13. Assigning issue to self...")
    assign_result = assign_issue_to_self(main_issue_key, account_id)
    results["15_assign_issue_to_self"] = assign_result
    save_json("15_assign_issue_to_self.json", assign_result)

    # 14. Add worklog
    print("\n14. Adding worklog...")
    worklog_result = add_worklog(main_issue_key)
    results["16_add_worklog"] = worklog_result
    save_json("16_add_worklog.json", worklog_result)

    # 15. Add watcher
    print("\n15. Adding self as watcher...")
    watcher_result = add_self_as_watcher(main_issue_key, account_id)
    results["17_add_self_as_watcher"] = watcher_result
    save_json("17_add_self_as_watcher.json", watcher_result)

    # 16. Get transitions
    print("\n16. Fetching available transitions...")
    transitions = get_issue_transitions(main_issue_key)
    results["18_get_transitions"] = transitions
    save_json("18_get_transitions.json", transitions)

    # 17. Transition issue
    print("\n17. Trying to transition issue...")
    transition_result = transition_issue(main_issue_key, transitions)
    results["19_transition_issue"] = transition_result
    save_json("19_transition_issue.json", transition_result)

    # 18. Changelog
    print("\n18. Fetching changelog/history...")
    changelog = get_changelog(main_issue_key)
    results["20_get_changelog"] = changelog
    save_json("20_get_changelog.json", changelog)

    # 19. Issue link types
    print("\n19. Fetching issue link types...")
    link_types = get_issue_link_types()
    results["21_get_issue_link_types"] = link_types
    save_json("21_get_issue_link_types.json", link_types)

    # 20. Link issues
    if linked_issue_key:
        print("\n20. Linking main issue with second issue...")
        link_result = link_issues(main_issue_key, linked_issue_key, link_types)
        results["22_link_issues"] = link_result
        save_json("22_link_issues.json", link_result)
    else:
        results["22_link_issues"] = {
            "test": "link_issues",
            "success": False,
            "reason": "Skipped because second issue was not created.",
        }
        save_json("22_link_issues.json", results["22_link_issues"])

    # 21. Final read after all actions
    print("\n21. Reading final issue state...")
    final_issue = get_issue_full(main_issue_key)
    results["23_final_issue_state"] = final_issue
    save_json("23_final_issue_state.json", final_issue)

    # 22. Optional cleanup
    if JIRA_CLEANUP_CREATED_ISSUES:
        print("\n22. Cleanup enabled. Deleting created test issues...")

        cleanup_results = []

        for issue_key in reversed(created_issue_keys):
            cleanup_result = delete_issue(issue_key)
            cleanup_results.append({
                "issue_key": issue_key,
                "result": cleanup_result,
            })

        results["24_cleanup"] = cleanup_results
        save_json("24_cleanup.json", cleanup_results)
    else:
        print("\n22. Cleanup disabled. Created issues are kept for UI inspection.")
        results["24_cleanup"] = {
            "cleanup_enabled": False,
            "created_issue_keys": created_issue_keys,
        }
        save_json("24_cleanup.json", results["24_cleanup"])

    # 23. Summary
    summary = make_summary(results)
    results["25_summary"] = summary
    save_json("25_summary.json", summary)

    print("\n==============================")
    print("Jira API POC completed.")
    print("==============================")
    print(f"Main test issue: {main_issue_key}")

    if linked_issue_key:
        print(f"Linked test issue: {linked_issue_key}")

    print(f"Total checks: {summary['total_checks']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Output folder: {OUTPUT_DIR}")

    print("\nOpen 25_summary.json for the final pass/fail report.")
    print("Some failures may be permission/workflow related, not script errors.")


if __name__ == "__main__":
    main()