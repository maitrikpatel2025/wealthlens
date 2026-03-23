"use client";

import { useMemo } from "react";
import { Upload, LayoutDashboard, AlertTriangle, Globe, DollarSign, ShieldCheck, TrendingUp, BarChart3, FlaskConical } from "lucide-react";
import type { WidgetSpec } from "@/types/widgets";

interface SmartSuggestion {
  icon: React.ReactNode;
  title: string;
  description: string;
  prompt: string;
}

interface SmartSuggestionCardsProps {
  households: any[];
  widgets: WidgetSpec[];
  onSelect: (prompt: string) => void;
  onUploadClick: () => void;
}

/** Derive portfolio stats from raw household data. */
function computePortfolioStats(households: any[]) {
  let totalValue = 0;
  let totalFees = 0;
  let totalIncome = 0;
  let canadaValue = 0;
  let holdingCount = 0;
  let maxMer = 0;
  let maxMerName = "";

  for (const h of households) {
    for (const acct of h.accounts ?? []) {
      for (const holding of acct.holdings ?? []) {
        const val = holding.market_value ?? 0;
        const mer = holding.mer ?? 0;
        const dy = holding.dividend_yield ?? 0;
        totalValue += val;
        totalFees += val * mer / 100;
        totalIncome += val * dy / 100;
        holdingCount++;

        const geo = (holding.geographic_exposure ?? holding.country ?? "").toLowerCase();
        if (geo.includes("canada") || geo === "ca") {
          canadaValue += val;
        }

        if (mer > maxMer) {
          maxMer = mer;
          maxMerName = holding.symbol || holding.name || "a holding";
        }
      }
    }
  }

  const weightedMer = totalValue > 0 ? (totalFees / totalValue) * 100 : 0;
  const weightedYield = totalValue > 0 ? (totalIncome / totalValue) * 100 : 0;
  const canadaPct = totalValue > 0 ? (canadaValue / totalValue) * 100 : 0;

  return { totalValue, weightedMer, weightedYield, canadaPct, holdingCount, maxMer, maxMerName, totalFees, totalIncome };
}

/** Static suggestions shown when no data is loaded. */
const STATIC_SUGGESTIONS: SmartSuggestion[] = [
  {
    icon: <Upload size={20} />,
    title: "Upload statement",
    description: "Import a brokerage PDF to get started",
    prompt: "__upload__",
  },
  {
    icon: <LayoutDashboard size={20} />,
    title: "Example dashboard",
    description: "See a sample portfolio analysis",
    prompt: "Show me an example dashboard with sample portfolio data",
  },
];

export function SmartSuggestionCards({ households, widgets, onSelect, onUploadClick }: SmartSuggestionCardsProps) {
  const hasData = households && households.length > 0;

  const suggestions = useMemo<SmartSuggestion[]>(() => {
    if (!hasData) return STATIC_SUGGESTIONS;

    const stats = computePortfolioStats(households);
    const cards: SmartSuggestion[] = [];

    // High MER warning
    if (stats.weightedMer > 0.5) {
      cards.push({
        icon: <AlertTriangle size={20} />,
        title: `MER: ${stats.weightedMer.toFixed(2)}%`,
        description: `Paying $${stats.totalFees.toFixed(0)}/yr in fees — see low-cost alternatives`,
        prompt: "Analyze my portfolio fees and show me lower-cost ETF alternatives to reduce my MER.",
      });
    }

    // Home bias alert
    if (stats.canadaPct > 40) {
      cards.push({
        icon: <Globe size={20} />,
        title: `${stats.canadaPct.toFixed(0)}% Canadian`,
        description: "Possible home bias — check geographic diversification",
        prompt: "Show my geographic exposure breakdown. Do I have a home bias toward Canada?",
      });
    }

    // Yield info
    if (stats.weightedYield > 0) {
      cards.push({
        icon: <DollarSign size={20} />,
        title: `Yield: ${stats.weightedYield.toFixed(2)}%`,
        description: `Est. $${stats.totalIncome.toFixed(0)}/yr income — see tax implications`,
        prompt: "Analyze my portfolio income and dividend yield, including tax implications by account type.",
      });
    }

    // Stress test
    cards.push({
      icon: <FlaskConical size={20} />,
      title: "Stress test",
      description: "Simulate bear market, recession, or rate hike",
      prompt: "Stress test my portfolio with a bear market scenario at moderate severity.",
    });

    // Risk checkup
    cards.push({
      icon: <ShieldCheck size={20} />,
      title: "Risk checkup",
      description: "Check beta, concentration, and sector risk",
      prompt: "Run a full risk assessment on my portfolio including beta, concentration, and sector analysis.",
    });

    // Performance
    cards.push({
      icon: <TrendingUp size={20} />,
      title: "Performance check",
      description: "Compare returns vs benchmark",
      prompt: "Compare my portfolio performance against a benchmark over the last year.",
    });

    // Goal alignment
    cards.push({
      icon: <BarChart3 size={20} />,
      title: "Goal alignment",
      description: "Check if your portfolio fits your goals",
      prompt: "Am I on track for retirement? Score my portfolio against a balanced retirement goal.",
    });

    return cards.slice(0, 4);
  }, [hasData, households]);

  return (
    <div className="grid grid-cols-2 gap-3 max-w-lg">
      {suggestions.map((card) => (
        <button
          key={card.title}
          onClick={() => card.prompt === "__upload__" ? onUploadClick() : onSelect(card.prompt)}
          className="flex flex-col items-start gap-2 p-4 rounded-xl border border-slate-200 bg-white hover:border-emerald-300 hover:shadow-md transition-all text-left group dark:border-slate-700 dark:bg-slate-900 dark:hover:border-emerald-600"
        >
          <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 group-hover:bg-emerald-100 transition-colors dark:bg-emerald-950/40 dark:text-emerald-400 dark:group-hover:bg-emerald-900/40">
            {card.icon}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{card.title}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{card.description}</p>
          </div>
        </button>
      ))}
    </div>
  );
}
