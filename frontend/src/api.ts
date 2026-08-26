import type { ColumnMapping, AnalyzeResponse } from "./types";

export class ApiError extends Error {}

export async function fetchHeaders(file: File): Promise<string[]> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/preview", { method: "POST", body: formData });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : "Could not read file";
    throw new ApiError(detail);
  }

  const data = await response.json();
  return data.headers;
}

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
  formData.append("revenue_col", mapping.revenue_col);
  if (mapping.segment_col) {
    formData.append("segment_col", mapping.segment_col);
  }

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