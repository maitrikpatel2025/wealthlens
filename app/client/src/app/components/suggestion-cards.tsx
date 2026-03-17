"use client";

import { Upload, HelpCircle, DollarSign, LayoutDashboard } from "lucide-react";

interface SuggestionCard {
  icon: React.ReactNode;
  title: string;
  description: string;
  prompt: string;
}

const suggestions: SuggestionCard[] = [
  {
    icon: <Upload size={20} />,
    title: "Upload statement",
    description: "Import a brokerage PDF to get started",
    prompt: "I'd like to upload a brokerage statement",
  },
  {
    icon: <HelpCircle size={20} />,
    title: "Account types?",
    description: "Learn about RRSP, TFSA, RESP, and more",
    prompt: "Explain the different Canadian registered account types and their tax implications",
  },
  {
    icon: <DollarSign size={20} />,
    title: "Analyze fees?",
    description: "Understand MERs and hidden costs",
    prompt: "How can I analyze the fees in my investment portfolio?",
  },
  {
    icon: <LayoutDashboard size={20} />,
    title: "Example dashboard",
    description: "See a sample portfolio analysis",
    prompt: "Show me an example dashboard with sample portfolio data",
  },
];

interface SuggestionCardsProps {
  onSelect: (prompt: string) => void;
  onUploadClick: () => void;
}

export function SuggestionCards({ onSelect, onUploadClick }: SuggestionCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-4 max-w-lg">
      {suggestions.map((card) => (
        <button
          key={card.title}
          onClick={() => card.title === "Upload statement" ? onUploadClick() : onSelect(card.prompt)}
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
