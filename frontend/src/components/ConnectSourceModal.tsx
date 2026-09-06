import { useState } from "react";
import { X } from "lucide-react";

type ConnectorId = "database" | "rest_api" | "webhook";
type DbDriver = "sqlite" | "postgres" | "mysql";

interface Props {
  connectorId: ConnectorId;
  connectorName: string;
  onClose: () => void;
  onCreated: () => void;
}

export default function ConnectSourceModal({ connectorId, connectorName, onClose, onCreated }: Props) {
  const [name, setName] = useState("");
  const [driver, setDriver] = useState<DbDriver>("sqlite");
  const [query, setQuery] = useState("SELECT * FROM orders");
  const [host, setHost] = useState("");
  const [port, setPort] = useState("");
  const [database, setDatabase] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [url, setUrl] = useState("");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function buildCredentials(): Record<string, string> {
    if (connectorId === "database") {
      if (driver === "sqlite") {
        return { driver, query };
      }
      return { driver, host, port, database, username, password, query };
    }
    if (connectorId === "rest_api") {
      return { url, token };
    }
    return {};
  }

  function validate(): string | null {
    if (!name.trim()) return "Please give this source a name.";

    if (connectorId === "database") {
      if (driver === "sqlite") {
        if (!query.trim()) return "Query is required.";
      } else {
        if (!host.trim()) return "Host is required.";
        if (!port.trim()) return "Port is required.";
        if (!/^\d+$/.test(port.trim())) return "Port must be a number.";
        if (!database.trim()) return "Database name is required.";
        if (!username.trim()) return "Username is required.";
      }
    }

    if (connectorId === "rest_api") {
      if (!url.trim()) return "Base URL is required.";
      if (!/^https?:\/\//.test(url.trim())) return "URL must start with http:// or https://";
    }

    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: connectorId,
          name: name.trim(),
          credentials: buildCredentials(),
          sync_mode: connectorId === "webhook" ? "webhook" : "manual",
        }),
      });

      if (!res.ok) throw new Error("Server error while creating the source.");

      const created = await res.json();

      if (created.status === "error") {
        setError(created.last_error || "Connection test failed.");
        setLoading(false);
        onCreated();
        return;
      }

      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Connect {connectorName}</h3>
          <button className="modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          <label className="form-field">
            <span>Name</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={`e.g. "My Shop ${connectorName}"`}
              autoFocus
            />
          </label>

          {connectorId === "database" && (
            <>
              <label className="form-field">
                <span>Driver</span>
                <select value={driver} onChange={(e) => setDriver(e.target.value as DbDriver)}>
                  <option value="sqlite">SQLite (test sandbox — functional)</option>
                  <option value="postgres">PostgreSQL (coming soon)</option>
                  <option value="mysql">MySQL (coming soon)</option>
                </select>
              </label>

              {driver !== "sqlite" && (
                <p className="hint">
                  The {driver} driver isn't implemented yet — you can register the source, but syncing won't work until it's added.
                </p>
              )}

              {driver !== "sqlite" && (
                <>
                  <div className="form-row">
                    <label className="form-field">
                      <span>Host</span>
                      <input type="text" value={host} onChange={(e) => setHost(e.target.value)} placeholder="localhost" />
                    </label>
                    <label className="form-field" style={{ maxWidth: 100 }}>
                      <span>Port</span>
                      <input type="text" value={port} onChange={(e) => setPort(e.target.value)} placeholder="5432" />
                    </label>
                  </div>
                  <label className="form-field">
                    <span>Database name</span>
                    <input type="text" value={database} onChange={(e) => setDatabase(e.target.value)} />
                  </label>
                  <div className="form-row">
                    <label className="form-field">
                      <span>Username</span>
                      <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
                    </label>
                    <label className="form-field">
                      <span>Password</span>
                      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
                    </label>
                  </div>
                </>
              )}

              <label className="form-field">
                <span>Query</span>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  rows={3}
                  style={{
                    padding: "9px 11px",
                    borderRadius: 8,
                    border: "1px solid var(--border)",
                    fontSize: 14,
                    background: "var(--surface-2)",
                    color: "var(--text)",
                    fontFamily: "monospace",
                    resize: "vertical",
                  }}
                />
              </label>
              {driver === "sqlite" && (
                <p className="hint">
                  This runs against a seeded sample "orders" table so you can try out syncing without a real database.
                </p>
              )}
            </>
          )}

          {connectorId === "rest_api" && (
            <>
              <label className="form-field">
                <span>Base URL</span>
                <input type="text" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://api.example.com" />
              </label>
              <label className="form-field">
                <span>Auth token (optional)</span>
                <input type="text" value={token} onChange={(e) => setToken(e.target.value)} />
              </label>
            </>
          )}

          {connectorId === "webhook" && (
            <p className="hint">
              A receiving URL will be generated after creation. Note: actually receiving webhook events isn't implemented yet — the source will show as "pending" until then.
            </p>
          )}

          {error && <div className="error-banner">{error}</div>}

          <div className="modal-footer">
            <button type="button" className="btn-link" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" style={{ marginTop: 0 }} disabled={loading}>
              {loading ? "Testing connection..." : "Connect"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 