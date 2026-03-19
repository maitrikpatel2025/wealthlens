"use client";

import { SummaryData, SummaryMetric } from "@/types/widgets";
import { TrendingUp, TrendingDown } from "lucide-react";

interface SummaryWidgetProps {
  data: SummaryData;
}

function formatValue(metric: SummaryMetric): string {
  const v = metric.value;
  if (metric.format === "currency") return `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  if (metric.format === "percent") return `${Number(v).toFixed(2)}%`;
  if (metric.format === "number") return Number(v).toLocaleString();
  return String(v);
}

export function SummaryWidget({ data }: SummaryWidgetProps) {
  // Normalize: handle both array and single-object formats
  const metrics = Array.isArray(data) ? data : [data];

  return (
    <div className="grid grid-cols-2 gap-3">
      {metrics.map((metric: any) => (
        <div key={metric.label} className="rounded-lg bg-slate-50 dark:bg-slate-800 p-3">
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{metric.label}</p>
          <p className="text-lg font-bold text-slate-900 dark:text-slate-100">{formatValue(metric)}</p>
          {metric.change !== undefined && (
            <div className={`flex items-center gap-1 text-xs mt-1 ${metric.change >= 0 ? "text-emerald-600" : "text-red-500"}`}>
              {metric.change >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {metric.change >= 0 ? "+" : ""}{metric.change.toFixed(2)}%
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
