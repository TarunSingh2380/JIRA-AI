import { useEffect, useState } from "react";
import { apiFetch } from "../api";
import { fmtDate } from "../lib/format";

export default function JiraTickets() {
  const [tickets, setTickets] = useState([]);
  const [countText, setCountText] = useState("Loading…");
  const [project, setProject] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setCountText("Loading…");
    setError("");
    const proj = project.trim().toUpperCase();
    const qs = proj ? `?project_key=${encodeURIComponent(proj)}&limit=200` : "?limit=200";
    try {
      const data = await apiFetch(`/graph-admin/jira-tickets${qs}`);
      if (data.error) {
        setError(data.error);
        setCountText("—");
        setTickets([]);
        return;
      }
      const excluded = (data.excluded_projects || []).join(", ");
      setCountText(
        `${data.count} ticket${data.count !== 1 ? "s" : ""} in cache${excluded ? ` · excluded ${excluded}` : ""}`,
      );
      setTickets(data.tickets || []);
    } catch (err) {
      setError(err.message);
      setCountText("—");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
        <span style={{ fontSize: 13, color: "var(--muted)" }}>{countText}</span>
        <input
          type="text"
          placeholder="Filter by project key…"
          value={project}
          onChange={(e) => setProject(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          style={{ border: "1px solid var(--line)", borderRadius: 5, padding: "5px 10px", font: "inherit", fontSize: 13, width: 180 }}
        />
        <button className="secondary" style={{ width: "auto", minHeight: "unset", padding: "6px 14px", fontSize: 13 }} onClick={load}>
          Refresh
        </button>
      </div>
      <table>
        <thead>
          <tr>
            <th style={{ width: "10%" }}>Key</th>
            <th style={{ width: "9%" }}>Project</th>
            <th>Summary</th>
            <th style={{ width: "10%" }}>Status</th>
            <th style={{ width: "10%" }}>Type</th>
            <th style={{ width: "13%" }}>Updated</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr key={t.ticket_key}>
              <td><b>{t.ticket_key}</b></td>
              <td>{t.project_key}</td>
              <td>{t.summary || ""}</td>
              <td><span className="badge">{t.status || "—"}</span></td>
              <td>{t.issue_type || "—"}</td>
              <td>{fmtDate(t.updated_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {error && <div style={{ color: "var(--danger)", fontSize: 13, marginTop: 8 }}>{error}</div>}
    </div>
  );
}
