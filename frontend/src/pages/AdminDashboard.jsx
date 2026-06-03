import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { apiFetch } from "../api";
import { deriveStats, runningStatusMessage } from "../lib/graphJob";
import Header from "../components/Header.jsx";
import JobSidebar from "../components/JobSidebar.jsx";
import JobProgress from "../components/JobProgress.jsx";
import Repositories from "../tabs/Repositories.jsx";
import JiraTickets from "../tabs/JiraTickets.jsx";
import Insights from "../tabs/Insights.jsx";
import Logs from "../tabs/Logs.jsx";
import TestCases from "../tabs/TestCases.jsx";
import SimilarTickets from "../tabs/SimilarTickets.jsx";

// Tab registry — order matches the original UI. "docs" is intentionally absent:
// the Documentation portal is a separate route, not a tab here.
const TABS = [
  { key: "repos", label: "Repositories", Component: Repositories },
  { key: "jira", label: "Jira Tickets", Component: JiraTickets },
  { key: "insights", label: "Ticket Insights", Component: Insights },
  { key: "logs", label: "Logs", Component: Logs },
  { key: "testcases", label: "Test Cases", Component: TestCases },
  { key: "similar", label: "Similar Tickets", Component: SimilarTickets },
];

const DEFAULT_OPTIONS = {
  pullLatestCode: true,
  fetchLatestJira: true,
  includeJira: true,
  buildEmbeddings: true,
  embeddingModel: "codebase_bge_m3",
  notes: "",
};

export default function AdminDashboard() {
  const { hasTab } = useAuth();
  const canRepos = hasTab("repos");

  const visibleTabs = useMemo(() => TABS.filter((t) => hasTab(t.key)), [hasTab]);
  const [activeTab, setActiveTab] = useState(() => visibleTabs[0]?.key || "");

  // Graph-job + repository state (shared by the sidebar and Repositories tab).
  const [repos, setRepos] = useState([]);
  const [excluded, setExcluded] = useState([]);
  const [selected, setSelected] = useState(() => new Set());
  const [options, setOptions] = useState(DEFAULT_OPTIONS);
  const [job, setJob] = useState(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState({ msg: canRepos ? "Loading repositories..." : "", cls: "" });
  const pollRef = useRef(null);

  const setOption = (key, value) => setOptions((o) => ({ ...o, [key]: value }));

  useEffect(() => {
    if (!activeTab && visibleTabs[0]) setActiveTab(visibleTabs[0].key);
  }, [visibleTabs, activeTab]);

  // Load repositories on mount (only if the role can use the repos tab).
  useEffect(() => {
    if (!canRepos) return;
    let active = true;
    (async () => {
      try {
        const data = await apiFetch("/graph-admin/repositories");
        if (!active) return;
        const list = data.repositories || [];
        setRepos(list);
        setExcluded(data.excluded_repositories || []);
        setSelected(new Set(list.map((r) => r.name)));
        setStatus({ msg: `${data.repository_count} repositories ready`, cls: "ok" });
      } catch (err) {
        if (active) setStatus({ msg: `Repository load failed: ${err.message}`, cls: "error" });
      }
    })();
    return () => {
      active = false;
    };
  }, [canRepos]);

  useEffect(() => () => pollRef.current && clearInterval(pollRef.current), []);

  function startPolling(jobId) {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(() => pollJob(jobId), 2000);
  }

  async function pollJob(jobId) {
    try {
      const data = await apiFetch(`/graph-admin/jobs/${jobId}`);
      setJob(data);
      if (data.status === "running") {
        setStatus({ msg: runningStatusMessage(data, options.buildEmbeddings), cls: "running" });
      }
      if (data.status === "completed" || data.status === "failed") {
        clearInterval(pollRef.current);
        pollRef.current = null;
        setBusy(false);
        setStatus({
          msg:
            data.status === "completed"
              ? "Job completed successfully"
              : `Job failed: ${data.error || "unknown"}`,
          cls: data.status === "completed" ? "ok" : "error",
        });
      }
    } catch {
      /* ignore transient poll errors */
    }
  }

  async function trigger(action) {
    const sel = [...selected];
    if (action !== "jira_tickets_only" && sel.length === 0) {
      setStatus({ msg: "Select at least one repository", cls: "error" });
      return;
    }
    setBusy(true);
    setJob(null);
    setStatus({
      msg:
        action === "jira_tickets_only"
          ? "Starting Jira-only job..."
          : `Starting job for ${sel.length} selected repos...`,
      cls: "running",
    });
    try {
      const data = await apiFetch("/graph-admin/trigger", {
        method: "POST",
        body: {
          action,
          repositories: sel,
          pull_latest_code: options.pullLatestCode,
          fetch_latest_jira_tickets: options.fetchLatestJira,
          include_jira_tickets: options.includeJira,
          build_embeddings: options.buildEmbeddings,
          embedding_model: options.embeddingModel,
          notes: options.notes || null,
        },
      });
      setStatus({
        msg: `Job started (${String(data.job_id).slice(0, 8)}...) for ${data.repository_count || sel.length} repos`,
        cls: "running",
      });
      setJob(data);
      startPolling(data.job_id);
    } catch (err) {
      setStatus({ msg: err.message, cls: "error" });
      setBusy(false);
    }
  }

  const stats = job ? deriveStats(job, options.buildEmbeddings) : null;
  const ActiveComponent = visibleTabs.find((t) => t.key === activeTab)?.Component;

  return (
    <>
      <Header />
      <main className={`dash${canRepos ? "" : " no-aside"}`}>
        {canRepos && (
          <JobSidebar options={options} setOption={setOption} trigger={trigger} busy={busy} />
        )}
        <section className="dash-main">
          {status.msg && <div className={`status-bar ${status.cls}`}>{status.msg}</div>}

          {canRepos && job && <JobProgress stats={stats} job={job} />}

          {visibleTabs.length === 0 ? (
            <EmptyState hasDocs={hasTab("docs")} />
          ) : (
            <>
              <nav className="tab-nav">
                {visibleTabs.map((t) => (
                  <button
                    key={t.key}
                    className={`tab-btn${activeTab === t.key ? " active" : ""}`}
                    onClick={() => setActiveTab(t.key)}
                  >
                    {t.label}
                  </button>
                ))}
              </nav>

              {ActiveComponent && (
                <ActiveComponent
                  // Props consumed only by the Repositories tab.
                  repos={repos}
                  excluded={excluded}
                  selected={selected}
                  setSelected={setSelected}
                  embeddingModel={options.embeddingModel}
                  setStatus={setStatus}
                />
              )}
            </>
          )}
        </section>
      </main>
    </>
  );
}

function EmptyState({ hasDocs }) {
  return (
    <div style={{ padding: "40px 0", color: "var(--muted)" }}>
      <p>Your role does not have access to any dashboard tabs.</p>
      {hasDocs && (
        <p>
          You can open the <Link to="/docs-portal">Documentation portal</Link>.
        </p>
      )}
    </div>
  );
}
