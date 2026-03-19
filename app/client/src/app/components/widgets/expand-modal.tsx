"use client";

import { useEffect, useCallback } from "react";
import { WidgetSpec, PieData, BarData, LineData, TableData, GaugeData, SummaryData, TreemapData, SankeyData } from "@/types/widgets";
import { X } from "lucide-react";
import { PieWidget } from "./pie-widget";
import { BarWidget } from "./bar-widget";
import { LineWidget } from "./line-widget";
import { TableWidget } from "./table-widget";
import { GaugeWidget } from "./gauge-widget";
import { SummaryWidget } from "./summary-widget";
import { TreemapWidget } from "./treemap-widget";
import { SankeyWidget } from "./sankey-widget";

interface ExpandModalProps {
  widget: WidgetSpec;
  onClose: () => void;
}

function renderContent(widget: WidgetSpec) {
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

export function ExpandModal({ widget, onClose }: ExpandModalProps) {
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape") onClose();
  }, [onClose]);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`Expanded view: ${widget.title}`}
    >
      <div
        className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-[90vw] max-w-4xl max-h-[85vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{widget.title}</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>
        {/* Content */}
        <div className="flex-1 p-6 overflow-auto">
          <div className="min-h-[400px]">
            {renderContent(widget)}
          </div>
        </div>
      </div>
    </div>
  );
}
