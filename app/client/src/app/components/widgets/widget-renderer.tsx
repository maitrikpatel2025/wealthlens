"use client";

import { Component, ReactNode, useRef, useState, useEffect } from "react";
import { WidgetSpec, PieData, BarData, LineData, TableData, GaugeData, SummaryData, TreemapData, SankeyData, ReportData, GraphData } from "@/types/widgets";
import { WidgetWrapper } from "./widget-wrapper";
import { PieWidget } from "./pie-widget";
import { BarWidget } from "./bar-widget";
import { LineWidget } from "./line-widget";
import { TableWidget } from "./table-widget";
import { GaugeWidget } from "./gauge-widget";
import { SummaryWidget } from "./summary-widget";
import { TreemapWidget } from "./treemap-widget";
import { SankeyWidget } from "./sankey-widget";
import { ReportWidget } from "./report-widget";
import { GraphWidget } from "./graph-widget";
import { composeDataPointQuestion } from "@/utils/compose-question";
import { MessageCircle } from "lucide-react";

// Error boundary to prevent one bad widget from crashing the dashboard
class WidgetErrorBoundary extends Component<{ children: ReactNode; title: string }, { hasError: boolean }> {
  constructor(props: { children: ReactNode; title: string }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return <p className="text-sm text-slate-400 p-4">Could not render &quot;{this.props.title}&quot;</p>;
    }
    return this.props.children;
  }
}

/** Banner shown when a data point is clicked — requires explicit "Ask in Chat" to send. */
function DataPointBanner({ question, onAsk, onDismiss }: { question: string; onAsk: () => void; onDismiss: () => void }) {
  return (
    <div className="mt-1.5 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/30 p-3 flex items-start gap-2">
      <MessageCircle size={14} className="text-emerald-600 dark:text-emerald-400 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-2">{question}</p>
        <div className="flex items-center gap-2 mt-2">
          <button
            onClick={onAsk}
            className="px-3 py-1 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-md transition-colors"
          >
            Ask in Chat
          </button>
          <button
            onClick={onDismiss}
            className="px-2 py-1 text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

interface WidgetRendererProps {
  widgets: WidgetSpec[];
  onExpand: (widget: WidgetSpec) => void;
  onRemove: (widgetId: string) => void;
  onAskAbout: (widget: WidgetSpec) => void;
  onDataPointClick?: (widget: WidgetSpec, dataPoint: Record<string, any>) => void;
  onReorder?: (widgets: WidgetSpec[]) => void;
}

function renderWidgetContent(
  widget: WidgetSpec,
  onDataPointClick?: (widget: WidgetSpec, dataPoint: Record<string, any>) => void,
) {
  const handleDataPoint = onDataPointClick
    ? (dp: Record<string, any>) => onDataPointClick(widget, dp)
    : undefined;

  switch (widget.type) {
    case "pie":
      return <PieWidget data={widget.data as PieData} onSliceClick={handleDataPoint} />;
    case "bar":
      return <BarWidget data={widget.data as BarData} onBarClick={handleDataPoint} />;
    case "line":
      return <LineWidget data={widget.data as LineData} />;
    case "table":
      return <TableWidget data={widget.data as TableData} onRowClick={handleDataPoint} />;
    case "gauge":
      return <GaugeWidget data={widget.data as GaugeData} />;
    case "summary":
      return <SummaryWidget data={widget.data as SummaryData} />;
    case "treemap":
      return <TreemapWidget data={widget.data as TreemapData} />;
    case "sankey":
      return <SankeyWidget data={widget.data as SankeyData} />;
    case "report":
      return <ReportWidget data={widget.data as ReportData} />;
    case "graph":
      return <GraphWidget data={widget.data as GraphData} />;
    default:
      return <p className="text-sm text-slate-400">Unknown widget type: {widget.type}</p>;
  }
}

function gridStyle(widget: WidgetSpec): React.CSSProperties {
  const pos = widget.gridPosition;
  if (!pos) return {};
  return {
    gridColumn: `${pos.col} / span ${pos.colSpan || 1}`,
    gridRow: `${pos.row} / span ${pos.rowSpan || 1}`,
  };
}

export function WidgetRenderer({ widgets, onExpand, onRemove, onAskAbout, onDataPointClick, onReorder }: WidgetRendererProps) {
  const gridRef = useRef<HTMLDivElement>(null);
  const [cols, setCols] = useState(2);
  const [pendingPreview, setPendingPreview] = useState<{ widgetId: string; widget: WidgetSpec; dataPoint: Record<string, any> } | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);
  const dragSrcId = useRef<string | null>(null);

  useEffect(() => {
    const el = gridRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width ?? 0;
      setCols(width >= 1200 ? 3 : width >= 500 ? 2 : 1);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const handleConfirmAsk = () => {
    if (pendingPreview && onDataPointClick) {
      onDataPointClick(pendingPreview.widget, pendingPreview.dataPoint);
    }
    setPendingPreview(null);
  };

  // Drag-to-reorder handlers
  const handleDragStart = (e: React.DragEvent, widgetId: string) => {
    dragSrcId.current = widgetId;
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent, widgetId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (widgetId !== dragSrcId.current) {
      setDragOverId(widgetId);
    }
  };

  const handleDragLeave = () => {
    setDragOverId(null);
  };

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    setDragOverId(null);
    const srcId = dragSrcId.current;
    if (!srcId || srcId === targetId || !onReorder) return;

    const reordered = [...widgets];
    const srcIdx = reordered.findIndex((w) => w.id === srcId);
    const tgtIdx = reordered.findIndex((w) => w.id === targetId);
    if (srcIdx === -1 || tgtIdx === -1) return;

    const [moved] = reordered.splice(srcIdx, 1);
    reordered.splice(tgtIdx, 0, moved);
    onReorder(reordered);
    dragSrcId.current = null;
  };

  const handleDragEnd = () => {
    dragSrcId.current = null;
    setDragOverId(null);
  };

  return (
    <div
      ref={gridRef}
      className="grid gap-4 auto-rows-min"
      style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
    >
      {widgets.map((widget) => {
        const localHandler = onDataPointClick
          ? (_w: WidgetSpec, dp: Record<string, any>) => setPendingPreview({ widgetId: widget.id, widget, dataPoint: dp })
          : undefined;
        const isPending = pendingPreview?.widgetId === widget.id;
        const isDragTarget = dragOverId === widget.id;

        return (
          <div
            key={widget.id}
            style={gridStyle(widget)}
            className={`widget-animate-in min-w-0 transition-all ${
              isDragTarget ? "ring-2 ring-emerald-400 ring-offset-2 dark:ring-offset-slate-950" : ""
            }`}
            draggable
            onDragStart={(e) => handleDragStart(e, widget.id)}
            onDragOver={(e) => handleDragOver(e, widget.id)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, widget.id)}
            onDragEnd={handleDragEnd}
          >
            <WidgetWrapper
              widget={widget}
              onExpand={onExpand}
              onRemove={onRemove}
              onAskAbout={onAskAbout}
            >
              <WidgetErrorBoundary title={widget.title}>
                {renderWidgetContent(widget, localHandler)}
              </WidgetErrorBoundary>
            </WidgetWrapper>
            {isPending && (
              <DataPointBanner
                question={composeDataPointQuestion(pendingPreview!.widget, pendingPreview!.dataPoint)}
                onAsk={handleConfirmAsk}
                onDismiss={() => setPendingPreview(null)}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
