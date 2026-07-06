import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../api";
import { fmtDate, fmtRelative } from "../lib/format";

// Maps a per-collection health string to a status dot class + label.
const HEALTH = {
  ok: { cls: "ok", text: "Healthy" },
  empty: { cls: "warn", text: "Empty" },
  missing: { cls: "warn", text: "Not built" },
  unreachable: { cls: "err", text: "Unreachable" },
  unknown: { cls: "idle", text: "Unknown" },
};

// Live-updating health panel for every embedding collection. Polls fast while a
// build job is writing embeddings, slowly otherwise. `refreshKey` lets the
// parent force an immediate refresh (e.g. right after triggering a job).
export default function EmbeddingsStatus({ refreshKey = 0 }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(true);
  const timerRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const res = await apiFetch("/graph-admin/embeddings/status");
      setData(res);
      setError("");
      return res;
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function tick() {
      const res = await load();
      if (!active) return;
      // Poll every 3s while embeddings are being written, else every 20s.
      const delay = res && res.updating ? 3000 : 20000;
      timerRef.current = setTimeout(tick, delay);
    }
    tick();
    return () => {
      active = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [load, refreshKey]);

  const collections = data?.collections || [];
  const overallCls =
    !data || !data.reachable ? "err" : data.overall === "ok" ? "ok" : "warn";

  return (
    <div className="embed-panel">
      <button
        type="button"
        className="embed-head"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className={`embed-dot ${data?.updating ? "run" : overallCls}`} />
        <span className="embed-title">Embeddings</span>
        {data?.updating && <span className="embed-syncing">syncing…</span>}
        <span className="embed-chevron">{open ? "▾" : "▸"}</span>
      </button>

      {open && (
        <div className="embed-body">
          {error && <div className="embed-error">{error}</div>}
          {!data && !error && <div className="embed-empty">Loading…</div>}

          {data && !data.reachable && (
            <div className="embed-error">
              Qdrant unreachable{data.error ? `: ${data.error}` : ""}
            </div>
          )}

          {collections.map((c) => {
            const h = HEALTH[c.health] || HEALTH.unknown;
            return (
              <div className="embed-row" key={c.key} title={`${c.key}\nLast updated: ${fmtDate(c.last_updated)}`}>
                <span className={`embed-dot ${c.updating ? "run" : h.cls}`} />
                <div className="embed-row-main">
                  <div className="embed-row-top">
                    <span className="embed-label">{c.label}</span>
                    <span className="embed-count">
                      {c.points != null ? c.points.toLocaleString() : "—"}
                    </span>
                  </div>
                  <div className="embed-row-sub">
                    <span>{c.updating ? "updating…" : h.text}</span>
                    <span>·</span>
                    <span>{fmtRelative(c.last_updated)}</span>
                    {c.vector_dim ? <span>· {c.vector_dim}d</span> : null}
                  </div>
                </div>
              </div>
            );
          })}

          {data && (
            <button type="button" className="embed-refresh" onClick={load}>
              Refresh now
            </button>
          )}
        </div>
      )}
    </div>
  );
}
