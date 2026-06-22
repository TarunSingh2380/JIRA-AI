import { useState } from "react";
import { apiDownload, apiFetch } from "../api";

// Activity score → label + badge style. Mirrors the recency/frequency blend
// computed on the backend (see app/repository_discovery.py).
function activityTier(score) {
  if (score == null) return { cls: "idle", label: "Unknown" };
  if (score >= 60) return { cls: "ok", label: "Active" };
  if (score >= 30) return { cls: "warn", label: "Moderate" };
  if (score >= 1) return { cls: "err", label: "Low" };
  return { cls: "idle", label: "Stale" };
}

function activityHint(r) {
  const parts = [];
  if (r.last_commit_days != null) parts.push(`last commit ${r.last_commit_days}d ago`);
  if (r.commits_90d != null) parts.push(`${r.commits_90d} commits / 90d`);
  if (r.commits_30d != null) parts.push(`${r.commits_30d} / 30d`);
  if (r.authors_90d != null) parts.push(`${r.authors_90d} authors / 90d`);
  return parts.join(" · ");
}

export default function Repositories({ repos, excluded, selected, setSelected, reloadRepos, embeddingModel, setStatus }) {
  const [downloading, setDownloading] = useState(false);
  const [repomixing, setRepomixing] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const allSelected = repos.length > 0 && selected.size === repos.length;

  // Rank most-active first so stale repos sink to the bottom; ties break by name.
  const rankedRepos = [...repos].sort((a, b) => {
    const diff = (b.activity_score ?? -1) - (a.activity_score ?? -1);
    return diff !== 0 ? diff : a.name.localeCompare(b.name);
  });

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

  async function recalcActivity() {
    setRecalculating(true);
    setStatus({ msg: "Recalculating activity scores...", cls: "running" });
    try {
      // Re-fetching the repository list recomputes git activity server-side;
      // keep the user's current selection intact.
      const count = await reloadRepos({ keepSelection: true });
      setStatus({ msg: `Activity scores recalculated for ${count} repositories`, cls: "ok" });
    } catch (err) {
      setStatus({ msg: `Recalculation failed: ${err.message}`, cls: "error" });
    } finally {
      setRecalculating(false);
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
        <button className="secondary" disabled={recalculating} onClick={recalcActivity}>
          {recalculating ? "Recalculating…" : "Recalculate Activity Score"}
        </button>
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
            <th style={{ width: "5%" }}>Use</th>
            <th style={{ width: "5%" }}>Rank</th>
            <th style={{ width: "18%" }}>Repository</th>
            <th style={{ width: "16%" }}>Activity</th>
            <th>Local clone path</th>
            <th style={{ width: "12%" }}>Branch</th>
            <th style={{ width: "14%" }}>Commit</th>
          </tr>
        </thead>
        <tbody>
          {rankedRepos.map((r, i) => {
            const tier = activityTier(r.activity_score);
            return (
              <tr key={r.name}>
                <td>
                  <input
                    type="checkbox"
                    checked={selected.has(r.name)}
                    onChange={(e) => toggleRepo(r.name, e.target.checked)}
                  />
                </td>
                <td className="meta">{i + 1}</td>
                <td>{r.name}</td>
                <td>
                  <div className="activity-cell" title={activityHint(r)}>
                    <span className={`badge ${tier.cls}`}>
                      {r.activity_score == null ? "—" : r.activity_score}
                    </span>
                    <span className="activity-sub">
                      {tier.label}
                      {r.last_commit_days != null ? ` · ${Math.round(r.last_commit_days)}d ago` : ""}
                    </span>
                  </div>
                </td>
                <td>{r.path}</td>
                <td>{r.branch || "-"}</td>
                <td>{(r.current_commit || "-").slice(0, 12)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <p className="meta">
        Using existing local clones. Excluded: {excluded?.length ? excluded.join(", ") : "none"}
        <br />
        Activity score (0–100) blends commit recency with commit volume over the last 90 days —
        higher means actively developed, 0 means stale.
      </p>
    </div>
  );
}
