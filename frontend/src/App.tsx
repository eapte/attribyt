import { useState } from "react";
import FileUpload from "./components/FileUpload";
import ColumnMappingForm, { guessMapping } from "./components/ColumnMapping";
import ResultsView from "./components/ResultsView";
import { analyzeCsv, readCsvHeaders, ApiError } from "./api";
import type { AnalyzeResponse, ColumnMapping } from "./types";

type Stage = "upload" | "mapping" | "results";

export default function App() {
  const [stage, setStage] = useState<Stage>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<ColumnMapping | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileSelected(selectedFile: File) {
    setFile(selectedFile);
    setError(null);
    try {
      const parsedHeaders = await readCsvHeaders(selectedFile);
      if (parsedHeaders.length === 0) {
        setError("Could not read CSV headers — check the file format.");
        return;
      }
      setHeaders(parsedHeaders);
      setMapping(guessMapping(parsedHeaders));
      setStage("mapping");
    } catch {
      setError("Error reading the file.");
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

  return (
    <div className="app">
      <header className="app-header">
        <h1>Attribyt</h1>
        <p>Multi-touch attribution — local, private, no cloud</p>
      </header>

      <main>
        <div className="upload-row">
          <FileUpload onFileSelected={handleFileSelected} fileName={file?.name ?? null} />
          {stage !== "upload" && (
            <button className="btn-link" onClick={reset}>
              Reset
            </button>
          )}
        </div>

        {error && <div className="error-banner">{error}</div>}

        {stage === "mapping" && mapping && (
          <>
            <ColumnMappingForm headers={headers} mapping={mapping} onChange={setMapping} />
            <button className="btn-primary" onClick={handleAnalyze} disabled={loading}>
              {loading ? "Analyzing…" : "Run analysis"}
            </button>
          </>
        )}

        {stage === "results" && result && <ResultsView data={result} />}
      </main>
    </div>
  );
} 