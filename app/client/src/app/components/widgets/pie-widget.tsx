"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { PieData } from "@/types/widgets";

const DEFAULT_COLORS = ["#059669", "#0284c7", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#65a30d", "#be185d"];

interface PieWidgetProps {
  data: PieData;
  onSliceClick?: (slice: { name: string; value: number }) => void;
}

export function PieWidget({ data, onSliceClick }: PieWidgetProps) {
  // Normalize data: accept both {name, value} and {label, value} formats
  const normalized = data.map((entry: any) => ({
    ...entry,
    name: entry.name || entry.label || "Unknown",
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={normalized}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={90}
          dataKey="value"
          nameKey="name"
          paddingAngle={2}
          onClick={onSliceClick ? (_data: any, index: number) => {
            const entry = normalized[index];
            if (entry) onSliceClick({ name: entry.name, value: entry.value });
          } : undefined}
          style={onSliceClick ? { cursor: "pointer" } : undefined}
        >
          {normalized.map((entry, i) => (
            <Cell key={`${entry.name}-${i}`} fill={entry.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
          contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          formatter={(value: string) => <span className="text-xs text-slate-600">{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
