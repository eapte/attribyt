import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell,
} from "recharts";
import type { AnalyzeResponse } from "../types";

const MODEL_LABELS: Record<string, string> = {
  last_click: "Last-Click",
  linear: "Linear",
  time_decay: "Time Decay",
  markov: "Markov",
};

const MODEL_COLORS: Record<string, string> = {
  last_click: "#6b7280",
  linear: "#38bdf8",
  time_decay: "#818cf8",
  markov: "#4ade80",
};

const PIE_COLORS = ["#4ade80", "#38bdf8", "#818cf8", "#fbbf24", "#f472b6", "#94a3b8", "#fb923c"];

const AXIS_STYLE = { fontSize: 12, fill: "#8b8d93" };
const GRID_STROKE = "#2a2b2e";
const TOOLTIP_STYLE = { background: "#1f2023", border: "1px solid #2a2b2e", borderRadius: 8 };
const TOOLTIP_LABEL_STYLE = { color: "#e8e9eb" };

export default function ResultsView({ data, currencySymbol }: { data: AnalyzeResponse; currencySymbol: string }) {
  const { summary, comparison, top_paths, segment_breakdown, data_quality } = data;
  const modelKeys = Object.keys(MODEL_LABELS).filter((k) =>
    comparison.some((row) => row[k as keyof typeof row] !== undefined)
  );

  const fmt = (value: number) => `${currencySymbol}${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

  const shareKey = modelKeys.includes("markov") ? "markov" : modelKeys[0];
  const pieData = comparison.map((row) => ({
    name: row.channel,
    value: (row[shareKey as keyof typeof row] as number) ?? 0,
  }));

  return (
    <div className="results">
      {data_quality.warnings.length > 0 && (
        <div className="warnings">
          <strong>Data quality notes:</strong>
          <ul>
            {data_quality.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="summary-cards">
        <SummaryCard label="Users" value={summary.total_users} />
        <SummaryCard label="Touchpoints" value={summary.total_touches} />
        <SummaryCard label="Conversion rate" value={`${summary.conversion_rate.toFixed(1)}%`} />
        <SummaryCard label="Total revenue" value={fmt(summary.total_revenue)} />
        <SummaryCard label="Avg. order value" value={fmt(summary.avg_revenue_per_converting_user)} />
      </div>

      <section>
        <h3>Attribution model comparison</h3>
        <div className="chart-row">
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={comparison}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
                <XAxis dataKey="channel" tick={AXIS_STYLE} />
                <YAxis tick={AXIS_STYLE} />
                <Tooltip formatter={(value: number) => fmt(value)} contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} />
                <Legend formatter={(key: string) => MODEL_LABELS[key] ?? key} wrapperStyle={{ fontSize: 13 }} />
                {modelKeys.map((key) => (
                  <Bar key={key} dataKey={key} fill={MODEL_COLORS[key]} radius={[4, 4, 0, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={340}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => fmt(value)} contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <table className="comparison-table">
          <thead>
            <tr>
              <th>Channel</th>
              {modelKeys.map((key) => (
                <th key={key}>{MODEL_LABELS[key]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {comparison.map((row) => (
              <tr key={row.channel}>
                <td>{row.channel}</td>
                {modelKeys.map((key) => (
                  <td key={key}>{fmt(row[key as keyof typeof row] as number)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {segment_breakdown.length > 0 && (
        <section>
          <h3>Revenue by segment</h3>
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Segment</th>
                <th>Conversions</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {segment_breakdown.map((row) => (
                <tr key={row.segment}>
                  <td>{row.segment}</td>
                  <td style={{ textAlign: "right" }}>{row.count}</td>
                  <td style={{ textAlign: "right" }}>{fmt(row.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section>
        <h3>Top converting paths</h3>
        <ol className="top-paths">
          {top_paths.map((p, i) => (
            <li key={i}>
              <span className="path-label">{p.path}</span>
              <span className="path-stats">
                {p.count}x · {fmt(p.revenue)}
              </span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="summary-card">
      <div className="summary-value">{value}</div>
      <div className="summary-label">{label}</div>
    </div>
  );
} 