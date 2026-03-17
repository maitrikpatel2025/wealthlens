"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { LineData } from "@/types/widgets";

const DEFAULT_COLORS = ["#059669", "#0284c7", "#d97706", "#dc2626", "#7c3aed"];

interface LineWidgetProps {
  data: LineData;
}

export function LineWidget({ data }: LineWidgetProps) {
  // Normalize data: handle both LineSeries[] format and flat array format
  const rawData = data as any;

  if (!rawData || !Array.isArray(rawData) || rawData.length === 0) {
    return <p className="text-sm text-slate-400 p-4">No line data available</p>;
  }

  // Check if it's the expected LineSeries[] format (array of {name, data: [{x, y}]})
  const isSeriesFormat = rawData[0]?.data && Array.isArray(rawData[0].data);

  if (!isSeriesFormat) {
    // Flat array format: [{x: "...", y: N, ...}] or [{label: "...", value: N}]
    // Convert to simple line chart
    const flatData = rawData.map((item: any) => ({
      x: item.x || item.label || item.name || "",
      value: item.y ?? item.value ?? 0,
    }));

    return (
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={flatData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="x" tick={{ fontSize: 11, fill: "#64748b" }} />
          <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
          <Tooltip
            contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
            formatter={(value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
          />
          <Line type="monotone" dataKey="value" stroke={DEFAULT_COLORS[0]} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  // Standard LineSeries[] format
  const seriesData = rawData as { name: string; color?: string; data: { x: string; y: number }[] }[];
  const allXValues = [...new Set(seriesData.flatMap((s) => s.data.map((d) => d.x)))];
  const chartData = allXValues.map((x) => {
    const point: Record<string, string | number> = { x };
    seriesData.forEach((series) => {
      const match = series.data.find((d) => d.x === x);
      point[series.name] = match ? match.y : 0;
    });
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="x" tick={{ fontSize: 11, fill: "#64748b" }} />
        <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
        <Tooltip
          contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
          formatter={(value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          formatter={(value: string) => <span className="text-xs text-slate-600">{value}</span>}
        />
        {seriesData.map((series, i) => (
          <Line
            key={series.name}
            type="monotone"
            dataKey={series.name}
            stroke={series.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
