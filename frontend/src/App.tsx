import { useState } from "react";
import FileUpload from "./components/FileUpload";
import ColumnMappingForm, { guessMapping } from "./components/ColumnMapping";
import ResultsView from "./components/ResultsView";
import { analyzeCsv, fetchHeaders, ApiError } from "./api";
import type { AnalyzeResponse, ColumnMapping } from "./types";
import { CURRENCIES } from "./types";

type Stage = "upload" | "mapping" | "results";

export default function App() {
  const [stage, setStage] = useState<Stage>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<ColumnMapping | null>(null);
  const [currency, setCurrency] = useState(CURRENCIES[0]);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    setStage("upload");
    setFile(null);
    setHeaders([]);
    setMapping(null);
    setResult(null);
    setError(null);
  }

  if (stage === "upload") {
    return (
      <div className="app">
        <div className="hero">
          <div className="hero-logo">
            <h1>Attribyt</h1>
          </div>
          <p className="tagline">Multi-touch attribution tool — local, private</p>
          <FileUpload onFileSelected={handleFileSelected} fileName={null} hero />
          {loading && <p className="hint" style={{ marginTop: 16 }}>Reading file…</p>}
          {error && <div className="error-banner">{error}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Attribyt</h1>
        <p>Multi-touch attribution — local, private, no cloud</p>
      </header>

      <main>
        <div className="upload-row">
          <FileUpload onFileSelected={handleFileSelected} fileName={file?.name ?? null} />
          <button className="btn-link" onClick={reset}>
            Reset
          </button>
        </div>

        {error && <div className="error-banner">{error}</div>}

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

        {stage === "results" && result && <ResultsView data={result} currencySymbol={currency.symbol} />}
      </main>
    </div>
  );
} 