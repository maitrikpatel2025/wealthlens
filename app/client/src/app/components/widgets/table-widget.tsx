"use client";

import { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import { TableData, TableColumn } from "@/types/widgets";

interface TableWidgetProps {
  data: TableData;
}

function formatCell(value: string | number, format?: string): string {
  if (value === undefined || value === null) return "—";
  if (format === "currency") return `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (format === "percent") return `${Number(value).toFixed(2)}%`;
  if (format === "number") return Number(value).toLocaleString();
  return String(value);
}

export function TableWidget({ data: rawData }: TableWidgetProps) {
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
    <div className="overflow-auto max-h-[300px]">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-slate-50">
          <tr>
            {data.columns.map((col) => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                className="text-left px-3 py-2 text-xs font-semibold text-slate-500 cursor-pointer hover:text-slate-700 select-none"
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
            <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
              {data.columns.map((col) => (
                <td key={col.key} className="px-3 py-2 text-slate-700">
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
