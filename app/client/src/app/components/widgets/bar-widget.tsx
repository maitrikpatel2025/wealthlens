"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";
import { BarData } from "@/types/widgets";

const DEFAULT_COLOR = "#059669";

interface BarWidgetProps {
  data: BarData;
}

export function BarWidget({ data }: BarWidgetProps) {
  // Normalize: accept both {label, value} and {name, value} formats
  const normalized = data.map((entry: any) => ({
    ...entry,
    label: entry.label || entry.name || "Unknown",
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={normalized} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} />
        <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
        <Tooltip
          contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
          formatter={(value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {normalized.map((entry, i) => (
            <Cell key={i} fill={entry.color || DEFAULT_COLOR} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
