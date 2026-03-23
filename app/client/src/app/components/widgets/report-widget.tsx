"use client";

import { ReportData } from "@/types/widgets";

interface ReportWidgetProps {
  data: ReportData;
}

/** Convert our markdown subset to HTML (h1-h3, bold, tables, lists, hr). */
function markdownToHtml(md: string): string {
  const lines = md.split("\n");
  const out: string[] = [];
  let inTable = false;
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Horizontal rule
    if (/^---+\s*$/.test(line)) {
      if (inTable) { out.push("</tbody></table>"); inTable = false; }
      if (inList) { out.push("</ol>"); inList = false; }
      out.push("<hr />");
      continue;
    }

    // Headers
    if (line.startsWith("### ")) {
      if (inTable) { out.push("</tbody></table>"); inTable = false; }
      if (inList) { out.push("</ol>"); inList = false; }
      out.push(`<h3>${inlineMd(line.slice(4))}</h3>`);
      continue;
    }
    if (line.startsWith("## ")) {
      if (inTable) { out.push("</tbody></table>"); inTable = false; }
      if (inList) { out.push("</ol>"); inList = false; }
      out.push(`<h2>${inlineMd(line.slice(3))}</h2>`);
      continue;
    }
    if (line.startsWith("# ")) {
      if (inTable) { out.push("</tbody></table>"); inTable = false; }
      if (inList) { out.push("</ol>"); inList = false; }
      out.push(`<h1>${inlineMd(line.slice(2))}</h1>`);
      continue;
    }

    // Table rows
    if (line.startsWith("|")) {
      // Skip separator rows (|---|---|)
      if (/^\|[\s\-:|]+\|$/.test(line)) continue;

      const cells = line.split("|").slice(1, -1).map((c) => c.trim());
      if (!inTable) {
        out.push('<table><thead><tr>');
        cells.forEach((c) => out.push(`<th>${inlineMd(c)}</th>`));
        out.push("</tr></thead><tbody>");
        inTable = true;
      } else {
        out.push("<tr>");
        cells.forEach((c) => out.push(`<td>${inlineMd(c)}</td>`));
        out.push("</tr>");
      }
      continue;
    }

    // Close table if line is not a table row
    if (inTable && !line.startsWith("|")) {
      out.push("</tbody></table>");
      inTable = false;
    }

    // Ordered list items
    if (/^\d+\.\s/.test(line)) {
      if (!inList) { out.push("<ol>"); inList = true; }
      out.push(`<li>${inlineMd(line.replace(/^\d+\.\s/, ""))}</li>`);
      continue;
    }

    // Unordered list items
    if (/^[-*]\s/.test(line)) {
      if (!inList) { out.push("<ul>"); inList = true; }
      out.push(`<li>${inlineMd(line.replace(/^[-*]\s/, ""))}</li>`);
      continue;
    }

    // Close list
    if (inList && !/^(\d+\.|[-*])\s/.test(line)) {
      out.push(inList ? "</ol>" : "</ul>");
      inList = false;
    }

    // Empty line or paragraph
    if (line.trim() === "") {
      out.push("");
      continue;
    }

    out.push(`<p>${inlineMd(line)}</p>`);
  }

  if (inTable) out.push("</tbody></table>");
  if (inList) out.push("</ol>");

  return out.join("\n");
}

/** Process inline markdown: bold, italic, code. */
function inlineMd(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
}

export function ReportWidget({ data }: ReportWidgetProps) {
  const { markdown, generated_at } = data;

  if (!markdown) {
    return (
      <p className="text-sm text-slate-400 text-center py-8">
        No report data available
      </p>
    );
  }

  const html = markdownToHtml(markdown);

  return (
    <div className="flex flex-col h-full">
      <div
        className="report-content overflow-y-auto max-h-[500px] pr-2 text-sm text-slate-700 dark:text-slate-300"
        dangerouslySetInnerHTML={{ __html: html }}
        style={{
          // Inline styles for report elements
        }}
      />
      {generated_at && (
        <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
          <p className="text-xs text-slate-400 dark:text-slate-500">
            Generated: {generated_at}
          </p>
        </div>
      )}
      <style jsx>{`
        .report-content h1 {
          font-size: 1.25rem;
          font-weight: 700;
          margin: 1rem 0 0.5rem;
          color: var(--heading-color, #0f172a);
        }
        .report-content h2 {
          font-size: 1.1rem;
          font-weight: 600;
          margin: 0.875rem 0 0.375rem;
          color: var(--heading-color, #0f172a);
        }
        .report-content h3 {
          font-size: 1rem;
          font-weight: 600;
          margin: 0.75rem 0 0.25rem;
          color: var(--heading-color, #0f172a);
        }
        .report-content table {
          width: 100%;
          border-collapse: collapse;
          margin: 0.5rem 0;
          font-size: 0.8125rem;
        }
        .report-content th {
          text-align: left;
          padding: 0.375rem 0.5rem;
          border-bottom: 2px solid #e2e8f0;
          font-weight: 600;
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.025em;
          color: #64748b;
        }
        .report-content td {
          padding: 0.3rem 0.5rem;
          border-bottom: 1px solid #f1f5f9;
        }
        .report-content tr:hover td {
          background-color: #f8fafc;
        }
        .report-content ol, .report-content ul {
          padding-left: 1.25rem;
          margin: 0.375rem 0;
        }
        .report-content li {
          margin: 0.25rem 0;
        }
        .report-content hr {
          border: none;
          border-top: 1px solid #e2e8f0;
          margin: 1rem 0;
        }
        .report-content p {
          margin: 0.25rem 0;
          line-height: 1.5;
        }
        .report-content strong {
          font-weight: 600;
        }
        .report-content code {
          background: #f1f5f9;
          padding: 0.125rem 0.25rem;
          border-radius: 0.25rem;
          font-size: 0.8125rem;
        }
        :global(.dark) .report-content h1,
        :global(.dark) .report-content h2,
        :global(.dark) .report-content h3 {
          color: #f1f5f9;
        }
        :global(.dark) .report-content th {
          border-bottom-color: #334155;
          color: #94a3b8;
        }
        :global(.dark) .report-content td {
          border-bottom-color: #1e293b;
        }
        :global(.dark) .report-content tr:hover td {
          background-color: #1e293b;
        }
        :global(.dark) .report-content hr {
          border-top-color: #334155;
        }
        :global(.dark) .report-content code {
          background: #1e293b;
        }
      `}</style>
    </div>
  );
}
