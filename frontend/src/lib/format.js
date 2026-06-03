export function fmtDate(val) {
  if (!val) return "—";
  try {
    return new Date(val).toLocaleString();
  } catch {
    return val;
  }
}

export function formatEta(seconds) {
  seconds = Number(seconds || 0);
  if (!Number.isFinite(seconds) || seconds <= 0) return "";
  if (seconds < 60) return `ETA ${Math.round(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (minutes < 60) return `ETA ${minutes}m ${secs}s`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `ETA ${hours}h ${mins}m`;
}

export function pct(done, total) {
  return total > 0 ? Math.round((Number(done) / Number(total)) * 100) : 0;
}
