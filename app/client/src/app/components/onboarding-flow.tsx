"use client";

import { useState } from "react";
import { Upload, BarChart3, Compass, X, Check } from "lucide-react";

interface OnboardingFlowProps {
  hasPortfolio: boolean;
  hasWidgets: boolean;
  onDismiss: () => void;
}

export function OnboardingFlow({ hasPortfolio, hasWidgets, onDismiss }: OnboardingFlowProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  const steps = [
    {
      label: "Upload Statement",
      icon: Upload,
      done: hasPortfolio,
      description: "Import a brokerage PDF",
    },
    {
      label: "First Analysis",
      icon: BarChart3,
      done: hasWidgets,
      description: "Ask about your portfolio",
    },
    {
      label: "Explore",
      icon: Compass,
      done: false,
      description: "Deep dive into insights",
    },
  ];

  const currentStep = steps.findIndex((s) => !s.done);

  return (
    <div className="relative mx-4 mb-4 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <button
        onClick={() => {
          setDismissed(true);
          onDismiss();
        }}
        className="absolute right-3 top-3 rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
      >
        <X size={14} />
      </button>

      <div className="flex items-center gap-4">
        {steps.map((step, i) => {
          const Icon = step.icon;
          const isCurrent = i === currentStep;

          return (
            <div key={step.label} className="flex flex-1 items-center gap-2">
              {/* Step circle */}
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-colors ${
                  step.done
                    ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400"
                    : isCurrent
                    ? "bg-emerald-500 text-white"
                    : "bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500"
                }`}
              >
                {step.done ? <Check size={14} /> : <Icon size={14} />}
              </div>

              {/* Step text */}
              <div className="min-w-0">
                <p
                  className={`text-xs font-semibold truncate ${
                    step.done || isCurrent
                      ? "text-slate-900 dark:text-slate-100"
                      : "text-slate-400 dark:text-slate-500"
                  }`}
                >
                  {step.label}
                </p>
                <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate">
                  {step.description}
                </p>
              </div>

              {/* Connector line */}
              {i < steps.length - 1 && (
                <div
                  className={`ml-auto h-px flex-1 ${
                    step.done ? "bg-emerald-300 dark:bg-emerald-700" : "bg-slate-200 dark:bg-slate-700"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
