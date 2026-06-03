import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function Header({ title = "Jira AI Admin" }) {
  const { user, logout, hasTab, isAdmin } = useAuth();
  const navigate = useNavigate();

  function onLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="app-header">
      <div className="app-header-left">
        <h1>{title}</h1>
        <nav className="app-nav">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          {hasTab("docs") && <NavLink to="/docs-portal">Documentation</NavLink>}
          {isAdmin && <NavLink to="/users">Users</NavLink>}
        </nav>
      </div>
      <div className="app-header-right">
        {user && (
          <span className="user-pill">
            <b>{user.email}</b>
            <span className="role-tag">{user.role}</span>
          </span>
        )}
        <button className="logout-btn" onClick={onLogout}>
          Sign out
        </button>
      </div>
    </header>
  );
}
