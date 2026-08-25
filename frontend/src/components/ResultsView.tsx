import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";
import type { AnalyzeResponse } from "../types";

const MODEL_LABELS: Record<string, string> = {
  last_click: "Last-Click",
  linear: "Linear",
  time_decay: "Time Decay",
  markov: "Markov",
};

const MODEL_COLORS: Record<string, string> = {
  last_click: "#94a3b8",
  linear: "#60a5fa",
  time_decay: "#38bdf8",
  markov: "#fbbf24",
};

export default function ResultsView({ data }: { data: AnalyzeResponse }) {
  const { summary, comparison, top_paths, data_quality } = data;
  const modelKeys = Object.keys(MODEL_LABELS).filter((k) =>
    comparison.some((row) => row[k as keyof typeof row] !== undefined)
  );

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
        <SummaryCard label="Total revenue" value={`$${summary.total_revenue.toLocaleString()}`} />
        <SummaryCard
          label="Avg. order value"
          value={`$${summary.avg_revenue_per_converting_user.toFixed(2)}`}
        />
      </div>

      <section>
        <h3>Attribution model comparison</h3>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={comparison}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="channel" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
              <Legend formatter={(key: string) => MODEL_LABELS[key] ?? key} />
              {modelKeys.map((key) => (
                <Bar key={key} dataKey={key} fill={MODEL_COLORS[key]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
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
                  <td key={key}>${(row[key as keyof typeof row] as number)?.toFixed(2)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h3>Top converting paths</h3>
        <ol className="top-paths">
          {top_paths.map((p, i) => (
            <li key={i}>
              <span className="path-label">{p.path}</span>
              <span className="path-stats">
                {p.count}x · ${p.revenue.toLocaleString()}
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