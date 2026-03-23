"use client";

import { useState, useMemo } from "react";
import { GraphData, GraphNode, GraphLink } from "@/types/widgets";

interface GraphWidgetProps {
  data: GraphData;
}

const TYPE_COLORS: Record<string, string> = {
  holding: "#22c55e",
  sector: "#f59e0b",
  asset_class: "#a855f7",
  account: "#3b82f6",
  geography: "#06b6d4",
};

const TYPE_LABELS: Record<string, string> = {
  holding: "Holdings",
  sector: "Sectors",
  asset_class: "Asset Classes",
  account: "Accounts",
  geography: "Geography",
};

interface LayoutNode extends GraphNode {
  x: number;
  y: number;
  r: number;
}

export function GraphWidget({ data }: GraphWidgetProps) {
  const { nodes, links } = data;
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [filterNode, setFilterNode] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);

  const width = 600;
  const height = 400;
  const cx = width / 2;
  const cy = height / 2;

  // Layout: holdings in inner ring, categories in outer ring
  const layout = useMemo(() => {
    const holdingNodes = nodes.filter((n) => n.type === "holding");
    const categoryNodes = nodes.filter((n) => n.type !== "holding");

    const innerRadius = Math.min(width, height) * 0.22;
    const outerRadius = Math.min(width, height) * 0.40;
    const minNodeR = 4;
    const maxNodeR = 18;

    const maxWeight = Math.max(...nodes.map((n) => n.weight_pct || 1), 1);

    const positioned: LayoutNode[] = [];

    // Inner ring: holdings
    holdingNodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / Math.max(holdingNodes.length, 1) - Math.PI / 2;
      const r = minNodeR + ((node.weight_pct || 1) / maxWeight) * (maxNodeR - minNodeR);
      positioned.push({
        ...node,
        x: cx + innerRadius * Math.cos(angle),
        y: cy + innerRadius * Math.sin(angle),
        r: Math.max(minNodeR, Math.min(r, maxNodeR)),
      });
    });

    // Outer ring: categories
    categoryNodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / Math.max(categoryNodes.length, 1) - Math.PI / 2;
      const r = minNodeR + ((node.weight_pct || 1) / maxWeight) * (maxNodeR - minNodeR);
      positioned.push({
        ...node,
        x: cx + outerRadius * Math.cos(angle),
        y: cy + outerRadius * Math.sin(angle),
        r: Math.max(minNodeR + 1, Math.min(r, maxNodeR)),
      });
    });

    return positioned;
  }, [nodes, cx, cy, width, height]);

  // Node lookup for links
  const nodeMap = useMemo(() => {
    const map: Record<string, LayoutNode> = {};
    layout.forEach((n) => { map[n.id] = n; });
    return map;
  }, [layout]);

  // Connected set for hover/filter highlighting
  const activeNode = filterNode || hoveredNode;
  const connectedSet = useMemo(() => {
    if (!activeNode) return new Set<string>();
    const set = new Set<string>([activeNode]);
    links.forEach((link) => {
      if (link.source === activeNode) set.add(link.target);
      if (link.target === activeNode) set.add(link.source);
    });
    return set;
  }, [activeNode, links]);

  // Legend: unique types present
  const legendTypes = useMemo(() => {
    const types = new Set(nodes.map((n) => n.type));
    return Array.from(types);
  }, [nodes]);

  if (!nodes.length) {
    return <p className="text-sm text-slate-400 text-center py-8">No graph data available</p>;
  }

  const handleNodeClick = (nodeId: string) => {
    setFilterNode((prev) => (prev === nodeId ? null : nodeId));
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Zoom controls */}
      <div className="flex items-center gap-1.5 justify-end px-2">
        {filterNode && (
          <button
            onClick={() => setFilterNode(null)}
            className="px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 rounded hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors"
          >
            Clear filter
          </button>
        )}
        <button
          onClick={() => setZoom((z) => Math.min(z + 0.2, 2))}
          className="w-6 h-6 flex items-center justify-center rounded border border-slate-200 dark:border-slate-700 text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          +
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(z - 0.2, 0.5))}
          className="w-6 h-6 flex items-center justify-center rounded border border-slate-200 dark:border-slate-700 text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          -
        </button>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full touch-manipulation"
        style={{ minHeight: 300, maxHeight: 450, transform: `scale(${zoom})`, transformOrigin: "center" }}
      >
        {/* Links */}
        {links.map((link, i) => {
          const src = nodeMap[link.source];
          const tgt = nodeMap[link.target];
          if (!src || !tgt) return null;

          const isHighlighted = activeNode && (connectedSet.has(link.source) && connectedSet.has(link.target));
          const isDimmed = activeNode && !isHighlighted;

          // Curved link
          const dx = tgt.x - src.x;
          const dy = tgt.y - src.y;
          const mx = (src.x + tgt.x) / 2 + dy * 0.15;
          const my = (src.y + tgt.y) / 2 - dx * 0.15;

          return (
            <path
              key={`link-${i}`}
              d={`M ${src.x} ${src.y} Q ${mx} ${my} ${tgt.x} ${tgt.y}`}
              fill="none"
              stroke={src.color || "#94a3b8"}
              strokeWidth={isHighlighted ? 2 : 1}
              opacity={isDimmed ? 0.08 : isHighlighted ? 0.6 : 0.2}
            />
          );
        })}

        {/* Nodes */}
        {layout.map((node) => {
          const isHovered = hoveredNode === node.id;
          const isFiltered = filterNode === node.id;
          const isConnected = connectedSet.has(node.id);
          const isDimmed = activeNode && !isConnected;

          return (
            <g
              key={node.id}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              onClick={() => handleNodeClick(node.id)}
              onTouchEnd={() => handleNodeClick(node.id)}
              style={{ cursor: "pointer" }}
            >
              <circle
                cx={node.x}
                cy={node.y}
                r={isHovered ? node.r + 2 : node.r}
                fill={node.color || TYPE_COLORS[node.type] || "#94a3b8"}
                opacity={isDimmed ? 0.2 : 1}
                stroke={isHovered ? "#fff" : "none"}
                strokeWidth={isHovered ? 2 : 0}
              />
              <text
                x={node.x}
                y={node.y + node.r + 12}
                textAnchor="middle"
                fontSize={9}
                className="fill-slate-600 dark:fill-slate-400"
                opacity={isDimmed ? 0.2 : 1}
              >
                {node.label.length > 12 ? node.label.slice(0, 11) + "\u2026" : node.label}
              </text>
              {/* Tooltip on hover */}
              {isHovered && (
                <g>
                  <rect
                    x={node.x - 55}
                    y={node.y - node.r - 38}
                    width={110}
                    height={28}
                    rx={4}
                    fill="rgba(15, 23, 42, 0.9)"
                  />
                  <text
                    x={node.x}
                    y={node.y - node.r - 26}
                    textAnchor="middle"
                    fontSize={9}
                    fill="#fff"
                    fontWeight={600}
                  >
                    {node.label}
                  </text>
                  <text
                    x={node.x}
                    y={node.y - node.r - 15}
                    textAnchor="middle"
                    fontSize={8}
                    fill="#94a3b8"
                  >
                    {node.weight_pct.toFixed(1)}% &middot; ${(node.value / 1000).toFixed(1)}k
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 justify-center px-2">
        {legendTypes.map((type) => (
          <div key={type} className="flex items-center gap-1.5">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: TYPE_COLORS[type] || "#94a3b8" }}
            />
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {TYPE_LABELS[type] || type}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
