"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, Legend } from "recharts";
import { BarData } from "@/types/widgets";

const DEFAULT_COLOR = "#059669";
const GROUPED_COLORS = ["#059669", "#3b82f6", "#f59e0b", "#ef4444"];

interface BarWidgetProps {
  data: BarData;
  onBarClick?: (item: { label: string; value: number }) => void;
}

function detectGroupedKeys(data: any[]): string[] {
  if (!data || data.length === 0) return [];
  const first = data[0];
  const numericKeys = Object.keys(first).filter(
    (k) => k !== "label" && k !== "name" && k !== "color" && typeof first[k] === "number"
  );
  // Grouped if there are multiple numeric keys (not just "value")
  if (numericKeys.length > 1) return numericKeys;
  if (numericKeys.length === 1 && numericKeys[0] !== "value") return numericKeys;
  return [];
}

export function BarWidget({ data, onBarClick }: BarWidgetProps) {
  // Normalize: accept both {label, value} and {name, value} formats
  const normalized = (data as any[]).map((entry: any) => ({
    ...entry,
    label: entry.label || entry.name || "Unknown",
  }));

  const groupedKeys = detectGroupedKeys(normalized);
  const isGrouped = groupedKeys.length > 1;

  if (isGrouped) {
    return (
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={normalized} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.2} />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} />
          <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
          <Tooltip
            contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
            formatter={(value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {groupedKeys.map((key, i) => (
            <Bar
              key={key}
              dataKey={key}
              fill={GROUPED_COLORS[i % GROUPED_COLORS.length]}
              radius={[4, 4, 0, 0]}
              name={key.charAt(0).toUpperCase() + key.slice(1)}
              onClick={onBarClick ? (entry: any) => {
                onBarClick({ label: entry.label || entry.name || "", value: entry[key] ?? 0 });
              } : undefined}
              style={onBarClick ? { cursor: "pointer" } : undefined}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={normalized} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.2} />
        <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} />
        <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
        <Tooltip
          contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
          formatter={(value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
        />
        <Bar
          dataKey="value"
          radius={[4, 4, 0, 0]}
          onClick={onBarClick ? (entry: any) => {
            onBarClick({ label: entry.label || entry.name || "", value: entry.value ?? 0 });
          } : undefined}
          style={onBarClick ? { cursor: "pointer" } : undefined}
        >
          {normalized.map((entry, i) => (
            <Cell key={i} fill={entry.color || DEFAULT_COLOR} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
