import { useEffect, useState } from "react";
import { apiFetch, apiDownload } from "../api";
import { fmtDate } from "../lib/format";

const MATCH_TYPES = [
  { value: "all", label: "All matches" },
  { value: "test_cases", label: "Test Cases" },
  { value: "requirements", label: "PRD / BRD / SRS" },
  { value: "prd", label: "PRD" },
  { value: "brd", label: "BRD" },
  { value: "srs", label: "SRS" },
];
const PIPELINE_LIMITS = [
  { value: "0", label: "No pipeline run" },
  { value: "3", label: "3 pipeline tickets" },
  { value: "5", label: "5 pipeline tickets" },
  { value: "10", label: "10 pipeline tickets" },
  { value: "20", label: "20 pipeline tickets" },
];

export default function Insights() {
  const [project, setProject] = useState("");
  const [matchType, setMatchType] = useState("all");
  const [pipelineLimit, setPipelineLimit] = useState("5");
  const [rows, setRows] = useState([]);
  const [counts, setCounts] = useState({});
  const [countText, setCountText] = useState("Loading…");
  const [info, setInfo] = useState({ msg: "", error: false });
  const [downloading, setDownloading] = useState(false);

  async function load(nextMatchType = matchType) {
    setCountText("Loading…");
    setInfo({ msg: "", error: false });
    const params = new URLSearchParams({ limit: "500", match_type: nextMatchType });
    const proj = project.trim().toUpperCase();
    if (proj) params.set("project_key", proj);
    try {
      const data = await apiFetch(`/graph-admin/jira-ticket-insights?${params.toString()}`);
      if (data.error) {
        setInfo({ msg: data.error, error: true });
        setCountText("—");
        setRows([]);
        setCounts({});
        return;
      }
      const total = data.total_tickets || 0;
      const matching = data.matching_tickets || 0;
      const returned = data.returned_tickets || 0;
      const excluded = (data.excluded_projects || []).join(", ");
      setCountText(
        `${matching} matching ticket${matching !== 1 ? "s" : ""} from ${total} scanned${excluded ? ` · excluded ${excluded}` : ""}`,
      );
      setCounts(data.counts || {});
      setRows(data.tickets || []);
      if (returned < matching) {
        setInfo({ msg: `Showing latest ${returned} of ${matching} matching tickets`, error: false });
      }
    } catch (err) {
      setInfo({ msg: err.message, error: true });
      setCountText("—");
      setCounts({});
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function downloadReport() {
    setDownloading(true);
    setInfo({ msg: "Generating pipeline comparison...", error: false });
    const params = new URLSearchParams({ limit: "500", format: "xlsx" });
    const proj = project.trim().toUpperCase();
    if (proj) params.set("project_key", proj);
    params.set("pipeline_limit", pipelineLimit || "5");
    try {
      await apiDownload(`/graph-admin/test-case-comparison-report?${params.toString()}`, {
        fallbackName: "jira-test-case-comparison.xlsx",
      });
      setInfo({ msg: "Pipeline comparison downloaded", error: false });
    } catch (err) {
      setInfo({ msg: err.message, error: true });
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div>
      <div className="insight-controls">
        <span style={{ fontSize: 13, color: "var(--muted)" }}>{countText}</span>
        <input
          className="insight-input"
          type="text"
          placeholder="Filter by project key…"
          value={project}
          onChange={(e) => setProject(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <select
          className="insight-select"
          value={matchType}
          onChange={(e) => {
            setMatchType(e.target.value);
            load(e.target.value);
          }}
        >
          {MATCH_TYPES.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
        <button className="secondary" style={{ width: "auto", minHeight: "unset", padding: "6px 14px", fontSize: 13 }} onClick={() => load()}>
          Refresh
        </button>
        <select
          className="insight-select"
          style={{ minWidth: 150 }}
          value={pipelineLimit}
          onChange={(e) => setPipelineLimit(e.target.value)}
        >
          {PIPELINE_LIMITS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
        <button
          className="secondary"
          style={{ width: "auto", minHeight: "unset", padding: "6px 14px", fontSize: 13 }}
          disabled={downloading}
          onClick={downloadReport}
        >
          Download Excel Comparison
        </button>
      </div>

      <div className="insight-stat-grid">
        <Stat value={counts.test_cases || 0} label="Test Cases" />
        <Stat value={counts.prd || 0} label="PRD" />
        <Stat value={counts.brd || 0} label="BRD" />
        <Stat value={counts.srs || 0} label="SRS" />
        <Stat value={counts.matching_tickets || 0} label="Matching Tickets" />
      </div>

      <table>
        <thead>
          <tr>
            <th style={{ width: "10%" }}>Key</th>
            <th style={{ width: "8%" }}>Project</th>
            <th>Summary</th>
            <th style={{ width: "12%" }}>Test Cases</th>
            <th style={{ width: "14%" }}>Docs</th>
            <th style={{ width: "24%" }}>Evidence</th>
            <th style={{ width: "12%" }}>Updated</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={7} style={{ color: "var(--muted)" }}>
                No matching tickets found
              </td>
            </tr>
          ) : (
            rows.map((t) => <InsightRow key={t.ticket_key} t={t} />)
          )}
        </tbody>
      </table>
      {info.msg && (
        <div style={{ color: info.error ? "var(--danger)" : "var(--muted)", fontSize: 13, marginTop: 8 }}>
          {info.msg}
        </div>
      )}
    </div>
  );
}

function Stat({ value, label }) {
  return (
    <div className="insight-stat">
      <div className="insight-stat-value">{value}</div>
      <div className="insight-stat-label">{label}</div>
    </div>
  );
}

function InsightRow({ t }) {
  const docs = t.requirement_docs || [];
  const matches = t.matches || [];
  return (
    <tr>
      <td>
        {t.url ? (
          <a href={t.url} target="_blank" rel="noopener noreferrer">
            <b>{t.ticket_key}</b>
          </a>
        ) : (
          <b>{t.ticket_key}</b>
        )}
      </td>
      <td>{t.project_key || ""}</td>
      <td>
        <div><b>{t.summary || ""}</b></div>
        <div style={{ marginTop: 4, color: "var(--muted)", fontSize: 12 }}>
          {(t.status || "—") + " · " + (t.issue_type || "—")}
        </div>
      </td>
      <td>
        {t.has_test_cases ? (
          <span className="insight-chip hit">Found</span>
        ) : (
          <span className="insight-chip">—</span>
        )}
      </td>
      <td>
        {docs.length ? (
          <div className="insight-chip-row">
            {docs.map((d, i) => (
              <span key={i} className="insight-chip doc">
                {d}
              </span>
            ))}
          </div>
        ) : (
          <span className="insight-chip">—</span>
        )}
      </td>
      <td>
        {matches.length === 0 ? (
          <span style={{ color: "var(--muted)" }}>—</span>
        ) : (
          <details className="insight-snippets">
            <summary>
              {matches.length} hit{matches.length !== 1 ? "s" : ""}
            </summary>
            {matches.map((m, i) => (
              <div key={i} className="insight-snippet">
                <span className="insight-source">
                  {(m.label || "") + " · " + (m.source || "")}
                </span>
                {m.snippet || ""}
              </div>
            ))}
          </details>
        )}
      </td>
      <td>{fmtDate(t.updated_at)}</td>
    </tr>
  );
}
