"use client";

import { Maximize2, MessageCircle, X } from "lucide-react";

interface WidgetToolbarProps {
  onExpand: () => void;
  onRemove: () => void;
  onAskAbout: () => void;
}

export function WidgetToolbar({ onExpand, onRemove, onAskAbout }: WidgetToolbarProps) {
  return (
    <div className="flex items-center gap-1">
      <button
        onClick={onAskAbout}
        className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
        title="Ask about this"
        aria-label="Ask about this widget"
      >
        <MessageCircle size={14} />
      </button>
      <button
        onClick={onExpand}
        className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
        title="Expand"
        aria-label="Expand widget"
      >
        <Maximize2 size={14} />
      </button>
      <button
        onClick={onRemove}
        className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
        title="Remove"
        aria-label="Remove widget"
      >
        <X size={14} />
      </button>
    </div>
  );
}
