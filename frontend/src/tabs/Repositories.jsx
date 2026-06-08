import { useState } from "react";
import { apiDownload, apiFetch } from "../api";

export default function Repositories({ repos, excluded, selected, setSelected, embeddingModel, setStatus }) {
  const [downloading, setDownloading] = useState(false);
  const [repomixing, setRepomixing] = useState(false);
  const allSelected = repos.length > 0 && selected.size === repos.length;

  function toggleRepo(name, checked) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) next.add(name);
      else next.delete(name);
      return next;
    });
  }

  function toggleAll(checked) {
    setSelected(checked ? new Set(repos.map((r) => r.name)) : new Set());
  }

  async function downloadCodeAnalysis() {
    if (selected.size === 0) {
      setStatus({ msg: "Select at least one repository for analysis", cls: "error" });
      return;
    }
    setDownloading(true);
    setStatus({ msg: "Generating code analysis document...", cls: "running" });
    try {
      await apiDownload("/graph-admin/code-analysis-report", {
        method: "POST",
        body: {
          // Graph DB is no longer used — rely on Qdrant/code context only.
          repositories: [...selected],
          include_graph_context: false,
          embedding_model: embeddingModel,
        },
        fallbackName: "code-analysis-report.md",
      });
      setStatus({ msg: "Code analysis document downloaded", cls: "ok" });
    } catch (err) {
      setStatus({ msg: err.message, cls: "error" });
    } finally {
      setDownloading(false);
    }
  }

  async function updateRepomix() {
    if (selected.size === 0) {
      setStatus({ msg: "Select at least one repository to update RepoMix data", cls: "error" });
      return;
    }
    setRepomixing(true);
    setStatus({ msg: "Updating RepoMix data for selected repositories...", cls: "running" });
    try {
      const data = await apiFetch("/graph-admin/repomix/reindex", {
        method: "POST",
        body: { repositories: [...selected], pull_latest_code: true, force: false },
      });
      const packed = data.packed?.length || 0;
      const skipped = data.skipped?.length || 0;
      const failed = data.failed?.length || 0;
      const unknown = data.unknown?.length || 0;
      const parts = [`${packed} repacked`, `${skipped} unchanged`];
      if (failed) parts.push(`${failed} failed`);
      if (unknown) parts.push(`${unknown} not in RepoMix config`);
      setStatus({
        msg: `RepoMix update done: ${parts.join(", ")}`,
        cls: failed ? "error" : "ok",
      });
    } catch (err) {
      setStatus({ msg: err.message, cls: "error" });
    } finally {
      setRepomixing(false);
    }
  }

  return (
    <div>
      <div className="repo-actions">
        <label>
          <input type="checkbox" checked={allSelected} onChange={(e) => toggleAll(e.target.checked)} />
          Select all repositories
        </label>
        <button className="secondary" disabled={downloading} onClick={downloadCodeAnalysis}>
          Download Code Analysis
        </button>
        <button className="secondary" disabled={repomixing} onClick={updateRepomix}>
          {repomixing ? "Updating RepoMix…" : "Update RepoMix Data"}
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th style={{ width: "6%" }}>Use</th>
            <th style={{ width: "20%" }}>Repository</th>
            <th>Local clone path</th>
            <th style={{ width: "16%" }}>Branch</th>
            <th style={{ width: "18%" }}>Commit</th>
          </tr>
        </thead>
        <tbody>
          {repos.map((r) => (
            <tr key={r.name}>
              <td>
                <input
                  type="checkbox"
                  checked={selected.has(r.name)}
                  onChange={(e) => toggleRepo(r.name, e.target.checked)}
                />
              </td>
              <td>{r.name}</td>
              <td>{r.path}</td>
              <td>{r.branch || "-"}</td>
              <td>{(r.current_commit || "-").slice(0, 12)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="meta">
        Using existing local clones. Excluded: {excluded?.length ? excluded.join(", ") : "none"}
      </p>
    </div>
  );
}
