// Ring Studio — diamond/gold/solitaire ring image-prompt generator.
//
// Assembles CELESTE-style luxury jewelry spec-sheet prompts from value banks.
// Pin any field via the dropdowns (blank = randomize), set a seed for
// reproducible designs, preview the master prompt + spec, optionally render an
// image, and batch-export prompts as JSONL for a 1000-image run.
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch, apiDownload } from "../api.js";

// The dropdown fields we expose, in display order. Each maps to a bank key.
const FORM_FIELDS = [
  ["ring_name", "Ring Name"],
  ["ring_subtitle", "Subtitle"],
  ["diamond_shape", "Diamond Shape"],
  ["carat", "Carat"],
  ["color", "Color"],
  ["clarity", "Clarity"],
  ["cut", "Cut"],
  ["metal", "Metal"],
  ["band_width", "Band Width"],
  ["setting", "Setting"],
  ["background", "Background"],
  ["accent_color", "Accent Color"],
  ["ring_size", "Ring Size"],
  ["motif", "Botanical Motif"],
];

// Meta keys shown in the spec summary, in catalog order.
const SPEC_ROWS = [
  ["diamond_shape", "Center Diamond"],
  ["carat", "Carat"],
  ["color", "Color"],
  ["clarity", "Clarity"],
  ["cut", "Cut"],
  ["metal", "Metal"],
  ["band_width", "Band Width"],
  ["setting", "Setting"],
  ["total_diamonds", "Total Diamonds"],
  ["accent_carat", "Accent Carat"],
  ["detail_label", "Detail View"],
  ["ring_size", "Ring Size"],
  ["motif", "Motif"],
];

export default function RingStudio() {
  const [banks, setBanks] = useState(null);
  const [overrides, setOverrides] = useState({});
  const [seed, setSeed] = useState("");
  const [result, setResult] = useState(null); // { prompt, meta, seed }
  const [views, setViews] = useState(null); // RingViewsResult { status, views[], message }
  const [busy, setBusy] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  // Batch controls.
  const [batchCount, setBatchCount] = useState(10);
  const [batchStart, setBatchStart] = useState(0);
  const [batching, setBatching] = useState(false);

  useEffect(() => {
    apiFetch("/ring-studio/banks")
      .then(setBanks)
      .catch((e) => setError(e.message));
  }, []);

  const setField = (key, value) =>
    setOverrides((o) => {
      const next = { ...o };
      if (value === "") delete next[key];
      else next[key] = value;
      return next;
    });

  const body = useCallback(() => {
    const s = seed.trim();
    return {
      seed: s === "" ? null : Number(s),
      overrides,
    };
  }, [seed, overrides]);

  const generate = async () => {
    setBusy(true);
    setError("");
    setViews(null);
    try {
      const data = await apiFetch("/ring-studio/prompt", { method: "POST", body: body() });
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const surprise = () => {
    setOverrides({});
    setSeed(String(Math.floor(Math.random() * 1_000_000)));
    // Generate on the next tick with the fresh seed.
    setTimeout(generate, 0);
  };

  const renderImages = async () => {
    if (!result) return;
    setRendering(true);
    setError("");
    try {
      // Pass the exact generated design (meta) so all five views match.
      const data = await apiFetch("/ring-studio/image", {
        method: "POST",
        body: { meta: result.meta, seed: result.seed },
      });
      setViews(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setRendering(false);
    }
  };

  const copyPrompt = async () => {
    if (!result?.prompt) return;
    try {
      await navigator.clipboard.writeText(result.prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked */
    }
  };

  const downloadBatch = async () => {
    setBatching(true);
    setError("");
    try {
      await apiDownload("/ring-studio/batch.jsonl", {
        method: "POST",
        body: { count: Number(batchCount), start_seed: Number(batchStart) },
        fallbackName: "ring_prompts.jsonl",
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setBatching(false);
    }
  };

  const pinnedCount = useMemo(() => Object.keys(overrides).length, [overrides]);
  const meta = result?.meta;

  return (
    <div className="ring-studio">
      <header className="ring-hero">
        <h2>💎 Ring Studio</h2>
        <p className="muted">
          Generate CELESTE-style luxury jewelry spec-sheet prompts for
          diamond / gold / solitaire rings. Pin any field below (blank =
          randomize), set a seed for reproducible designs, then preview the
          master prompt, render an image, or export a batch as JSONL.
        </p>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="ring-grid">
        {/* ── Design form ─────────────────────────────────────────── */}
        <section className="ring-form card">
          <h3>Design Spec</h3>
          <div className="ring-fields">
            {FORM_FIELDS.map(([key, label]) => (
              <label key={key} className="ring-field">
                <span>{label}</span>
                <select
                  className="tc-select"
                  value={overrides[key] || ""}
                  onChange={(e) => setField(key, e.target.value)}
                >
                  <option value="">Randomize</option>
                  {(banks?.banks?.[key] || []).map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>

          <div className="ring-seed-row">
            <label className="ring-field">
              <span>Seed (optional — reproducible)</span>
              <input
                value={seed}
                onChange={(e) => setSeed(e.target.value.replace(/[^0-9]/g, ""))}
                placeholder="e.g. 42"
                inputMode="numeric"
              />
            </label>
            <div className="ring-pins muted">
              {pinnedCount ? `${pinnedCount} field${pinnedCount > 1 ? "s" : ""} pinned` : "All randomized"}
            </div>
          </div>

          <div className="ring-actions">
            <button onClick={generate} disabled={busy || !banks}>
              {busy ? "Assembling…" : "Generate Prompt"}
            </button>
            <button className="secondary" onClick={surprise} disabled={busy || !banks}>
              🎲 Surprise Me
            </button>
            <button
              className="secondary"
              onClick={() => {
                setOverrides({});
                setSeed("");
              }}
              disabled={busy}
            >
              Reset
            </button>
          </div>

          <div className="ring-batch">
            <h4>Batch export</h4>
            <p className="muted">
              Generate a reproducible batch (seed = start + index) and download
              as <code>ring_prompts.jsonl</code>.
            </p>
            <div className="ring-batch-row">
              <label className="ring-field">
                <span>Count (1–1000)</span>
                <input
                  type="number"
                  min={1}
                  max={1000}
                  value={batchCount}
                  onChange={(e) => setBatchCount(e.target.value)}
                />
              </label>
              <label className="ring-field">
                <span>Start seed</span>
                <input
                  type="number"
                  value={batchStart}
                  onChange={(e) => setBatchStart(e.target.value)}
                />
              </label>
              <button className="secondary" onClick={downloadBatch} disabled={batching}>
                {batching ? "Building…" : "Download JSONL"}
              </button>
            </div>
          </div>
        </section>

        {/* ── Preview ─────────────────────────────────────────────── */}
        <section className="ring-preview card">
          {!result ? (
            <div className="ring-empty muted">
              <p>Configure a design and hit <b>Generate Prompt</b> to preview it.</p>
            </div>
          ) : (
            <>
              <div className="ring-titlebar">
                <div>
                  <div className="ring-name">{meta.ring_name}</div>
                  <div className="ring-subtitle">{meta.ring_subtitle}</div>
                </div>
                {result.seed != null && (
                  <span className="ring-seed-tag">seed {result.seed}</span>
                )}
              </div>

              <p className="ring-desc">{meta.description}</p>

              <table className="ring-spec">
                <tbody>
                  {SPEC_ROWS.map(([key, label]) => (
                    <tr key={key}>
                      <th>{label}</th>
                      <td>{String(meta[key])}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="ring-prompt-head">
                <h4>Master prompt</h4>
                <button className="link" onClick={copyPrompt}>
                  {copied ? "Copied ✓" : "Copy"}
                </button>
              </div>
              <pre className="ring-prompt">{result.prompt}</pre>

              <div className="ring-actions">
                <button onClick={renderImages} disabled={rendering}>
                  {rendering ? "Rendering 5 views…" : "🖼️ Render 5 Views"}
                </button>
                <span className="ring-render-hint muted">
                  Hero renders first, then Top · Side · Front · Detail re-render
                  from it — same ring across all five.
                </span>
              </div>

              {views ? <ViewsGallery result={views} /> : null}
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function ViewsGallery({ result }) {
  const notConfigured = result.status === "not_configured";
  return (
    <div className="ring-views">
      {result.message ? (
        <div className={notConfigured ? "ring-image-note muted" : "error-banner"}>
          {result.message}
        </div>
      ) : null}
      {result.model ? (
        <div className="ring-image-meta muted">Rendered with {result.model}</div>
      ) : null}
      <div className="ring-views-grid">
        {(result.views || []).map((v) => (
          <ViewCard key={v.view} v={v} />
        ))}
      </div>
    </div>
  );
}

function ViewCard({ v }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(v.prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked */
    }
  };
  return (
    <figure className="ring-view-card">
      {v.status === "rendered" && v.image_url ? (
        <a href={v.image_url} download title="Download PNG">
          <img src={v.image_url} alt={v.label} />
        </a>
      ) : v.status === "error" ? (
        <div className="ring-view-err">{v.message || "Render failed."}</div>
      ) : (
        <div className="ring-view-placeholder">
          <button className="link" onClick={copy}>
            {copied ? "Copied ✓" : "Copy prompt"}
          </button>
        </div>
      )}
      <figcaption>{v.label}</figcaption>
    </figure>
  );
}
