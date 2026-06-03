import { useEffect, useState } from "react";
import { apiFetch } from "../api";
import { useAuth } from "../auth.jsx";
import Header from "../components/Header.jsx";
import { fmtDate } from "../lib/format";

export default function Users() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [roleTabs, setRoleTabs] = useState({});
  const [banner, setBanner] = useState({ msg: "", cls: "" });
  const [form, setForm] = useState({ email: "", password: "", role: "viewer" });
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const [usersData, rolesData] = await Promise.all([
        apiFetch("/auth/users"),
        apiFetch("/auth/roles"),
      ]);
      setUsers(usersData);
      setRoles(rolesData.roles || []);
      setRoleTabs(rolesData.role_tabs || {});
      if (rolesData.roles?.length && !rolesData.roles.includes(form.role)) {
        setForm((f) => ({ ...f, role: rolesData.roles[0] }));
      }
    } catch (err) {
      setBanner({ msg: err.message, cls: "error" });
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createUser(e) {
    e.preventDefault();
    setBusy(true);
    setBanner({ msg: "", cls: "" });
    try {
      await apiFetch("/auth/users", {
        method: "POST",
        body: { email: form.email.trim(), password: form.password, role: form.role, is_active: true },
      });
      setBanner({ msg: `Created ${form.email.trim()}`, cls: "ok" });
      setForm((f) => ({ ...f, email: "", password: "" }));
      load();
    } catch (err) {
      setBanner({ msg: err.message, cls: "error" });
    } finally {
      setBusy(false);
    }
  }

  async function changeRole(u, role) {
    try {
      await apiFetch(`/auth/users/${u.id}`, { method: "PATCH", body: { role } });
      load();
    } catch (err) {
      setBanner({ msg: err.message, cls: "error" });
    }
  }

  async function toggleActive(u) {
    try {
      await apiFetch(`/auth/users/${u.id}`, { method: "PATCH", body: { is_active: !u.is_active } });
      load();
    } catch (err) {
      setBanner({ msg: err.message, cls: "error" });
    }
  }

  async function resetPassword(u) {
    const pw = window.prompt(`New password for ${u.email} (min 6 chars):`);
    if (!pw) return;
    try {
      await apiFetch(`/auth/users/${u.id}`, { method: "PATCH", body: { password: pw } });
      setBanner({ msg: `Password updated for ${u.email}`, cls: "ok" });
    } catch (err) {
      setBanner({ msg: err.message, cls: "error" });
    }
  }

  async function removeUser(u) {
    if (!window.confirm(`Delete user ${u.email}? This cannot be undone.`)) return;
    try {
      await apiFetch(`/auth/users/${u.id}`, { method: "DELETE" });
      load();
    } catch (err) {
      setBanner({ msg: err.message, cls: "error" });
    }
  }

  return (
    <>
      <Header title="Jira AI Admin" />
      <div className="page">
        <h2>User management</h2>
        <p className="sub">
          Create users and assign roles. Each role grants access to a fixed set of tabs (per-tab RBAC).
        </p>

        {banner.msg && <div className={`banner ${banner.cls}`}>{banner.msg}</div>}

        <form className="user-form" onSubmit={createUser}>
          <div className="tc-field">
            <label className="tc-label">Email</label>
            <input className="tc-input" type="email" required value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} placeholder="user@example.com" />
          </div>
          <div className="tc-field">
            <label className="tc-label">Password</label>
            <input className="tc-input" type="text" required minLength={6} value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} placeholder="min 6 chars" />
          </div>
          <div className="tc-field">
            <label className="tc-label">Role</label>
            <select className="tc-select" value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}>
              {roles.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
          <button type="submit" disabled={busy}>Add user</button>
        </form>

        <table>
          <thead>
            <tr>
              <th style={{ width: "26%" }}>Email</th>
              <th style={{ width: "16%" }}>Role</th>
              <th>Tabs</th>
              <th style={{ width: "10%" }}>Active</th>
              <th style={{ width: "14%" }}>Created</th>
              <th style={{ width: "16%" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>
                  <b>{u.email}</b>
                  {u.id === me.id && <span className="role-tag">you</span>}
                </td>
                <td>
                  <select className="tc-select" value={u.role} onChange={(e) => changeRole(u, e.target.value)} disabled={u.id === me.id}>
                    {roles.map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                    {!roles.includes(u.role) && <option value={u.role}>{u.role}</option>}
                  </select>
                </td>
                <td style={{ fontSize: 12, color: "var(--muted)" }}>
                  {(u.permissions || roleTabs[u.role] || []).join(", ") || "—"}
                </td>
                <td>
                  <span className={`badge ${u.is_active ? "ok" : "err"}`}>{u.is_active ? "active" : "disabled"}</span>
                </td>
                <td>{fmtDate(u.created_at)}</td>
                <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  <button className="secondary inline-btn" onClick={() => resetPassword(u)}>Reset PW</button>
                  {u.id !== me.id && (
                    <>
                      <button className="secondary inline-btn" onClick={() => toggleActive(u)}>
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                      <button className="danger inline-btn" onClick={() => removeUser(u)}>Delete</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
