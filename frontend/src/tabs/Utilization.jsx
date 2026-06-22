import { useEffect, useState } from "react";
import { apiFetch } from "../api";
import { fmtDate } from "../lib/format";

// Aggregated utilization analytics for the AI Governor system. Reads
// /graph-admin/utilization; every section is optional (available flag) so the
// view degrades gracefully when a data source has no table yet.
export default function Utilization() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setError("");
    setLoading(true);
    try {
      setData(await apiFetch("/graph-admin/utilization"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const tc = data?.test_cases || {};
  const dr = data?.doc_reviews || {};
  const tk = data?.tickets || {};
  const tr = data?.transitions || {};
  const dd = data?.due_date || {};
  const doc = data?.documentation || {};
  const conv = data?.conversations || {};

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14, flexWrap: "wrap" }}>
        <span style={{ fontSize: 13, color: "var(--muted)" }}>
          AI Governor utilization — test cases, document reviews, ticket states &amp; transitions
        </span>
        <button
          className="secondary"
          style={{ width: "auto", minHeight: "unset", padding: "6px 14px", fontSize: 13 }}
          onClick={load}
        >
          Refresh
        </button>
      </div>

      {data && !data.database_configured && (
        <div style={{ color: "var(--muted)", fontSize: 14, padding: "24px 0" }}>
          Database is not configured. Set <code>DATABASE_URL</code> (or the <code>DB_*</code> vars)
          in the server environment to enable utilization analytics.
        </div>
      )}

      {data?.database_configured && (
        <>
          <div className="stats-grid">
            <Stat value={tc.total_test_cases} label="Test Cases Built" />
            <Stat value={tc.tickets_covered} label="Tickets w/ Test Cases" />
            <Stat value={dr.docs_reviewed} label="PRD/BRD Docs Reviewed" />
            <Stat value={dr.total_reviews} label="Doc Review Runs" />
            <Stat value={tr.total} label="State Transitions" />
            <Stat value={tk.total} label="Tickets Tracked" />
            <Stat value={doc.generated} label="Docs Generated" />
            <Stat value={conv.threads} label="Slack Q&A Threads" />
          </div>

          <Breakdown
            title="Test cases by status"
            rows={tc.by_status}
            cols={[["status", "Status"], ["count", "Count"]]}
            empty={tc.available === false ? "No test_cases table found." : "No test cases yet."}
          />

          <Breakdown
            title="Document reviews by type (PRD / TechDoc / BRD)"
            rows={dr.by_type}
            cols={[["doc_type", "Document type"], ["docs", "Docs"], ["reviews", "Review runs"]]}
            empty={dr.available === false ? "No doc_reviews table found." : "No documents reviewed yet."}
          />

          <Breakdown
            title="Ticket state distribution (current snapshot)"
            rows={tk.by_status}
            cols={[["status", "Status"], ["count", "Tickets"]]}
            empty={tk.available === false ? "No jira_ticket_cache table found." : "No tickets cached yet."}
          />

          <Breakdown
            title="Tickets by project"
            rows={tk.by_project}
            cols={[["project", "Project"], ["count", "Tickets"]]}
            empty="—"
            hideWhenEmpty
          />

          <Breakdown
            title="State transitions (from → to)"
            rows={tr.by_transition}
            cols={[["from_status", "From"], ["to_status", "To"], ["count", "Moves"]]}
            empty={
              tr.available === false
                ? "Transition logging is not set up yet."
                : "No transitions recorded yet — they accrue once the Status Transition Logger workflow is active."
            }
          />

          {dd.available && (
            <Breakdown
              title="Due-date alerts fired (by remaining-time band)"
              rows={[
                { band: "< 75% time left", count: dd.alerts?.lt_75pct },
                { band: "< 50% time left", count: dd.alerts?.lt_50pct },
                { band: "< 25% time left", count: dd.alerts?.lt_25pct },
                { band: "Breached / overdue", count: dd.alerts?.breached },
              ]}
              cols={[["band", "Band"], ["count", "Tickets alerted"]]}
              empty="—"
            />
          )}

          {tr.recent?.length > 0 && (
            <div style={{ marginTop: 22 }}>
              <span className="tc-section-title">Recent transitions</span>
              <table>
                <thead>
                  <tr>
                    <th style={{ width: "16%" }}>Ticket</th>
                    <th>From</th>
                    <th>To</th>
                    <th>Assignee</th>
                    <th style={{ width: "18%" }}>When</th>
                  </tr>
                </thead>
                <tbody>
                  {tr.recent.map((r, i) => (
                    <tr key={i}>
                      <td>{r.jira_ticket_id}</td>
                      <td style={{ color: "var(--muted)" }}>{r.from_status || "—"}</td>
                      <td>
                        <span className="badge ok">{r.to_status}</span>
                      </td>
                      <td>{r.assignee_name || "—"}</td>
                      <td style={{ fontSize: 12, color: "var(--muted)" }}>{fmtDate(r.changed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {loading && !data && <div style={{ color: "var(--muted)", fontSize: 13, marginTop: 8 }}>Loading…</div>}
      {error && <div style={{ color: "var(--danger)", fontSize: 13, marginTop: 8 }}>{error}</div>}
    </div>
  );
}

function Stat({ value, label }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value ?? 0}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function Breakdown({ title, rows, cols, empty, hideWhenEmpty }) {
  const list = rows || [];
  if (hideWhenEmpty && list.length === 0) return null;
  return (
    <div style={{ marginTop: 22 }}>
      <span className="tc-section-title">{title}</span>
      {list.length === 0 ? (
        <div style={{ color: "var(--muted)", fontSize: 13, padding: "6px 0" }}>{empty}</div>
      ) : (
        <table>
          <thead>
            <tr>
              {cols.map(([key, label]) => (
                <th key={key}>{label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {list.map((row, i) => (
              <tr key={i}>
                {cols.map(([key]) => (
                  <td key={key}>{row[key] ?? "—"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
