"use client";

import { useState, useEffect } from "react";
import { X, Plus, Trash2, Play } from "lucide-react";

interface SimulationChange {
  id: string;
  action: "sell" | "buy" | "adjust_weight";
  symbol: string;
  amount: string;
  targetSymbol: string;
}

interface SimulationPanelProps {
  isOpen: boolean;
  households: any[];
  onClose: () => void;
  onRunSimulation: (prompt: string) => void;
}

/** Collect all unique symbols from households. */
function getHoldingSymbols(households: any[]): string[] {
  const symbols = new Set<string>();
  for (const h of households) {
    for (const acct of h.accounts ?? []) {
      for (const holding of acct.holdings ?? []) {
        if (holding.symbol) symbols.add(holding.symbol);
      }
    }
  }
  return Array.from(symbols).sort();
}

export function SimulationPanel({ isOpen, households, onClose, onRunSimulation }: SimulationPanelProps) {
  const [changes, setChanges] = useState<SimulationChange[]>([
    { id: "1", action: "sell", symbol: "", amount: "", targetSymbol: "" },
  ]);

  const symbols = getHoldingSymbols(households);

  // Reset state when panel opens
  useEffect(() => {
    if (isOpen) {
      setChanges([{ id: "1", action: "sell", symbol: "", amount: "", targetSymbol: "" }]);
    }
  }, [isOpen]);

  // Escape key to close
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  const addChange = () => {
    setChanges((prev) => [
      ...prev,
      { id: String(Date.now()), action: "sell", symbol: "", amount: "", targetSymbol: "" },
    ]);
  };

  const removeChange = (id: string) => {
    setChanges((prev) => prev.filter((c) => c.id !== id));
  };

  const updateChange = (id: string, field: keyof SimulationChange, value: string) => {
    setChanges((prev) =>
      prev.map((c) => (c.id === id ? { ...c, [field]: value } : c)),
    );
  };

  const handleRun = () => {
    const validChanges = changes.filter((c) => c.symbol && c.amount);
    if (validChanges.length === 0) return;

    const changeDescriptions = validChanges.map((c) => {
      if (c.action === "sell" && c.targetSymbol) {
        return `sell $${c.amount} of ${c.symbol} and buy ${c.targetSymbol}`;
      }
      if (c.action === "sell") return `sell $${c.amount} of ${c.symbol}`;
      if (c.action === "buy") return `buy $${c.amount} of ${c.symbol}`;
      return `adjust ${c.symbol} to ${c.amount}% weight`;
    });

    const prompt = `Simulate: ${changeDescriptions.join(", ")}. Show me before vs after comparison.`;
    onRunSimulation(prompt);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={onClose} />

      {/* Panel */}
      <aside className="fixed top-14 right-0 bottom-0 z-50 w-full sm:w-[380px] bg-white dark:bg-slate-950 border-l border-slate-200 dark:border-slate-800 flex flex-col shadow-xl animate-in slide-in-from-right">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800">
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">What-If Simulator</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400">
            <X size={16} />
          </button>
        </div>

        {/* Current holdings */}
        <div className="px-5 py-3 border-b border-slate-100 dark:border-slate-800/50">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Current Holdings</p>
          <div className="flex flex-wrap gap-1.5 max-h-20 overflow-auto">
            {symbols.map((s) => (
              <span key={s} className="px-2 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded text-slate-600 dark:text-slate-400">
                {s}
              </span>
            ))}
            {symbols.length === 0 && (
              <span className="text-xs text-slate-400">No holdings found</span>
            )}
          </div>
        </div>

        {/* Changes */}
        <div className="flex-1 overflow-auto px-5 py-4 space-y-4">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Hypothetical Changes</p>

          {changes.map((change) => (
            <div key={change.id} className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 space-y-2.5">
              <div className="flex items-center gap-2">
                <select
                  value={change.action}
                  onChange={(e) => updateChange(change.id, "action", e.target.value)}
                  className="flex-1 text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300"
                >
                  <option value="sell">Sell</option>
                  <option value="buy">Buy</option>
                  <option value="adjust_weight">Adjust Weight</option>
                </select>
                <button onClick={() => removeChange(change.id)} className="p-1 text-slate-400 hover:text-red-500">
                  <Trash2 size={14} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  placeholder="Symbol (e.g. VFV.TO)"
                  value={change.symbol}
                  onChange={(e) => updateChange(change.id, "symbol", e.target.value)}
                  list={`symbols-${change.id}`}
                  className="text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 placeholder:text-slate-400"
                />
                <datalist id={`symbols-${change.id}`}>
                  {symbols.map((s) => <option key={s} value={s} />)}
                </datalist>
                <input
                  type="text"
                  placeholder={change.action === "adjust_weight" ? "Target %" : "$ Amount"}
                  value={change.amount}
                  onChange={(e) => updateChange(change.id, "amount", e.target.value)}
                  className="text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 placeholder:text-slate-400"
                />
              </div>

              {change.action === "sell" && (
                <input
                  type="text"
                  placeholder="Reinvest into (optional symbol)"
                  value={change.targetSymbol}
                  onChange={(e) => updateChange(change.id, "targetSymbol", e.target.value)}
                  list={`target-symbols-${change.id}`}
                  className="w-full text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 placeholder:text-slate-400"
                />
              )}
              <datalist id={`target-symbols-${change.id}`}>
                {symbols.map((s) => <option key={s} value={s} />)}
              </datalist>
            </div>
          ))}

          <button
            onClick={addChange}
            className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 font-medium"
          >
            <Plus size={14} /> Add change
          </button>
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-slate-200 dark:border-slate-800">
          <button
            onClick={handleRun}
            disabled={!changes.some((c) => c.symbol && c.amount)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            <Play size={14} />
            Run Simulation
          </button>
          <p className="text-[10px] text-slate-400 text-center mt-2">
            Original portfolio data will not be modified.
          </p>
        </div>
      </aside>
    </>
  );
}
