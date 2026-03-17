"use client";

import { useState } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import { Paperclip } from "lucide-react";
import { PdfUpload } from "./pdf-upload";

const initialMessage =
  "Welcome to WealthLens! I can help you analyze your Canadian investment portfolio. Upload a brokerage statement or ask me anything about your holdings, fees, or asset allocation.";

interface ChatPanelProps {
  onUploadComplete?: (result: any) => void;
}

export function ChatPanel({ onUploadComplete }: ChatPanelProps) {
  const [showUpload, setShowUpload] = useState(false);

  const handleUploadComplete = (result: any) => {
    setShowUpload(false);
    onUploadComplete?.(result);
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-950">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 dark:bg-emerald-500 flex items-center justify-center">
            <span className="text-white text-sm font-bold">W</span>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">WealthLens</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Portfolio Intelligence</p>
          </div>
        </div>
        <button
          onClick={() => setShowUpload(true)}
          className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          title="Upload statement"
        >
          <Paperclip size={18} />
        </button>
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-hidden">
        <CopilotChat
          className="h-full"
          instructions="You are WealthLens, a Canadian portfolio analysis assistant. Help users understand their investments, fees, and asset allocation. Never provide financial advice — only analysis and education."
          labels={{
            title: "",
            initial: initialMessage,
            placeholder: "Ask about your portfolio...",
          }}
        />
      </div>

      {/* Upload modal */}
      {showUpload && (
        <PdfUpload
          onUploadComplete={handleUploadComplete}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  );
}
