export type WidgetType =
  | "pie"
  | "bar"
  | "line"
  | "table"
  | "gauge"
  | "summary"
  | "treemap"
  | "sankey"
  | "report"
  | "graph";

export interface GridPosition {
  col: number;
  row: number;
  colSpan?: number;
  rowSpan?: number;
}

export interface WidgetSpec {
  id: string;
  type: WidgetType;
  title: string;
  data: PieData | BarData | LineData | TableData | GaugeData | SummaryData | TreemapData | SankeyData | ReportData | GraphData;
  gridPosition?: GridPosition;
  confidence?: number;
}

// --- Per-widget data interfaces ---

export interface PieSlice {
  name: string;
  value: number;
  color?: string;
}
export type PieData = PieSlice[];

export interface BarDatum {
  label: string;
  value: number;
  color?: string;
}
export type BarData = BarDatum[];

export interface LineSeries {
  name: string;
  color?: string;
  data: { x: string; y: number }[];
}
export type LineData = LineSeries[];

export interface TableColumn {
  key: string;
  label: string;
  format?: "currency" | "percent" | "number" | "text";
}
export interface TableData {
  columns: TableColumn[];
  rows: Record<string, string | number>[];
}

export interface GaugeData {
  value: number;
  min: number;
  max: number;
  label: string;
  thresholds?: { value: number; color: string; label: string }[];
}

export interface SummaryMetric {
  label: string;
  value: string | number;
  change?: number;
  format?: "currency" | "percent" | "number" | "text";
}
export type SummaryData = SummaryMetric[];

export interface TreemapNode {
  name: string;
  value: number;
  color?: string;
  children?: TreemapNode[];
}
export type TreemapData = TreemapNode[];

export interface SankeyNode {
  name: string;
}
export interface SankeyLink {
  source: number;
  target: number;
  value: number;
}
export interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

export interface ReportData {
  markdown: string;
  generated_at: string;
  sections: string[];
  portfolio_value: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "holding" | "sector" | "asset_class" | "account" | "geography";
  value: number;
  weight_pct: number;
  color: string;
}
export interface GraphLink {
  source: string;
  target: string;
  type: "belongs_to" | "held_in" | "exposed_to" | "classified_as";
  value: number;
}
export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  total_value: number;
  node_count: number;
  link_count: number;
}
