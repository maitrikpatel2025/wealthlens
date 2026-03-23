"use client";

import { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import { TableData, TableColumn } from "@/types/widgets";

interface TableWidgetProps {
  data: TableData;
  onRowClick?: (rowData: Record<string, any>) => void;
}

function formatCell(value: string | number, format?: string): string {
  if (value === undefined || value === null) return "—";
  if (typeof value === "string" && (value === "—" || value === "N/A" || value === "")) return value || "—";
  const num = Number(value);
  if (format === "currency") {
    if (isNaN(num)) return String(value);
    return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  if (format === "percent") {
    if (isNaN(num)) return "—";
    return `${num.toFixed(2)}%`;
  }
  if (format === "number") {
    if (isNaN(num)) return String(value);
    return num.toLocaleString();
  }
  return String(value);
}

export function TableWidget({ data: rawData, onRowClick }: TableWidgetProps) {
  // Normalize: handle multiple data shapes
  const data: TableData = (() => {
    const d = rawData as any;
    if (d && d.columns && d.rows) {
      // Normalize columns: string[] → TableColumn[]
      const cols: TableColumn[] = d.columns.map((c: any, i: number) => {
        if (typeof c === "string") return { key: String(i), label: c, format: "text" as const };
        return c;
      });
      // Normalize rows: if rows are arrays of primitives → convert to keyed objects
      const rows = d.rows.map((row: any) => {
        if (Array.isArray(row)) {
          const obj: Record<string, string | number> = {};
          cols.forEach((col, i) => { obj[col.key] = row[i] ?? ""; });
          return obj;
        }
        return row;
      });
      return { columns: cols, rows };
    }
    if (Array.isArray(d) && d.length > 0) {
      const keys = Object.keys(d[0]);
      return {
        columns: keys.map((k) => ({ key: k, label: k, format: "text" as const })),
        rows: d,
      };
    }
    return { columns: [], rows: [] };
  })();
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const sortedRows = [...data.rows].sort((a, b) => {
    if (!sortKey) return 0;
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    if (typeof aVal === "number" && typeof bVal === "number") {
      return sortDir === "asc" ? aVal - bVal : bVal - aVal;
    }
    return sortDir === "asc"
      ? String(aVal).localeCompare(String(bVal))
      : String(bVal).localeCompare(String(aVal));
  });

  return (
    <div className="overflow-x-auto max-h-[300px]">
      <table className="w-full text-sm min-w-[600px]">
        <thead className="sticky top-0 bg-slate-50 dark:bg-slate-800">
          <tr>
            {data.columns.map((col) => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                className="text-left px-3 py-2 text-xs font-semibold text-slate-500 dark:text-slate-400 cursor-pointer hover:text-slate-700 dark:hover:text-slate-200 select-none"
              >
                <span className="inline-flex items-center gap-1">
                  {col.label}
                  {sortKey === col.key && (
                    sortDir === "asc" ? <ChevronUp size={12} /> : <ChevronDown size={12} />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, i) => (
            <tr
              key={i}
              className={`border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50${onRowClick ? " cursor-pointer hover:bg-emerald-50 dark:hover:bg-emerald-950/20" : ""}`}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {data.columns.map((col) => (
                <td key={col.key} className="px-3 py-2 text-slate-700 dark:text-slate-300">
                  {formatCell(row[col.key], col.format)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
