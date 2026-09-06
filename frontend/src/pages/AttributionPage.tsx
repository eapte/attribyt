import { useEffect, useState } from "react";
import FileUpload from "../components/FileUpload";
import ColumnMappingForm, { guessMapping } from "../components/ColumnMapping";
import ResultsView from "../components/ResultsView";
import { analyzeCsv, fetchHeaders, ApiError } from "../api";
import type { AnalyzeResponse, ColumnMapping } from "../types";
import { CURRENCIES } from "../types";

type Stage = "idle" | "mapping" | "results";
type InputMode = "file" | "source";

interface Source {
  id: string;
  type: string;
  name: string;
  status: string;
  last_sync?: string | null;
}

export default function AttributionPage() {
  const [mode, setMode] = useState<InputMode>("file");

  // File upload flow state
  const [stage, setStage] = useState<Stage>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<ColumnMapping | null>(null);
  const [currency, setCurrency] = useState(CURRENCIES[0]);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Source-based flow state
  const [sources, setSources] = useState<Source[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [sourceResult, setSourceResult] = useState<AnalyzeResponse | null>(null);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [sourceError, setSourceError] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "source") return;
    setSourcesLoading(true);
    fetch("/api/sources")
      .then((res) => (res.ok ? res.json() : []))
      .then((all: Source[]) => setSources(all.filter((s) => s.type === "database")))
      .catch(() => setSources([]))
      .finally(() => setSourcesLoading(false));
  }, [mode]);

  async function handleFileSelected(selectedFile: File) {
    setFile(selectedFile);
    setError(null);
    setLoading(true);
    try {
      const parsedHeaders = await fetchHeaders(selectedFile);
      if (parsedHeaders.length === 0) {
        setError("Could not read file headers — check the file format.");
        return;
      }
      setHeaders(parsedHeaders);
      setMapping(guessMapping(parsedHeaders));
      setStage("mapping");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error reading the file.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze() {
    if (!file || !mapping) return;
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeCsv(file, mapping);
      setResult(data);
      setStage("results");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Unknown error during analysis.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setStage("idle");
    setFile(null);
    setHeaders([]);
    setMapping(null);
    setResult(null);
    setError(null);
  }

  function switchMode(next: InputMode) {
    setMode(next);
    reset();
    setSourceResult(null);
    setSourceError(null);
    setSelectedSourceId(null);
  }

  async function handleAnalyzeSource(sourceId: string) {
    setSelectedSourceId(sourceId);
    setSourceLoading(true);
    setSourceError(null);
    setSourceResult(null);
    try {
      const res = await fetch(`/api/sources/${sourceId}/analyze`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        setSourceError(data.detail || "Analysis failed.");
        return;
      }
      setSourceResult(data);
    } catch {
      setSourceError("Network error while analyzing.");
    } finally {
      setSourceLoading(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Analytics</h1>
        <p>Multi-touch attribution insights from your data</p>
      </div>

      <div className="mode-toggle">
        <button
          className={"mode-btn" + (mode === "file" ? " active" : "")}
          onClick={() => switchMode("file")}
        >
          Upload a file
        </button>
        <button
          className={"mode-btn" + (mode === "source" ? " active" : "")}
          onClick={() => switchMode("source")}
        >
          Use connected source
        </button>
      </div>

      {mode === "source" && (
        <div className="workspace">
          {sourcesLoading && <p className="hint">Loading sources...</p>}

          {!sourcesLoading && sources.length === 0 && (
            <div className="empty-state">
              <h3>No database sources connected</h3>
              <p>Connect a Database source on the Data Sources page to analyze it here</p>
            </div>
          )}

          {!sourcesLoading && sources.length > 0 && (
            <>
              <h3 className="section-label">Choose a source</h3>
              <div className="source-picker">
                {sources.map((s) => (
                  <button
                    key={s.id}
                    className={"source-picker-item" + (selectedSourceId === s.id ? " active" : "")}
                    onClick={() => handleAnalyzeSource(s.id)}
                    disabled={sourceLoading}
                  >
                    <div style={{ fontWeight: 600 }}>{s.name}</div>
                    <div className="hint">
                      {s.status}
                      {s.last_sync ? ` · last sync ${new Date(s.last_sync).toLocaleString()}` : " · never synced"}
                    </div>
                  </button>
                ))}
              </div>

              {sourceLoading && <p className="hint" style={{ marginTop: 16 }}>Analyzing...</p>}
              {sourceError && <div className="error-banner">{sourceError}</div>}
              {sourceResult && (
                <div style={{ marginTop: 20 }}>
                  <ResultsView data={sourceResult} currencySymbol="$" />
                </div>
              )}
            </>
          )}
        </div>
      )}

      {mode === "file" && (
        <div className="workspace">
          <div className="upload-row">
            <FileUpload onFileSelected={handleFileSelected} fileName={file?.name ?? null} />
            {file && (
              <button className="btn-link" onClick={reset}>
                Reset
              </button>
            )}
          </div>

          {loading && stage === "idle" && <p className="hint">Reading file…</p>}
          {error && <div className="error-banner">{error}</div>}

          {stage === "idle" && !file && (
            <div className="empty-state">
              <h3>Upload a file to get started</h3>
              <p>CSV or Excel with your customer journey data</p>
            </div>
          )}

          {stage === "mapping" && mapping && (
            <>
              <ColumnMappingForm headers={headers} mapping={mapping} onChange={setMapping} />
              <label className="currency-field">
                <span>Currency</span>
                <select
                  value={currency.code}
                  onChange={(e) => setCurrency(CURRENCIES.find((c) => c.code === e.target.value)!)}
                >
                  {CURRENCIES.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </label>
              <button className="btn-primary" onClick={handleAnalyze} disabled={loading}>
                {loading ? "Analyzing…" : "Run analysis"}
              </button>
            </>
          )}

          {stage === "results" && result && (
            <ResultsView data={result} currencySymbol={currency.symbol} />
          )}
        </div>
      )}
    </div>
  );
} 