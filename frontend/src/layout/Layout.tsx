import { NavLink, Outlet } from "react-router-dom";
import { Home, Database, BarChart3, Settings, Circle } from "lucide-react";

const navItems = [
  { to: "/", label: "Home", icon: Home, end: true },
  { to: "/sources", label: "Data Sources", icon: Database },
  { to: "/attribution", label: "Analytics", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="sidebar-logo-mark">Attribyt</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => "sidebar-link" + (isActive ? " active" : "")}
            >
              <Icon size={17} strokeWidth={1.8} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <Circle size={8} fill="currentColor" className="status-dot" />
          <span>Local mode</span>
        </div>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
} 