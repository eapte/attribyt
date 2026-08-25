import type { ColumnMapping, AnalyzeResponse } from "./types";

export class ApiError extends Error {}

export async function analyzeCsv(
  file: File,
  mapping: ColumnMapping,
  model: string = "both"
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("model", model);
  formData.append("user_col", mapping.user_col);
  formData.append("timestamp_col", mapping.timestamp_col);
  formData.append("channel_col", mapping.channel_col);
  formData.append("event_col", mapping.event_col);
  formData.append("revenue_col", mapping.revenue_col);

  const response = await fetch("/api/analyze", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : "Analysis failed";
    throw new ApiError(detail);
  }

  return response.json();
}

/**
 * Reads only the first chunk of a CSV file to extract column headers,
 * without loading the whole file into memory twice or sending it to
 * the server just to inspect headers.
 */
export function readCsvHeaders(file: File): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    // A 64KB chunk is enough to reliably capture the header line for
    // any reasonably-formatted CSV, even wide tables with long names.
    const blob = file.slice(0, 65536);
    reader.onload = () => {
      const text = reader.result as string;
      const firstLine = text.split(/\r\n|\n/)[0] ?? "";
      const headers = firstLine.split(",").map((h) => h.trim().replace(/^"|"$/g, ""));
      resolve(headers.filter(Boolean));
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsText(blob);
  });
} 