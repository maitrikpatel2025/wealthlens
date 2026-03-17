"use client";

import { Treemap, ResponsiveContainer, Tooltip } from "recharts";
import { TreemapData } from "@/types/widgets";

const DEFAULT_COLORS = ["#059669", "#0284c7", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#65a30d", "#be185d"];

interface TreemapWidgetProps {
  data: TreemapData;
}

interface CustomContentProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  value?: number;
  index?: number;
  color?: string;
}

function CustomContent({ x = 0, y = 0, width = 0, height = 0, name = "", index = 0, color }: CustomContentProps) {
  if (width < 30 || height < 20) return null;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
        stroke="#fff"
        strokeWidth={2}
        rx={4}
      />
      {width > 50 && height > 30 && (
        <text
          x={x + width / 2}
          y={y + height / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#fff"
          fontSize={11}
          fontWeight={600}
        >
          {name}
        </text>
      )}
    </g>
  );
}

export function TreemapWidget({ data }: TreemapWidgetProps) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <Treemap
        data={data as any}
        dataKey="value"
        nameKey="name"
        content={<CustomContent />}
      >
        <Tooltip
          contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
          formatter={(value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
        />
      </Treemap>
    </ResponsiveContainer>
  );
}
