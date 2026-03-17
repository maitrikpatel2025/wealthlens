"use client";

import { Component, ReactNode, useRef, useState, useEffect } from "react";
import { WidgetSpec, PieData, BarData, LineData, TableData, GaugeData, SummaryData, TreemapData, SankeyData } from "@/types/widgets";
import { WidgetWrapper } from "./widget-wrapper";
import { PieWidget } from "./pie-widget";
import { BarWidget } from "./bar-widget";
import { LineWidget } from "./line-widget";
import { TableWidget } from "./table-widget";
import { GaugeWidget } from "./gauge-widget";
import { SummaryWidget } from "./summary-widget";
import { TreemapWidget } from "./treemap-widget";
import { SankeyWidget } from "./sankey-widget";

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

interface WidgetRendererProps {
  widgets: WidgetSpec[];
  onExpand: (widget: WidgetSpec) => void;
  onRemove: (widgetId: string) => void;
  onAskAbout: (widget: WidgetSpec) => void;
}

function renderWidgetContent(widget: WidgetSpec) {
  switch (widget.type) {
    case "pie":
      return <PieWidget data={widget.data as PieData} />;
    case "bar":
      return <BarWidget data={widget.data as BarData} />;
    case "line":
      return <LineWidget data={widget.data as LineData} />;
    case "table":
      return <TableWidget data={widget.data as TableData} />;
    case "gauge":
      return <GaugeWidget data={widget.data as GaugeData} />;
    case "summary":
      return <SummaryWidget data={widget.data as SummaryData} />;
    case "treemap":
      return <TreemapWidget data={widget.data as TreemapData} />;
    case "sankey":
      return <SankeyWidget data={widget.data as SankeyData} />;
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

export function WidgetRenderer({ widgets, onExpand, onRemove, onAskAbout }: WidgetRendererProps) {
  const gridRef = useRef<HTMLDivElement>(null);
  const [cols, setCols] = useState(2);

  useEffect(() => {
    const el = gridRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width ?? 0;
      setCols(width < 500 ? 1 : 2);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div
      ref={gridRef}
      className="grid gap-4 auto-rows-min"
      style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
    >
      {widgets.map((widget) => (
        <div key={widget.id} style={gridStyle(widget)} className="widget-animate-in min-w-0">
          <WidgetWrapper
            widget={widget}
            onExpand={onExpand}
            onRemove={onRemove}
            onAskAbout={onAskAbout}
          >
            <WidgetErrorBoundary title={widget.title}>
              {renderWidgetContent(widget)}
            </WidgetErrorBoundary>
          </WidgetWrapper>
        </div>
      ))}
    </div>
  );
}
