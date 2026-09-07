import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plug, BarChart3, Database, Package, ListOrdered, Zap } from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import BusinessFlow from "../components/BusinessFlow";
import LiveActivity from "../components/LiveActivity";

interface Source {
  id: string;
  type: string;
  name: string;
  status: string;
}

interface FlowData {
  total_rows: number;
  unique_users: number;
  conversions: number;
}

interface SummaryData {
  available: boolean;
  reason?: string;
  total_revenue?: number;
  orders?: number;
  conversion_rate?: number;
  customers?: number;
  avg_order_value?: number;
  channel_breakdown?: { channel: string; revenue: number }[];
  timeline?: { date: string; revenue: number; orders: number }[];
}

const PIE_COLORS = ["#4ade80", "#38bdf8", "#818cf8", "#fbbf24", "#f472b6", "#94a3b8", "#fb923c"];
const AXIS_STYLE = { fontSize: 11, fill: "#8b8d93" };
const GRID_STROKE = "#2a2b2e";
const TOOLTIP_STYLE = { background: "#1f2023", border: "1px solid #2a2b2e", borderRadius: 8 };
const TOOLTIP_LABEL_STYLE = { color: "#e8e9eb" };

export default function DashboardPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [flow, setFlow] = useState<FlowData | null>(null);
  const [summary, setSummary] = useState<SummaryData | null>(null);

  useEffect(() => {
    fetch("/api/sources")
      .then((res) => (res.ok ? res.json() : []))
      .then((all: Source[]) => {
        setSources(all);
        const activeSource = all.find(
          (s) => (s.type === "database" || s.type === "rest_api") && s.status === "connected"
        );
        if (activeSource) {
          fetch(`/api/sources/${activeSource.id}/flow`)
            .then((r) => (r.ok ? r.json() : null))
            .then(setFlow)
            .catch(() => setFlow(null));

          fetch(`/api/sources/${activeSource.id}/summary`)
            .then((r) => (r.ok ? r.json() : null))
            .then(setSummary)
            .catch(() => setSummary(null));
        }
      })
      .catch(() => setSources([]))
      .finally(() => setLoading(false));
  }, []);

  const hasSources = sources.length > 0;
  const hasSummary = !!summary?.available;

  const statCards: { label: string; value: string | number | null }[] = [
    { label: "Total Revenue", value: hasSummary ? `$${summary!.total_revenue!.toLocaleString()}` : null },
    { label: "Orders", value: hasSummary ? summary!.orders! : null },
    { label: "Conversion Rate", value: hasSummary ? `${summary!.conversion_rate}%` : null },
    { label: "Customers", value: hasSummary ? summary!.customers! : null },
    { label: "Avg. Order Value", value: hasSummary ? `$${summary!.avg_order_value}` : null },
  ];

  return (
    <div>
      <div className="page-header">
        <h1>Home</h1>
        <p>Your data control center — connect, analyze, act</p>
      </div>

      {summary && !summary.available && (
        <div className="warnings" style={{ marginBottom: 20 }}>
          <strong>Summary unavailable:</strong> {summary.reason}
        </div>
      )}

      <div className="home-grid">
        {/* Main column */}
        <div className="home-main">
          <div className="stat-row">
            {statCards.map((s) => (
              <div key={s.label} className="stat-card">
                <div className="stat-label">{s.label}</div>
                {s.value !== null ? (
                  <div className="stat-value">{s.value}</div>
                ) : (
                  <div className="stat-value-placeholder">—</div>
                )}
              </div>
            ))}
          </div>

          <div className="chart-row">
            <div className="chart-wrap">
              {hasSummary && summary!.timeline && summary!.timeline.length > 0 ? (
                <>
                  <h4 style={{ margin: "0 0 12px" }}>Revenue &amp; Orders</h4>
                  <ResponsiveContainer width="100%" height={240}>
                    <LineChart data={summary!.timeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
                      <XAxis dataKey="date" tick={AXIS_STYLE} />
                      <YAxis tick={AXIS_STYLE} />
                      <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Line type="monotone" dataKey="revenue" stroke="#4ade80" strokeWidth={2} dot={false} name="Revenue" />
                      <Line type="monotone" dataKey="orders" stroke="#38bdf8" strokeWidth={2} dot={false} name="Orders" />
                    </LineChart>
                  </ResponsiveContainer>
                </>
              ) : (
                <div className="placeholder-inner" style={{ margin: "40px auto" }}>
                  <h4>Revenue &amp; Orders</h4>
                  <p>Connect a source to see revenue and order trends over time</p>
                </div>
              )}
            </div>

            <div className="chart-wrap">
              {hasSummary && summary!.channel_breakdown && summary!.channel_breakdown.length > 0 ? (
                <>
                  <h4 style={{ margin: "0 0 12px" }}>Sales by Channel</h4>
                  <ResponsiveContainer width="100%" height={240}>
                    <PieChart>
                      <Pie
                        data={summary!.channel_breakdown}
                        dataKey="revenue"
                        nameKey="channel"
                        innerRadius={45}
                        outerRadius={80}
                        paddingAngle={2}
                      >
                        {summary!.channel_breakdown.map((_, i) => (
                          <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                    </PieChart>
                  </ResponsiveContainer>
                </>
              ) : (
                <div className="placeholder-inner" style={{ margin: "40px auto" }}>
                  <h4>Sales by Channel</h4>
                  <p>Channel breakdown appears once a source is connected</p>
                </div>
              )}
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

          {flow ? (
            <BusinessFlow
              totalRows={flow.total_rows}
              uniqueUsers={flow.unique_users}
              conversions={flow.conversions}
            />
          ) : (
            <div className="dashboard-panel">
              <h3 className="panel-title">Business Flow</h3>
              <div className="empty-state" style={{ padding: "28px 20px" }}>
                <p style={{ margin: 0 }}>Sync a Database source to see your funnel here</p>
              </div>
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="home-side">
          <LiveActivity />

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