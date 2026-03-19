"use client";

import { SankeyData } from "@/types/widgets";

const COLORS = ["#059669", "#0284c7", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#65a30d", "#be185d"];

interface SankeyWidgetProps {
  data: SankeyData;
}

/**
 * Simple SVG-based Sankey diagram.
 * Recharts Sankey requires recharts-sankey which may not be available,
 * so we render a custom SVG fallback.
 */
export function SankeyWidget({ data }: SankeyWidgetProps) {
  const { nodes, links } = data;
  if (!nodes.length || !links.length) {
    return <p className="text-sm text-slate-400 text-center py-8">No flow data available</p>;
  }

  const width = 500;
  const height = 250;
  const nodeWidth = 20;
  const padding = 20;

  // Determine left/right nodes from links
  const sourceIndices = new Set(links.map((l) => l.source));
  const targetIndices = new Set(links.map((l) => l.target));
  const leftNodes = [...sourceIndices].filter((i) => !targetIndices.has(i));
  const rightNodes = [...targetIndices].filter((i) => !sourceIndices.has(i));
  const middleNodes = [...sourceIndices].filter((i) => targetIndices.has(i));

  // Simple layout: left column, optional middle, right column
  const columns = [leftNodes, ...(middleNodes.length ? [middleNodes] : []), rightNodes];
  const colCount = columns.length;

  // Assign positions
  const nodePositions: Record<number, { x: number; y: number; h: number }> = {};
  const totalValue = links.reduce((s, l) => s + l.value, 0);

  columns.forEach((col, ci) => {
    const x = padding + (ci / (colCount - 1)) * (width - 2 * padding - nodeWidth);
    const colTotal = col.reduce((s, ni) => {
      const val = links.filter((l) => l.source === ni || l.target === ni).reduce((a, l) => a + l.value, 0);
      return s + val;
    }, 0);
    let yOffset = padding;
    col.forEach((ni) => {
      const val = links.filter((l) => l.source === ni || l.target === ni).reduce((a, l) => a + l.value, 0);
      const h = Math.max(10, (val / Math.max(colTotal, 1)) * (height - 2 * padding - col.length * 4));
      nodePositions[ni] = { x, y: yOffset, h };
      yOffset += h + 4;
    });
  });

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-[250px]">
      {/* Links */}
      {links.map((link, i) => {
        const src = nodePositions[link.source];
        const tgt = nodePositions[link.target];
        if (!src || !tgt) return null;
        const srcMid = src.y + src.h / 2;
        const tgtMid = tgt.y + tgt.h / 2;
        const thickness = Math.max(2, (link.value / totalValue) * 40);
        return (
          <path
            key={i}
            d={`M ${src.x + nodeWidth} ${srcMid} C ${(src.x + nodeWidth + tgt.x) / 2} ${srcMid}, ${(src.x + nodeWidth + tgt.x) / 2} ${tgtMid}, ${tgt.x} ${tgtMid}`}
            fill="none"
            stroke={COLORS[link.source % COLORS.length]}
            strokeWidth={thickness}
            opacity={0.3}
          />
        );
      })}
      {/* Nodes */}
      {Object.entries(nodePositions).map(([ni, pos]) => (
        <g key={ni}>
          <rect
            x={pos.x}
            y={pos.y}
            width={nodeWidth}
            height={pos.h}
            fill={COLORS[Number(ni) % COLORS.length]}
            rx={3}
          />
          <text
            x={pos.x + nodeWidth + 6}
            y={pos.y + pos.h / 2}
            dominantBaseline="middle"
            fontSize={10}
            className="fill-slate-600 dark:fill-slate-400"
          >
            {nodes[Number(ni)]?.name ?? ""}
          </text>
        </g>
      ))}
    </svg>
  );
}
