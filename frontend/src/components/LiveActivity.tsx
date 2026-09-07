import { useEffect, useState } from "react";
import { RefreshCw, AlertCircle, Radio } from "lucide-react";

interface ActivityEvent {
  name: string;
  type: string;
  status: string;
  last_error: string | null;
  last_sync: string;
}

export default function LiveActivity() {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/sources/activity/recent")
      .then((res) => (res.ok ? res.json() : { events: [] }))
      .then((data) => setEvents(data.events || []))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="dashboard-panel">
      <h3 className="panel-title">
        <Radio size={16} /> Live Activity
      </h3>

      {loading && <p className="hint">Loading...</p>}

      {!loading && events.length === 0 && (
        <div className="empty-state" style={{ padding: "24px 16px" }}>
          <p style={{ margin: 0 }}>No activity yet — sync a source to see events here</p>
        </div>
      )}

      {!loading && events.length > 0 && (
        <ul className="activity-list">
          {events.map((e, i) => (
            <li key={i}>
              <div className="activity-icon">
                {e.status === "error" ? (
                  <AlertCircle size={14} className="activity-icon-error" />
                ) : (
                  <RefreshCw size={14} className="activity-icon-ok" />
                )}
              </div>
              <div style={{ flex: 1 }}>
                <div className="activity-title">
                  {e.status === "error" ? "Sync failed" : "Synced"} · {e.name}
                </div>
                <div className="hint">
                  {e.type}
                  {e.last_error ? ` · ${e.last_error}` : ""}
                </div>
              </div>
              <div className="activity-time">{new Date(e.last_sync).toLocaleTimeString()}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
} 