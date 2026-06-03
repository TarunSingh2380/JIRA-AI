export default function JobProgress({ stats, job }) {
  if (!stats) return null;
  return (
    <>
      <div className="stats-grid">
        <StatCard value={stats.statStatus} label="Status" />
        <StatCard value={stats.statRepos} label="Repositories" />
        <StatCard value={stats.statJira} label="Jira Tickets" />
        <StatCard value={stats.statEmbeddings} label="Embeddings" />
        <StatCard value={stats.statAction} label="Action" />
      </div>

      <div>
        <ProgressSection label="Repository progress" pctValue={stats.repoPct} meta={stats.repoEtaText} />
        <ProgressSection label="Jira ticket progress" pctValue={stats.jiraPct} meta={stats.jiraEtaText} />
        {stats.showEmbeddingSection && (
          <ProgressSection
            label={stats.embeddingLabel}
            pctValue={stats.embeddingPct}
            meta={stats.embeddingEtaText}
            indeterminate={stats.embeddingIndeterminate}
          />
        )}
      </div>

      {job && (
        <pre>{JSON.stringify(job, null, 2)}</pre>
      )}
    </>
  );
}

function StatCard({ value, label }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function ProgressSection({ label, pctValue, meta, indeterminate }) {
  return (
    <div className="progress-section">
      <div className="progress-label">{label}</div>
      <div className="progress-track">
        <div
          className={`progress-fill${indeterminate ? " indeterminate" : ""}`}
          style={indeterminate ? undefined : { width: `${pctValue}%` }}
        />
      </div>
      <div className="progress-meta">{meta}</div>
    </div>
  );
}
