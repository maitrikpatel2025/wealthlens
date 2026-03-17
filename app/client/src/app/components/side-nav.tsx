"use client";

import { Plus, Upload, X, MessageSquare } from "lucide-react";
import type { Conversation, UsageMeter } from "@/types/api";

interface SideNavProps {
  isOpen: boolean;
  conversations: Conversation[];
  usage?: UsageMeter;
  onClose: () => void;
  onNewChat?: () => void;
  onUploadStatement?: () => void;
  onSelectConversation?: (id: string) => void;
}

export function SideNav({
  isOpen,
  conversations,
  usage,
  onClose,
  onNewChat,
  onUploadStatement,
  onSelectConversation,
}: SideNavProps) {
  return (
    <>
      {/* Backdrop (mobile) */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Panel */}
      <aside
        className={`fixed top-14 bottom-0 left-0 z-40 flex w-[280px] flex-col border-r border-slate-200 bg-white transition-transform duration-200 ease-out dark:border-slate-800 dark:bg-slate-950 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-800/50">
          <button
            onClick={onNewChat}
            className="flex h-9 flex-1 items-center justify-center gap-2 rounded-lg bg-emerald-600 text-sm font-medium text-white transition-colors hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600"
          >
            <Plus className="h-4 w-4" />
            New chat
          </button>
          <button
            onClick={onClose}
            className="ml-2 flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 lg:hidden dark:hover:bg-slate-800 dark:hover:text-slate-300"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Upload Shortcut */}
        <div className="px-3 pt-3">
          <button
            onClick={onUploadStatement}
            className="flex w-full items-center gap-2.5 rounded-lg border border-dashed border-slate-300 px-3 py-2.5 text-sm text-slate-600 transition-colors hover:border-emerald-400 hover:bg-emerald-50/50 hover:text-emerald-700 dark:border-slate-700 dark:text-slate-400 dark:hover:border-emerald-600 dark:hover:bg-emerald-950/30 dark:hover:text-emerald-400"
          >
            <Upload className="h-4 w-4" />
            Upload statement
          </button>
        </div>

        {/* Conversation History */}
        <div className="flex-1 overflow-y-auto px-3 pt-4">
          <p className="mb-2 px-2 text-xs font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Recent
          </p>
          <div className="space-y-0.5">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation?.(conv.id)}
                className={`flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors ${
                  conv.isActive
                    ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300"
                    : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800/60"
                }`}
              >
                <MessageSquare
                  className={`mt-0.5 h-4 w-4 shrink-0 ${
                    conv.isActive
                      ? "text-emerald-600 dark:text-emerald-400"
                      : "text-slate-400 dark:text-slate-500"
                  }`}
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{conv.title}</p>
                  <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-500">
                    {conv.timestamp}
                  </p>
                </div>
              </button>
            ))}
            {conversations.length === 0 && (
              <p className="px-2 py-4 text-center text-xs text-slate-400 dark:text-slate-500">
                No conversations yet
              </p>
            )}
          </div>
        </div>

        {/* Footer: Usage Meter */}
        <div className="border-t border-slate-100 px-3 py-3 dark:border-slate-800/50">
          {usage && (
            <div className="rounded-lg bg-slate-50 px-3 py-2.5 dark:bg-slate-900">
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  {usage.label || "Messages"}
                </span>
                <span className="text-xs tabular-nums text-slate-500 dark:text-slate-400 font-mono">
                  {usage.used}/{usage.limit}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                <div
                  className={`h-full rounded-full transition-all ${
                    usage.used / usage.limit > 0.8
                      ? "bg-amber-500"
                      : "bg-emerald-500"
                  }`}
                  style={{
                    width: `${Math.min((usage.used / usage.limit) * 100, 100)}%`,
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
