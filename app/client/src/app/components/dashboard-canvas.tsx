"use client";

import { useState } from "react";
import { WidgetSpec } from "@/types/widgets";
import { SmartSuggestionCards } from "./smart-suggestion-cards";
import { WidgetRenderer } from "./widgets/widget-renderer";
import { ExpandModal } from "./widgets/expand-modal";
import { Download, Printer, FlaskConical } from "lucide-react";

interface DashboardCanvasProps {
  widgets: WidgetSpec[];
  households: any[];
  onSuggestionSelect: (prompt: string) => void;
  onUploadClick: () => void;
  onRemoveWidget: (widgetId: string) => void;
  onAskAboutWidget: (widget: WidgetSpec) => void;
  onDataPointClick?: (widget: WidgetSpec, dataPoint: Record<string, any>) => void;
  onSimulateClick?: () => void;
}

export function DashboardCanvas({ widgets, households, onSuggestionSelect, onUploadClick, onRemoveWidget, onAskAboutWidget, onDataPointClick, onSimulateClick }: DashboardCanvasProps) {
  const [expandedWidget, setExpandedWidget] = useState<WidgetSpec | null>(null);
  const hasWidgets = widgets && widgets.length > 0;

  const handleExportPrint = () => {
    sessionStorage.setItem("wealthlens_export_widgets", JSON.stringify(widgets));
    window.open("/export", "_blank");
  };

  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(widgets, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `wealthlens-dashboard-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!hasWidgets) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">W</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">WealthLens</h1>
          <p className="text-slate-500 dark:text-slate-400 max-w-md">
            Upload a brokerage statement or ask a question to generate your personalized portfolio dashboard.
          </p>
        </div>
        <SmartSuggestionCards households={households} widgets={widgets} onSelect={onSuggestionSelect} onUploadClick={onUploadClick} />
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      {/* Toolbar */}
      <div className="sticky top-0 z-10 bg-slate-50/90 dark:bg-slate-950/90 backdrop-blur-sm border-b border-slate-200 dark:border-slate-800 px-6 py-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          Dashboard ({widgets.length} widget{widgets.length !== 1 ? "s" : ""})
        </h2>
        <div className="flex items-center gap-2">
          {onSimulateClick && (
            <button
              onClick={onSimulateClick}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors"
              title="Simulate portfolio changes"
            >
              <FlaskConical size={14} />
              Simulate
            </button>
          )}
          <button
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors"
            title="Download JSON"
          >
            <Download size={14} />
            JSON
          </button>
          <button
            onClick={handleExportPrint}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600 rounded-lg transition-colors"
            title="Print / PDF"
          >
            <Printer size={14} />
            Export
          </button>
        </div>
      </div>

      {/* Widgets */}
      <div className="p-6">
        <WidgetRenderer
          widgets={widgets}
          onExpand={setExpandedWidget}
          onRemove={onRemoveWidget}
          onAskAbout={onAskAboutWidget}
          onDataPointClick={onDataPointClick}
        />
      </div>

      {/* Suggested next */}
      {households && households.length > 0 && (
        <div className="px-6 pb-6">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Suggested next</p>
          <SmartSuggestionCards households={households} widgets={widgets} onSelect={onSuggestionSelect} onUploadClick={() => {}} />
        </div>
      )}

      {expandedWidget && (
        <ExpandModal
          widget={expandedWidget}
          onClose={() => setExpandedWidget(null)}
        />
      )}
    </div>
  );
}
