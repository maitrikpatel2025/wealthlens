"use client";

import { GaugeData } from "@/types/widgets";

interface GaugeWidgetProps {
  data: GaugeData;
}

export function GaugeWidget({ data }: GaugeWidgetProps) {
  const raw = data as any;
  const value = raw.value ?? 0;
  const min = raw.min ?? 0;
  const max = raw.max ?? 1;
  const label = raw.label ?? "";
  const thresholds = raw.thresholds;
  const range = max - min;
  const pct = Math.max(0, Math.min(1, (value - min) / range));
  const angle = -90 + pct * 180; // -90 to 90 degrees arc

  // Determine color from thresholds or default
  let color = "#059669";
  if (thresholds) {
    for (const t of [...thresholds].sort((a, b) => b.value - a.value)) {
      if (value >= t.value) {
        color = t.color;
        break;
      }
    }
  }

  const r = 80;
  const cx = 100;
  const cy = 95;

  // Arc path from -180 to 0 degrees (bottom half semicircle)
  const startAngle = Math.PI;
  const endAngle = Math.PI * (1 - pct);
  const x1 = cx + r * Math.cos(startAngle);
  const y1 = cy + r * Math.sin(startAngle);
  const x2 = cx + r * Math.cos(endAngle);
  const y2 = cy + r * Math.sin(endAngle);
  const largeArc = pct > 0.5 ? 1 : 0;

  return (
    <div className="flex flex-col items-center w-full">
      <svg viewBox="0 0 200 120" className="w-full max-w-[200px] h-auto">
        {/* Background arc */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          className="stroke-slate-200 dark:stroke-slate-700"
          strokeWidth="16"
          strokeLinecap="round"
        />
        {/* Value arc */}
        {pct > 0 && (
          <path
            d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
            fill="none"
            stroke={color}
            strokeWidth="16"
            strokeLinecap="round"
          />
        )}
        {/* Value text */}
        <text x={cx} y={cy - 10} textAnchor="middle" className="text-2xl font-bold fill-slate-900 dark:fill-slate-100">
          {value}
        </text>
        <text x={cx} y={cy + 10} textAnchor="middle" className="text-xs fill-slate-500 dark:fill-slate-400">
          {label}
        </text>
        {/* Min/Max labels */}
        <text x={cx - r} y={cy + 20} textAnchor="middle" className="text-[10px] fill-slate-400 dark:fill-slate-500">{min}</text>
        <text x={cx + r} y={cy + 20} textAnchor="middle" className="text-[10px] fill-slate-400 dark:fill-slate-500">{max}</text>
      </svg>
    </div>
  );
}
