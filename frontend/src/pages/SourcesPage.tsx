import { useEffect, useState } from "react";
import { Database, Plug, Webhook, RefreshCw } from "lucide-react";
import ConnectSourceModal from "../components/ConnectSourceModal";

interface Source {
  id: string;
  type: string;
  name: string;
  sync_mode: string;
  status: string;
  last_error?: string | null;
  last_sync?: string | null;
  created_at: string;
}

interface ConnectorType {
  id: "database" | "rest_api" | "webhook";
  name: string;
  description: string;
  icon: typeof Database;
}

const connectorTypes: ConnectorType[] = [
  {
    id: "database",
    name: "Database",
    description: "Connect Postgres, MySQL, or another SQL database",
    icon: Database,
  },
  {
    id: "rest_api",
    name: "REST API",
    description: "Poll any HTTP endpoint on a schedule",
    icon: Plug,
  },
  {
    id: "webhook",
    name: "Webhook",
    description: "Get a URL that services can push events to",
    icon: Webhook,
  },
];

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeConnector, setActiveConnector] = useState<ConnectorType | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<Record<string, string>>({});

  function loadSources() {
    setLoading(true);
    fetch("/api/sources")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load sources");
        return res.json();
      })
      .then(setSources)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadSources();
  }, []);

  async function handleDelete(id: string) {
    await fetch(`/api/sources/${id}`, { method: "DELETE" });
    loadSources();
  }

  async function handleSync(id: string) {
    setSyncingId(id);
    setSyncResult((prev) => ({ ...prev, [id]: "" }));
    try {
      const res = await fetch(`/api/sources/${id}/sync`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        setSyncResult((prev) => ({ ...prev, [id]: data.detail || "Sync failed." }));
      } else {
        setSyncResult((prev) => ({ ...prev, [id]: `Synced ${data.synced_rows} rows` }));
      }
    } catch {
      setSyncResult((prev) => ({ ...prev, [id]: "Sync failed — network error." }));
    } finally {
      setSyncingId(null);
      loadSources();
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Data Sources</h1>
        <p>Connect a service so Attribyt can see your sales and orders</p>
      </div>

      <h3 className="section-label">Connect a new source</h3>
      <div className="connector-grid">
        {connectorTypes.map((connector) => {
          const Icon = connector.icon;
          return (
            <div key={connector.id} className="connector-card">
              <div className="connector-icon">
                <Icon size={20} strokeWidth={1.8} />
              </div>
              <div className="connector-name">{connector.name}</div>
              <p className="connector-desc">{connector.description}</p>
              <button className="btn-secondary connector-btn" onClick={() => setActiveConnector(connector)}>
                Connect
              </button>
            </div>
          );
        })}
      </div>

      <h3 className="section-label">Connected sources</h3>

      {loading && <p className="hint">Loading...</p>}
      {error && <div className="error-banner">{error}</div>}

      {!loading && !error && sources.length === 0 && (
        <div className="empty-state">
          <p style={{ margin: 0 }}>No sources connected yet — pick a connector above to get started</p>
        </div>
      )}

      {sources.length > 0 && (
        <div className="summary-cards">
          {sources.map((s) => (
            <div key={s.id} className="summary-card source-card" style={{ textAlign: "left" }}>
              <div className="summary-label">{s.type}</div>
              <div style={{ fontWeight: 600, margin: "6px 0" }}>{s.name}</div>
              <div className={"source-status-text " + s.status}>{s.status}</div>
              {s.status === "error" && s.last_error && (
                <div className="source-error-msg">{s.last_error}</div>
              )}
              {s.last_sync && (
                <div className="hint" style={{ marginTop: 4 }}>
                  Last sync: {new Date(s.last_sync).toLocaleString()}
                </div>
              )}

              <div style={{ display: "flex", gap: 12, marginTop: 10, alignItems: "center" }}>
                {s.type === "database" && (
                  <button
                    className="btn-link"
                    onClick={() => handleSync(s.id)}
                    disabled={syncingId === s.id}
                    style={{ display: "flex", alignItems: "center", gap: 4 }}
                  >
                    <RefreshCw size={13} className={syncingId === s.id ? "spin" : ""} />
                    {syncingId === s.id ? "Syncing..." : "Sync now"}
                  </button>
                )}
                <button className="btn-link source-remove-btn" onClick={() => handleDelete(s.id)}>
                  Remove
                </button>
              </div>

              {syncResult[s.id] && (
                <div className="hint" style={{ marginTop: 6 }}>
                  {syncResult[s.id]}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeConnector && (
        <ConnectSourceModal
          connectorId={activeConnector.id}
          connectorName={activeConnector.name}
          onClose={() => setActiveConnector(null)}
          onCreated={loadSources}
        />
      )}
    </div>
  );
} 