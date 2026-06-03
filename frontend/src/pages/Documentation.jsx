import { useEffect, useRef, useState } from "react";
import { apiFetch, apiDownload, triggerBlobDownload } from "../api";
import { renderMarkdown } from "../lib/markdown";
import Header from "../components/Header.jsx";

// Standalone Documentation portal. Reached only via its own URL (/docs-portal),
// not as a tab on the main dashboard.
export default function Documentation() {
  const [repos, setRepos] = useState([]);
  const [docTypes, setDocTypes] = useState([]);
  const [repo, setRepo] = useState("");
  const [docType, setDocType] = useState("");
  const [format, setFormat] = useState("docx");
  const [status, setStatus] = useState({ msg: "", cls: "" });
  const [busy, setBusy] = useState(false);
  const [downloadBusy, setDownloadBusy] = useState(false);
  const [result, setResult] = useState(null); // { markdown, filename }
  const [copied, setCopied] = useState(false);
  const cancelRef = useRef(false);

  useEffect(() => {
    cancelRef.current = false;
    (async () => {
      try {
        const data = await apiFetch("/graph-admin/repo-docs/repositories");
        const list = data.repositories || [];
        setRepos(list);
        const firstReady = list.find((r) => r.ready);
        if (firstReady) setRepo(firstReady.name);
        const types = data.doc_types || [];
        setDocTypes(types);
        if (types[0]) setDocType(types[0].id);
      } catch (err) {
        setStatus({ msg: err.message, cls: "error" });
      }
    })();
    return () => {
      cancelRef.current = true;
    };
  }, []);

  function pollDocJob(jobId, startedAt) {
    const MAX_MS = 600000;
    return new Promise((resolve, reject) => {
      const tick = async () => {
        if (cancelRef.current) return;
        try {
          const job = await apiFetch(`/graph-admin/repo-docs/jobs/${jobId}`);
          if (job.status === "done" || job.status === "error") {
            resolve(job);
            return;
          }
          if (Date.now() - startedAt > MAX_MS) {
            reject(new Error("Generation timed out"));
            return;
          }
          const secs = Math.round((Date.now() - startedAt) / 1000);
          setStatus({ msg: `Generating document with RepoTree… ${secs}s elapsed`, cls: "running" });
          setTimeout(tick, 3000);
        } catch (err) {
          reject(err);
        }
      };
      tick();
    });
  }

  async function generate() {
    if (!repo) {
      setStatus({ msg: "Pick a repository first", cls: "error" });
      return;
    }
    setBusy(true);
    setResult(null);
    setStatus({ msg: "Generating document with RepoTree… this can take 30–240 seconds", cls: "running" });
    const startedAt = Date.now();
    try {
      const start = await apiFetch("/graph-admin/repo-docs/generate", {
        method: "POST",
        body: { repo, doc_type: docType },
      });
      const job = await pollDocJob(start.job_id, startedAt);
      if (job.status === "error") throw new Error(job.error || "Document generation failed");
      setResult({ markdown: job.markdown || "", filename: job.filename || `${repo}.md` });
      setStatus({ msg: "Document ready", cls: "ok" });
    } catch (err) {
      setStatus({ msg: err.message, cls: "error" });
    } finally {
      setBusy(false);
    }
  }

  async function download() {
    if (!result?.markdown) return;
    const baseName = result.filename.replace(/\.md$/i, "");
    if (format === "md") {
      triggerBlobDownload(new Blob([result.markdown], { type: "text/markdown" }), `${baseName}.md`);
      return;
    }
    setDownloadBusy(true);
    setStatus({ msg: "Building Word document…", cls: "running" });
    try {
      await apiDownload("/graph-admin/repo-docs/export", {
        method: "POST",
        body: { markdown: result.markdown, filename: baseName },
        fallbackName: `${baseName}.docx`,
      });
      setStatus({ msg: "Document ready", cls: "ok" });
    } catch (err) {
      setStatus({ msg: err.message, cls: "error" });
    } finally {
      setDownloadBusy(false);
    }
  }

  function copy() {
    if (!result?.markdown) return;
    navigator.clipboard.writeText(result.markdown).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }

  return (
    <>
      <Header title="Documentation Portal" />
      <div className="docs-portal-body">
        <div className="tc-layout">
          <div className="tc-form-col">
            <p className="tc-section-label">Generate repository document</p>
            <div className="tc-field">
              <label className="tc-label">Repository <span className="tc-required">*</span></label>
              <select className="tc-select" value={repo} onChange={(e) => setRepo(e.target.value)}>
                {repos.length === 0 && <option value="">Loading repositories…</option>}
                {repos.map((r) => (
                  <option key={r.name} value={r.name} disabled={!r.ready}>
                    {r.ready ? r.name : `${r.name} (no artifacts — run a scan)`}
                  </option>
                ))}
              </select>
            </div>
            <div className="tc-field">
              <label className="tc-label">Document type</label>
              <select className="tc-select" value={docType} onChange={(e) => setDocType(e.target.value)}>
                {docTypes.map((t) => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </select>
            </div>
            <div className="tc-field">
              <label className="tc-label">Download format</label>
              <select className="tc-select" value={format} onChange={(e) => setFormat(e.target.value)}>
                <option value="docx">Word document (.docx)</option>
                <option value="md">Markdown (.md)</option>
              </select>
            </div>
            <button style={{ marginTop: 18 }} disabled={busy} onClick={generate}>
              Generate Document
            </button>
            {result && (
              <button className="secondary" style={{ marginTop: 10 }} disabled={downloadBusy} onClick={download}>
                Download
              </button>
            )}
            <div className={`status-bar ${status.cls}`} style={{ marginTop: 10 }}>{status.msg}</div>
            <p className="tc-optional" style={{ marginTop: 14, lineHeight: 1.5 }}>
              Documents are grounded in the repository's RepoTree architecture map and Repomix packed
              source. Generation can take 30–90 seconds for large repos.
            </p>
          </div>

          <div className="tc-result-col">
            {!result ? (
              <div className="tc-placeholder">
                Pick a repository and click <strong>Generate Document</strong>.
              </div>
            ) : (
              <>
                <div className="tc-stats">
                  <span className="tc-stat">{result.filename}</span>
                  <button
                    className="secondary"
                    style={{ width: "auto", minHeight: 32, padding: "5px 14px", fontSize: 13, marginLeft: "auto" }}
                    onClick={copy}
                  >
                    {copied ? "Copied!" : "Copy Markdown"}
                  </button>
                </div>
                <div className="tc-output" dangerouslySetInnerHTML={{ __html: renderMarkdown(result.markdown) }} />
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
