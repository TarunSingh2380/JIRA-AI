// Zoho Tickets — enter a customer's email/phone, fetch and display their Zoho
// Desk tickets. Backs the "zoho" capability. The same POST /zoho/tickets API is
// intended to be reused by the customer portal (see the design doc).
import { useEffect, useState } from "react";
import { apiFetch } from "../api.js";
import { fmtDate } from "../lib/format.js";

// Zoho status → badge class. Anything unmapped falls back to a neutral pill.
function statusClass(status) {
  const s = (status || "").toLowerCase();
  if (s === "closed") return "badge idle";
  if (s === "open") return "badge run";
  if (s === "on hold" || s === "escalated") return "badge warn";
  return "badge ok";
}

function priorityClass(priority) {
  const p = (priority || "").toLowerCase();
  if (p === "high" || p === "urgent") return "badge err";
  if (p === "medium") return "badge warn";
  return "badge idle";
}

export default function ZohoTickets() {
  const [configured, setConfigured] = useState(null); // null = unknown yet
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null); // { configured, contact, tickets, message }

  // Probe configuration once so we can warn before the operator wastes a lookup.
  useEffect(() => {
    apiFetch("/zoho/status")
      .then((d) => setConfigured(!!d.configured))
      .catch(() => setConfigured(false));
  }, []);

  const fetchTickets = async (e) => {
    e?.preventDefault();
    if (!email.trim() && !phone.trim()) {
      setError("Enter a customer email or phone number.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiFetch("/zoho/tickets", {
        method: "POST",
        body: { email: email.trim() || null, phone: phone.trim() || null },
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const tickets = result?.tickets || [];

  return (
    <div className="zoho-tab">
      <header className="zoho-hero">
        <h2>🎫 Zoho Tickets</h2>
        <p className="muted">
          Enter a customer's email or phone number to look them up in Zoho Desk
          and view their support tickets and current statuses.
        </p>
      </header>

      {configured === false && (
        <div className="error-banner">
          Zoho Desk is not configured. Set <code>ZOHO_CLIENT_ID</code>,{" "}
          <code>ZOHO_CLIENT_SECRET</code>, <code>ZOHO_REFRESH_TOKEN</code> and{" "}
          <code>ZOHO_ORG_ID</code> in the server environment.
        </div>
      )}

      <form className="zoho-form card" onSubmit={fetchTickets}>
        <div className="zoho-fields">
          <label className="zoho-field">
            <span>Customer email</span>
            <input
              className="tc-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="customer@example.com"
              autoComplete="off"
            />
          </label>
          <label className="zoho-field">
            <span>Phone (optional)</span>
            <input
              className="tc-input"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91…"
              autoComplete="off"
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Fetching…" : "Fetch Tickets"}
          </button>
        </div>
      </form>

      {error ? <div className="error-banner">{error}</div> : null}

      {result && (
        <section className="zoho-results card">
          {result.contact && (
            <div className="zoho-contact">
              <div className="zoho-contact-name">{result.contact.name || "Customer"}</div>
              <div className="muted">
                {[result.contact.email, result.contact.phone].filter(Boolean).join(" · ")}
              </div>
            </div>
          )}

          {tickets.length > 0 ? (
            <div className="zoho-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Subject</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Created</th>
                    <th>Last Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((t) => (
                    <tr key={t.id}>
                      <td>{t.ticket_number ? `#${t.ticket_number}` : t.id}</td>
                      <td>{t.subject || "—"}</td>
                      <td>
                        <span className={statusClass(t.status)}>{t.status || "—"}</span>
                      </td>
                      <td>
                        <span className={priorityClass(t.priority)}>{t.priority || "—"}</span>
                      </td>
                      <td>{fmtDate(t.created_time)}</td>
                      <td>{fmtDate(t.modified_time)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="muted">{result.message || "No tickets found for this customer."}</p>
          )}
        </section>
      )}
    </div>
  );
}
