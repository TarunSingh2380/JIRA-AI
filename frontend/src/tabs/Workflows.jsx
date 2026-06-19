import { useEffect, useState } from "react";
import { apiFetch } from "../api";
import { fmtDate } from "../lib/format";

// Maps an n8n execution status to the shared badge class.
function statusClass(status) {
  if (!status) return "";
  if (status === "success") return "ok";
  if (status === "error" || status === "crashed") return "err";
  return "run";
}

export default function Workflows() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setError("");
    setLoading(true);
    try {
      const res = await apiFetch("/graph-admin/n8n/workflows");
      setData(res);
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

  const totals = data?.totals || {};
  const workflows = data?.workflows || [];

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14, flexWrap: "wrap" }}>
        <span style={{ fontSize: 13, color: "var(--muted)" }}>
          Live n8n workflow status &amp; execution health
          {data?.execution_window
            ? ` (counts from last ${data.execution_window} executions)`
            : ""}
        </span>
        <button
          className="secondary"
          style={{ width: "auto", minHeight: "unset", padding: "6px 14px", fontSize: 13 }}
          onClick={load}
        >
          Refresh
        </button>
      </div>

      {data && !data.configured && (
        <div style={{ color: "var(--muted)", fontSize: 14, padding: "24px 0" }}>
          n8n monitoring is not configured. Set <code>N8N_BASE_URL</code> and{" "}
          <code>N8N_API_KEY</code> in the server environment to enable it.
        </div>
      )}

      {data?.configured && (
        <>
          <div className="stats-grid">
            <Stat value={totals.workflows ?? 0} label="Workflows" />
            <Stat value={totals.active ?? 0} label="Active / Live" />
            <Stat value={totals.inactive ?? 0} label="Inactive" />
            <Stat value={totals.executions ?? 0} label="Executions" />
            <Stat value={totals.errors ?? 0} label="Errors" />
          </div>

          <table>
            <thead>
              <tr>
                <th style={{ width: "26%" }}>Workflow</th>
                <th style={{ width: "9%" }}>Status</th>
                <th style={{ width: "9%" }}>Executions</th>
                <th style={{ width: "8%" }}>Success</th>
                <th style={{ width: "8%" }}>Errors</th>
                <th style={{ width: "12%" }}>Last Run</th>
                <th style={{ width: "10%" }}>Last Result</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {workflows.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ color: "var(--muted)" }}>
                    No workflows found
                  </td>
                </tr>
              ) : (
                workflows.map((w) => (
                  <tr key={w.id}>
                    <td>{w.name}</td>
                    <td>
                      <span className={`badge ${w.active ? "ok" : ""}`}>
                        {w.active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td>{w.executions}</td>
                    <td>{w.success}</td>
                    <td style={{ color: w.errors > 0 ? "var(--danger)" : undefined, fontWeight: w.errors > 0 ? 700 : undefined }}>
                      {w.errors}
                    </td>
                    <td>{fmtDate(w.last_run_at)}</td>
                    <td>
                      {w.last_status ? (
                        <span className={`badge ${statusClass(w.last_status)}`}>{w.last_status}</span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td style={{ fontSize: 12, color: "var(--muted)" }}>
                      {(w.tags || []).join(", ") || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
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
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
