"use client";

import { WidgetSpec, PieData, BarData, LineData, TableData, GaugeData, SummaryData, TreemapData, SankeyData } from "@/types/widgets";
import { PieWidget } from "./widgets/pie-widget";
import { BarWidget } from "./widgets/bar-widget";
import { LineWidget } from "./widgets/line-widget";
import { TableWidget } from "./widgets/table-widget";
import { GaugeWidget } from "./widgets/gauge-widget";
import { SummaryWidget } from "./widgets/summary-widget";
import { TreemapWidget } from "./widgets/treemap-widget";
import { SankeyWidget } from "./widgets/sankey-widget";

interface ExportViewProps {
  widgets: WidgetSpec[];
}

function renderWidget(widget: WidgetSpec) {
  switch (widget.type) {
    case "pie": return <PieWidget data={widget.data as PieData} />;
    case "bar": return <BarWidget data={widget.data as BarData} />;
    case "line": return <LineWidget data={widget.data as LineData} />;
    case "table": return <TableWidget data={widget.data as TableData} />;
    case "gauge": return <GaugeWidget data={widget.data as GaugeData} />;
    case "summary": return <SummaryWidget data={widget.data as SummaryData} />;
    case "treemap": return <TreemapWidget data={widget.data as TreemapData} />;
    case "sankey": return <SankeyWidget data={widget.data as SankeyData} />;
    default: return null;
  }
}

function confidenceBadge(confidence?: number) {
  if (confidence === undefined) return null;
  let color = "bg-red-100 text-red-700";
  let label = "Low";
  if (confidence > 0.8) { color = "bg-emerald-100 text-emerald-700"; label = "High"; }
  else if (confidence > 0.5) { color = "bg-amber-100 text-amber-700"; label = "Medium"; }
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${color}`}>
      {label} ({Math.round(confidence * 100)}%)
    </span>
  );
}

export function ExportView({ widgets }: ExportViewProps) {
  return (
    <div className="export-container max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center">
            <span className="text-white text-lg font-bold">W</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">WealthLens Dashboard</h1>
            <p className="text-xs text-slate-500">Generated {new Date().toLocaleDateString("en-CA")}</p>
          </div>
        </div>
        <p className="text-xs text-slate-400">For informational purposes only. Not financial advice.</p>
      </div>

      {/* Widgets grid */}
      <div className="grid grid-cols-2 gap-6 print-grid">
        {widgets.map((widget) => (
          <div
            key={widget.id}
            className={`rounded-xl border border-slate-200 bg-white p-4 print-widget ${
              widget.gridPosition?.colSpan === 2 ? "col-span-2" : ""
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-900">{widget.title}</h3>
              {confidenceBadge(widget.confidence)}
            </div>
            {renderWidget(widget)}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-8 pt-4 border-t border-slate-200 text-center">
        <p className="text-xs text-slate-400">
          WealthLens Portfolio Analysis — {new Date().toLocaleDateString("en-CA")}
        </p>
      </div>
    </div>
  );
}
