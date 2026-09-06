import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Plug, BarChart3, Database, LineChart, PieChart as PieChartIcon,
  Package, ListOrdered, Zap,
} from "lucide-react";

interface Source {
  id: string;
  type: string;
  name: string;
  status: string;
}

const STAT_PLACEHOLDERS = [
  { label: "Total Revenue" },
  { label: "Orders" },
  { label: "Conversion Rate" },
  { label: "Customers" },
  { label: "Avg. Order Value" },
];

export default function DashboardPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/sources")
      .then((res) => (res.ok ? res.json() : []))
      .then(setSources)
      .catch(() => setSources([]))
      .finally(() => setLoading(false));
  }, []);

  const hasSources = sources.length > 0;

  return (
    <div>
      <div className="page-header">
        <h1>Home</h1>
        <p>Your data control center — connect, analyze, act</p>
      </div>

      <div className="home-grid">
        {/* Main column */}
        <div className="home-main">
          <div className="stat-row">
            {STAT_PLACEHOLDERS.map((s) => (
              <div key={s.label} className="stat-card">
                <div className="stat-label">{s.label}</div>
                <div className="stat-value-placeholder">—</div>
              </div>
            ))}
          </div>

          <div className="chart-row">
            <div className="chart-wrap home-chart-placeholder">
              <div className="placeholder-inner">
                <LineChart size={22} strokeWidth={1.6} />
                <h4>Revenue &amp; Orders</h4>
                <p>Connect a source to see revenue and order trends over time</p>
              </div>
            </div>
            <div className="chart-wrap home-chart-placeholder">
              <div className="placeholder-inner">
                <PieChartIcon size={22} strokeWidth={1.6} />
                <h4>Sales by Channel</h4>
                <p>Channel breakdown appears once a source is connected</p>
              </div>
            </div>
          </div>

          <div className="chart-row">
            <div className="chart-wrap home-chart-placeholder">
              <div className="placeholder-inner">
                <Package size={22} strokeWidth={1.6} />
                <h4>Top Products</h4>
                <p>Your best-selling products will show up here</p>
              </div>
            </div>
            <div className="chart-wrap home-chart-placeholder">
              <div className="placeholder-inner">
                <ListOrdered size={22} strokeWidth={1.6} />
                <h4>Recent Orders</h4>
                <p>Live order feed will show up here</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="home-side">
          <div className="dashboard-panel">
            <h3 className="panel-title">
              <Database size={16} /> Connected Sources
            </h3>

            {loading && <p className="hint">Loading...</p>}

            {!loading && !hasSources && (
              <div className="empty-state" style={{ padding: "24px 16px" }}>
                <p style={{ margin: 0 }}>No sources connected yet</p>
              </div>
            )}

            {!loading && hasSources && (
              <ul className="source-status-list">
                {sources.map((s) => (
                  <li key={s.id}>
                    <span className={"status-dot-small " + s.status} />
                    <span className="source-status-name">{s.name}</span>
                    <span className="source-status-type">{s.type}</span>
                    <span className="source-status-value">{s.status}</span>
                  </li>
                ))}
              </ul>
            )}

            <Link to="/sources" className="btn-link panel-footer-link">
              Manage sources →
            </Link>
          </div>

          <div className="dashboard-panel">
            <h3 className="panel-title">
              <Zap size={16} /> Quick Actions
            </h3>
            <div className="quick-actions-grid">
              <Link to="/sources" className="quick-action-tile">
                <Plug size={18} />
                <span>Connect a source</span>
              </Link>
              <Link to="/attribution" className="quick-action-tile">
                <BarChart3 size={18} />
                <span>Run analysis</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 