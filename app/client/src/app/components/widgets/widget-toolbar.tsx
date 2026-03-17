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
        className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
        title="Ask about this"
      >
        <MessageCircle size={14} />
      </button>
      <button
        onClick={onExpand}
        className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
        title="Expand"
      >
        <Maximize2 size={14} />
      </button>
      <button
        onClick={onRemove}
        className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-red-500 transition-colors"
        title="Remove"
      >
        <X size={14} />
      </button>
    </div>
  );
}
