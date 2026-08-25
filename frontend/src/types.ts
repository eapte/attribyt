export interface ColumnMapping {
  user_col: string;
  timestamp_col: string;
  channel_col: string;
  event_col: string;
  revenue_col: string;
}

export interface SummaryData {
  total_users: number;
  total_touches: number;
  conversion_users: number;
  non_conversion_users: number;
  conversion_rate: number;
  avg_revenue_per_converting_user: number;
  total_revenue: number;
}

export interface ChannelComparison {
  channel: string;
  last_click?: number;
  linear?: number;
  time_decay?: number;
  markov?: number;
}

export interface TopPath {
  path: string;
  count: number;
  revenue: number;
}

export interface AnalyzeResponse {
  summary: SummaryData;
  comparison: ChannelComparison[];
  top_paths: TopPath[];
  data_quality: { warnings: string[] };
} 