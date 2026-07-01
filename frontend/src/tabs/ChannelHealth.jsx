import { useEffect, useState } from "react";
import { apiFetch } from "../api";

// Slack channel health: discover every channel ID the digests post to
// (role map + assignee DMs + env-pinned channels) and probe each one with a
// test message, flagging the IDs the bot can't post to (e.g. not_in_channel) —
// the failure that shows up as a red Slack node in n8n without naming the ID.
export default function ChannelHealth() {
  const [channels, setChannels] = useState([]);
  const [configured, setConfigured] = useState(true);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(null);
  const [results, setResults] = useState(null);

  async function loadChannels() {
    setError("");
    setLoading(true);
    try {
      const res = await apiFetch("/graph-admin/channel-health/channels");
      setChannels(res.channels || []);
      setConfigured(res.configured);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadChannels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runCheck(channelIds) {
    setError("");
    setChecking(true);
    setResults(null);
    setSummary(null);
    try {
      const res = await apiFetch("/graph-admin/channel-health/check", {
        method: "POST",
        body: channelIds ? { channel_ids: channelIds } : {},
      });
      setResults(res.results || []);
      setSummary({
        checked: res.checked,
        ok: res.ok_count,
        failed: res.failed_count,
        configured: res.configured,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setChecking(false);
    }
  }

  // Merge probe results back onto the discovered channel rows for display.
  const resultMap = {};
  (results || []).forEach((r) => {
    resultMap[r.channel_id] = r;
  });

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginBottom: 14,
          flexWrap: "wrap",
        }}
      >
        <span style={{ fontSize: 13, color: "var(--muted)" }}>
          Sends a test message to every Slack channel/DM the digests post to and
          flags the ones the bot can’t reach (e.g. <code>not_in_channel</code>).
        </span>
        <button
          style={{ width: "auto", minHeight: "unset", padding: "6px 16px", fontSize: 13 }}
          onClick={() => runCheck(null)}
          disabled={checking || loading}
        >
          {checking ? "Checking…" : "Run health check"}
        </button>
        <button
          className="secondary"
          style={{ width: "auto", minHeight: "unset", padding: "6px 12px", fontSize: 13 }}
          onClick={loadChannels}
          disabled={loading || checking}
        >
          Reload channels
        </button>
      </div>

      {!configured && (
        <div style={{ color: "var(--muted)", fontSize: 14, padding: "12px 0" }}>
          <code>SLACK_BOT_TOKEN</code> is not configured — discovery works but
          probes will all fail until the bot token is set in the server
          environment.
        </div>
      )}

      {summary && (
        <div className="stats-grid" style={{ marginBottom: 14 }}>
          <Stat value={summary.checked} label="Probed" />
          <Stat value={summary.ok} label="Reachable" />
          <Stat value={summary.failed} label="Failed" danger={summary.failed > 0} />
        </div>
      )}

      <table>
        <thead>
          <tr>
            <th style={{ width: "22%" }}>Channel ID</th>
            <th style={{ width: "34%" }}>Sources</th>
            <th style={{ width: "14%" }}>Status</th>
            <th style={{ width: "20%" }}>Error</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {channels.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ color: "var(--muted)" }}>
                {loading ? "Loading…" : "No channel IDs discovered."}
              </td>
            </tr>
          ) : (
            channels.map((c) => {
              const r = resultMap[c.channel_id];
              return (
                <tr key={c.channel_id}>
                  <td style={{ fontFamily: "monospace", fontSize: 12 }}>{c.channel_id}</td>
                  <td style={{ fontSize: 12, color: "var(--muted)" }}>
                    {(c.sources || []).join(", ")}
                  </td>
                  <td>
                    {!r ? (
                      <span className="badge">—</span>
                    ) : r.ok ? (
                      <span className="badge ok">OK</span>
                    ) : (
                      <span className="badge err">Failed</span>
                    )}
                  </td>
                  <td
                    style={{
                      fontSize: 12,
                      color: r && !r.ok ? "var(--danger)" : "var(--muted)",
                      fontFamily: r && !r.ok ? "monospace" : undefined,
                    }}
                  >
                    {r && !r.ok ? r.error : "—"}
                  </td>
                  <td>
                    <button
                      className="secondary"
                      style={{
                        width: "auto",
                        minHeight: "unset",
                        padding: "4px 10px",
                        fontSize: 12,
                      }}
                      onClick={() => runCheck([c.channel_id])}
                      disabled={checking}
                    >
                      Retest
                    </button>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      {error && (
        <div style={{ color: "var(--danger)", fontSize: 13, marginTop: 8 }}>{error}</div>
      )}
    </div>
  );
}

function Stat({ value, label, danger }) {
  return (
    <div className="stat-card">
      <div className="stat-value" style={danger ? { color: "var(--danger)" } : undefined}>
        {value}
      </div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
