"use client";

import { WidgetSpec } from "@/types/widgets";
import { WidgetToolbar } from "./widget-toolbar";

interface WidgetWrapperProps {
  widget: WidgetSpec;
  onExpand: (widget: WidgetSpec) => void;
  onRemove: (widgetId: string) => void;
  onAskAbout: (widget: WidgetSpec) => void;
  children: React.ReactNode;
}

function confidenceColor(confidence?: number): string {
  if (confidence === undefined) return "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300";
  if (confidence > 0.8) return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400";
  if (confidence > 0.5) return "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400";
  return "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400";
}

export function WidgetWrapper({ widget, onExpand, onRemove, onAskAbout, children }: WidgetWrapperProps) {
  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2 min-w-0">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">{widget.title}</h3>
          {widget.confidence !== undefined && (
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${confidenceColor(widget.confidence)}`}>
              {Math.round(widget.confidence * 100)}%
            </span>
          )}
        </div>
        <WidgetToolbar
          onExpand={() => onExpand(widget)}
          onRemove={() => onRemove(widget.id)}
          onAskAbout={() => onAskAbout(widget)}
        />
      </div>
      {/* Body */}
      <div className="flex-1 p-4 min-h-0 min-w-0 overflow-hidden">
        {children}
      </div>
    </div>
  );
}
