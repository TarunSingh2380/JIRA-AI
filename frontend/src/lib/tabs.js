// Capability keys that correspond to tabs on the main dashboard. "docs" and
// "users" are deliberately excluded — they are standalone pages, not tabs.
export const DASHBOARD_TAB_KEYS = ["repos", "jira", "insights", "logs", "testcases", "similar", "workflows", "utilization", "neo4j", "rca", "rings", "zoho"];

export function hasAnyDashboardTab(hasTab) {
  return DASHBOARD_TAB_KEYS.some((t) => hasTab(t));
}
