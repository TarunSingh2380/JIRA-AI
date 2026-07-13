// Ring Studio — diamond/gold/solitaire ring image-prompt generator.
//
// Assembles CELESTE-style luxury jewelry spec-sheet prompts from value banks.
// Pin any field via the dropdowns (blank = randomize), set a seed for
// reproducible designs, preview the master prompt + spec, optionally render an
// image, and batch-export prompts as JSONL for a 1000-image run.
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch, apiDownload, apiObjectUrl } from "../api.js";

// The dropdown fields we expose, in display order. Each maps to a bank key.
const FORM_FIELDS = [
  ["ring_name", "Ring Name"],
  ["ring_subtitle", "Subtitle"],
  ["design_tradition", "Design Tradition"],
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
  ["design_tradition", "Design Tradition"],
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
  const [views, setViews] = useState(null); // RingViewsResult { status, views[], cost_usd, message }
  const [renderJobId, setRenderJobId] = useState(null); // for ZIP download
  const [quality, setQuality] = useState("medium"); // low | medium | high
  const [baseImages, setBaseImages] = useState([]); // scraped base designs
  const [baseImageId, setBaseImageId] = useState(""); // "" = generate from text
  const [basePreviewUrl, setBasePreviewUrl] = useState(""); // auth'd object URL
  const [busy, setBusy] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  // Batch controls.
  const [batchCount, setBatchCount] = useState(10);
  const [batchStart, setBatchStart] = useState(0);
  const [batching, setBatching] = useState(false);

  // Base-designs batch (render one global-style ring from every scraped product).
  const [baseBatchJobId, setBaseBatchJobId] = useState(null);
  const [baseBatch, setBaseBatch] = useState(null); // RingBatchResult (live + final)
  const [baseBatchRunning, setBaseBatchRunning] = useState(false);

  useEffect(() => {
    apiFetch("/ring-studio/banks")
      .then(setBanks)
      .catch((e) => setError(e.message));
    // Scraped base designs (from scraper.py) available to seed a render.
    apiFetch("/ring-studio/base-images")
      .then((d) => setBaseImages(d.images || []))
      .catch(() => {}); // optional — absence just hides the picker
  }, []);

  // Load an auth'd preview of the selected base design (an <img> can't send the
  // JWT the endpoint requires, so we fetch the bytes and hold an object URL).
  useEffect(() => {
    if (!baseImageId) {
      setBasePreviewUrl("");
      return;
    }
    let objUrl;
    let alive = true;
    apiObjectUrl(`/ring-studio/base-image?id=${encodeURIComponent(baseImageId)}`)
      .then((u) => {
        if (alive) {
          objUrl = u;
          setBasePreviewUrl(u);
        } else {
          URL.revokeObjectURL(u);
        }
      })
      .catch(() => setBasePreviewUrl(""));
    return () => {
      alive = false;
      if (objUrl) URL.revokeObjectURL(objUrl);
    };
  }, [baseImageId]);

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
    setViews(null);
    setRenderJobId(null);
    try {
      // Rendering four views takes ~40–60s, so the API returns a job id and we
      // poll for the result — this keeps each request short of proxy timeouts.
      // Pass the exact generated design (meta) so all four views match.
      const { job_id } = await apiFetch("/ring-studio/image", {
        method: "POST",
        body: {
          meta: result.meta,
          seed: result.seed,
          quality,
          base_image_id: baseImageId || null,
        },
      });
      setRenderJobId(job_id);
      const job = await pollRenderJob(job_id);
      if (job.status === "failed") {
        setError(job.error || "Rendering failed.");
      } else {
        setViews(job.result);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setRendering(false);
    }
  };

  const downloadZip = async () => {
    if (!renderJobId) return;
    try {
      await apiDownload(`/ring-studio/image/${renderJobId}/zip`, {
        fallbackName: "ring-views.zip",
      });
    } catch (e) {
      setError(e.message);
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

  const generateFromAllBases = async () => {
    setBaseBatchRunning(true);
    setError("");
    setBaseBatch(null);
    setBaseBatchJobId(null);
    try {
      const { job_id } = await apiFetch("/ring-studio/render-base-designs", {
        method: "POST",
        body: { quality },
      });
      setBaseBatchJobId(job_id);
      const job = await pollBatchJob(job_id, (r) => setBaseBatch(r));
      if (job.status === "failed") {
        setError(job.error || "Base-designs batch failed.");
      } else {
        setBaseBatch(job.result);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBaseBatchRunning(false);
    }
  };

  const downloadBaseBatchZip = async () => {
    if (!baseBatchJobId) return;
    try {
      await apiDownload(`/ring-studio/render-base-designs/${baseBatchJobId}/zip`, {
        fallbackName: "ring-base-designs.zip",
      });
    } catch (e) {
      setError(e.message);
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

          <div className="ring-base-batch">
            <h4>Base designs → global styles</h4>
            <p className="muted">
              Take every scraped base product and render one better global-style
              ring image for each — one folder per product, downloadable as a
              single ZIP. Uses the <b>{quality}</b> quality above.
            </p>
            {(() => {
              const baseCount = new Set(
                baseImages.map((i) => `${i.gender}/${i.product}`),
              ).size;
              return (
                <>
                  <div className="ring-base-batch-row">
                    <button
                      onClick={generateFromAllBases}
                      disabled={baseBatchRunning || baseCount === 0}
                    >
                      {baseBatchRunning
                        ? "Generating…"
                        : baseCount === 0
                          ? "✨ Generate from all base designs"
                          : `✨ Generate from all ${baseCount} base designs`}
                    </button>
                    {baseBatch &&
                    baseBatch.status === "completed" &&
                    (baseBatch.items || []).some((it) =>
                      (it.result?.views || []).some((v) => v.status === "rendered"),
                    ) ? (
                      <button className="secondary" onClick={downloadBaseBatchZip}>
                        ⬇ Download all as ZIP
                      </button>
                    ) : null}
                  </div>
                  {baseCount === 0 ? (
                    <p className="muted">
                      Button is disabled because no scraped base designs were
                      found. Run <code>scraper.py</code> to populate them, then
                      reload.
                    </p>
                  ) : null}
                  {baseBatch ? (
                    <BaseBatchProgress result={baseBatch} running={baseBatchRunning} />
                  ) : null}
                </>
              );
            })()}
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

              <div className="ring-render-controls">
                <label className="ring-field ring-quality">
                  <span>Quality</span>
                  <select
                    className="tc-select"
                    value={quality}
                    onChange={(e) => setQuality(e.target.value)}
                    disabled={rendering}
                  >
                    <option value="high">High (sharpest · costliest)</option>
                    <option value="medium">Medium (balanced)</option>
                    <option value="low">Low (fastest · cheapest)</option>
                  </select>
                </label>
                {baseImages.length > 0 ? (
                  <label className="ring-field ring-base">
                    <span>Base design</span>
                    <select
                      className="tc-select"
                      value={baseImageId}
                      onChange={(e) => setBaseImageId(e.target.value)}
                      disabled={rendering}
                    >
                      <option value="">None — generate from text</option>
                      {baseImages.map((img) => (
                        <option key={img.id} value={img.id}>
                          {[img.gender, img.product, img.filename]
                            .filter(Boolean)
                            .join(" · ")}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}
                <button onClick={renderImages} disabled={rendering}>
                  {rendering ? "Rendering 4 views…" : "🖼️ Render 4 Views"}
                </button>
              </div>
              {baseImageId && basePreviewUrl ? (
                <div className="ring-base-preview">
                  <img src={basePreviewUrl} alt="Selected base design" />
                  <span className="muted">
                    Base silhouette — reinterpreted in the{" "}
                    {meta?.design_tradition
                      ? meta.design_tradition.split(" (")[0]
                      : "selected"}{" "}
                    tradition.
                  </span>
                </div>
              ) : null}
              <span className="ring-render-hint muted">
                {baseImageId
                  ? "Hero re-renders the chosen base design in a global tradition; Top · Side · Laydown then carry that same new ring forward."
                  : "Rendered in sequence — Hero renders first, then Top · Side · Laydown each re-render from it, carrying the same ring forward so nothing is re-invented."}
              </span>

              {views ? <ViewsGallery result={views} onDownloadZip={downloadZip} /> : null}
            </>
          )}
        </section>
      </div>
    </div>
  );
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Poll a queued render until it finishes. Each GET is cheap and returns fast,
// so it never hits the gateway timeout that blocked the old inline render.
async function pollRenderJob(jobId, { intervalMs = 2500, timeoutMs = 5 * 60 * 1000 } = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const job = await apiFetch(`/ring-studio/image/${jobId}`);
    if (job.status === "completed" || job.status === "failed") return job;
    await sleep(intervalMs);
  }
  throw new Error("Rendering timed out — the images may still be processing. Try again shortly.");
}

// Poll the base-designs batch, surfacing per-product progress via onProgress.
// The batch is long (products × views), so the timeout is generous.
async function pollBatchJob(jobId, onProgress, { intervalMs = 3000, timeoutMs = 20 * 60 * 1000 } = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const job = await apiFetch(`/ring-studio/render-base-designs/${jobId}`);
    if (job.result && onProgress) onProgress(job.result);
    if (job.status === "completed" || job.status === "failed") return job;
    await sleep(intervalMs);
  }
  throw new Error("Batch timed out — it may still be processing. Try again shortly.");
}

const fmtUsd = (n) =>
  typeof n === "number" ? `$${n.toFixed(n < 0.1 ? 4 : 3)}` : null;

// Per-product progress + status for the base-designs batch.
function BaseBatchProgress({ result, running }) {
  const cost = fmtUsd(result.cost_usd);
  const pct = result.total ? Math.round((result.completed / result.total) * 100) : 0;
  return (
    <div className="ring-base-batch-status">
      <div className="ring-base-batch-head muted">
        {running
          ? `Rendering ${result.completed}/${result.total} products… (${pct}%)`
          : `Done — ${result.completed}/${result.total} products`}
        {cost ? ` · ${cost}` : null}
      </div>
      {result.message ? <div className="muted">{result.message}</div> : null}
      <ul className="ring-base-batch-list">
        {(result.items || []).map((it, i) => {
          const rendered = (it.result?.views || []).filter((v) => v.status === "rendered").length;
          const ok = it.result && it.result.status !== "error" && !it.error;
          return (
            <li key={`${it.base_image_id}-${i}`} className={ok ? "" : "ring-base-batch-fail"}>
              <span className="ring-base-batch-name">{it.label || it.product}</span>
              <span className="muted">
                {it.design_tradition ? it.design_tradition.split(" (")[0] : ""}
                {it.result ? ` · ${rendered ? "✓ rendered" : "no image"}` : ""}
                {it.error ? ` · ${it.error}` : ""}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function ViewsGallery({ result, onDownloadZip }) {
  const notConfigured = result.status === "not_configured";
  const renderedCount = (result.views || []).filter((v) => v.status === "rendered").length;
  const cost = fmtUsd(result.cost_usd);
  return (
    <div className="ring-views">
      {result.message ? (
        <div className={notConfigured ? "ring-image-note muted" : "error-banner"}>
          {result.message}
        </div>
      ) : null}

      {renderedCount > 0 ? (
        <div className="ring-views-toolbar">
          <div className="ring-image-meta muted">
            {result.model ? `Rendered with ${result.model}` : null}
            {result.quality ? ` · ${result.quality} quality` : null}
            {cost ? (
              <>
                {" · "}
                <b>Cost: {cost}</b>
                <span className="ring-cost-note"> (est. for {renderedCount} image{renderedCount > 1 ? "s" : ""})</span>
              </>
            ) : null}
          </div>
          <button className="secondary" onClick={onDownloadZip}>
            ⬇ Download all as ZIP
          </button>
        </div>
      ) : result.model ? (
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
      <figcaption>
        {v.label}
        {v.status === "rendered" && typeof v.cost_usd === "number" ? (
          <span className="ring-view-cost muted"> · {fmtUsd(v.cost_usd)}</span>
        ) : null}
      </figcaption>
    </figure>
  );
}
