"use client";

import { useState } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import { Paperclip } from "lucide-react";
import { PdfUpload } from "./pdf-upload";
import { Upload } from "lucide-react";

const initialMessage =
  "Welcome to WealthLens! I can help you analyze your Canadian investment portfolio. Upload a brokerage statement or ask me anything about your holdings, fees, or asset allocation.";

interface ChatPanelProps {
  onUploadComplete?: (result: any) => void;
  showWelcome?: boolean;
  onUploadClick?: () => void;
}

export function ChatPanel({
  onUploadComplete,
  showWelcome = false,
  onUploadClick,
}: ChatPanelProps) {
  const [showUpload, setShowUpload] = useState(false);

  const handleUploadComplete = (result: any) => {
    setShowUpload(false);
    onUploadComplete?.(result);
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-950">
      {/* Header — hidden in welcome mode (TopNav already shows branding) */}
      {!showWelcome && (
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
      )}

      {/* Welcome hero — shown when no widgets exist */}
      {showWelcome && (
        <div className="flex flex-col items-center px-6 pt-16 pb-6">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-900/40">
            <span className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">W</span>
          </div>
          <h1 className="mb-2 text-2xl font-bold text-slate-900 dark:text-slate-100">WealthLens</h1>
          <p className="mb-8 max-w-md text-center text-slate-500 dark:text-slate-400">
            AI-powered portfolio intelligence. Upload a brokerage statement to get started.
          </p>
          <button
            onClick={() => onUploadClick?.()}
            className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-6 py-4 text-left transition-all hover:border-emerald-300 hover:shadow-md dark:border-slate-700 dark:bg-slate-900 dark:hover:border-emerald-600"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
              <Upload size={20} />
            </div>
            <div>
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">Upload statement</span>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Import a brokerage PDF to get started</p>
            </div>
          </button>
        </div>
      )}

      {/* Chat */}
      <div className="flex-1 overflow-hidden">
        <CopilotChat
          className="h-full"
          instructions="You are WealthLens, a Canadian portfolio analysis assistant. Help users understand their investments, fees, and asset allocation. Never provide financial advice — only analysis and education."
          labels={{
            title: "",
            initial: showWelcome ? "" : initialMessage,
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
