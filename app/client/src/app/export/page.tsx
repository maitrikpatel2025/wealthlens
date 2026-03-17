"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ExportView } from "../components/export-view";
import { WidgetSpec } from "@/types/widgets";
import { Printer, ArrowLeft } from "lucide-react";

function ExportContent() {
  const searchParams = useSearchParams();
  const [widgets, setWidgets] = useState<WidgetSpec[]>([]);

  useEffect(() => {
    // Read widgets from sessionStorage (set by dashboard before navigating)
    const stored = sessionStorage.getItem("wealthlens_export_widgets");
    if (stored) {
      try {
        setWidgets(JSON.parse(stored));
      } catch {
        // ignore parse errors
      }
    }
  }, []);

  const handlePrint = () => {
    window.print();
  };

  if (!widgets.length) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-500 mb-4">No widgets to export.</p>
          <a href="/" className="text-emerald-600 hover:text-emerald-700 font-medium">
            Return to dashboard
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-8">
      {/* Print controls (hidden in print) */}
      <div className="flex items-center gap-3 mb-6 print-hidden">
        <a
          href="/"
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
        >
          <ArrowLeft size={16} />
          Back to dashboard
        </a>
        <div className="flex-1" />
        <button
          onClick={handlePrint}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"
        >
          <Printer size={16} />
          Print / Save PDF
        </button>
      </div>

      <ExportView widgets={widgets} />
    </div>
  );
}

export default function ExportPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-white flex items-center justify-center"><p className="text-slate-500">Loading...</p></div>}>
      <ExportContent />
    </Suspense>
  );
}
