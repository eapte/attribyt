import { useEffect, useState } from "react";
import { Database, Plug, Webhook, Clock } from "lucide-react";

interface Source {
  id: string;
  type: string;
  name: string;
  sync_mode: string;
  status: string;
  created_at: string;
}

interface ConnectorType {
  id: string;
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
  const [comingSoonId, setComingSoonId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/sources")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load sources");
        return res.json();
      })
      .then(setSources)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function handleConnect(id: string) {
    setComingSoonId(id);
    setTimeout(() => setComingSoonId(null), 1800);
  }

  return (
    <div>
      <div className="page-header">
        <h1>Data Sources</h1>
        <p>Connect a service so Attribyt can see your sales and orders</p>
      </div>

      <h3 className="section-label">Connect a new source</h3>
      <div className="connector-grid">
        {connectorTypes.map(({ id, name, description, icon: Icon }) => (
          <div key={id} className="connector-card">
            <div className="connector-icon">
              <Icon size={20} strokeWidth={1.8} />
            </div>
            <div className="connector-name">{name}</div>
            <p className="connector-desc">{description}</p>
            <button
              className="btn-secondary connector-btn"
              onClick={() => handleConnect(id)}
              disabled={comingSoonId === id}
            >
              {comingSoonId === id ? (
                <>
                  <Clock size={14} /> Coming soon
                </>
              ) : (
                "Connect"
              )}
            </button>
          </div>
        ))}
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
            <div key={s.id} className="summary-card" style={{ textAlign: "left" }}>
              <div className="summary-label">{s.type}</div>
              <div style={{ fontWeight: 600, margin: "6px 0" }}>{s.name}</div>
              <div className="hint">{s.status}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 