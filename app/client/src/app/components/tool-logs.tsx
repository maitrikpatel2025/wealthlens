"use client"

import { Check } from "lucide-react"
import React from "react"
import type { ToolLog } from "@/types/api"

interface ToolLogsProps {
  logs: ToolLog[]
}

export function ToolLogs({ logs }: ToolLogsProps) {
  if (!logs || logs.length === 0) return null;
  return (
    <div className="flex flex-col gap-2 p-2">
      {logs.map((log) => (
        <div
          key={log.id}
          className={`flex items-center gap-3 rounded-lg px-3 py-2 border text-sm font-medium shadow-sm transition-colors
            ${
              log.status === "processing"
                ? "bg-yellow-50 dark:bg-yellow-950/30 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-300"
                : "bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800 text-green-800 dark:text-green-300"
            }
          `}
        >
          {log.status === "processing" ? (
            <span className="relative flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-4 w-4 bg-yellow-400"></span>
            </span>
          ) : (
            <Check size={18} className="text-green-600" />
          )}
          <span className="text-xs font-semibold">{log.message}</span>
        </div>
      ))}
    </div>
  )
}
