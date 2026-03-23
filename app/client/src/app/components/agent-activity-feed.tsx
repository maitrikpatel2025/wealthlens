"use client";

import { Loader2, Check, Shield, DollarSign, TrendingUp, BarChart3, Sparkles, Users } from "lucide-react";

interface AgentActivity {
  id: string;
  agent: string;
  status: string;
  message: string;
  tool?: string;
  started_at?: number;
  completed_at?: number;
}

interface AgentActivityFeedProps {
  activities: AgentActivity[];
}

const AGENT_CONFIG: Record<string, { icon: typeof Shield; color: string; label: string }> = {
  supervisor: { icon: Sparkles, color: "text-purple-500", label: "Supervisor" },
  risk_analyst: { icon: Shield, color: "text-red-500", label: "Risk Analyst" },
  fee_optimizer: { icon: DollarSign, color: "text-amber-500", label: "Fee Optimizer" },
  income_analyst: { icon: TrendingUp, color: "text-green-500", label: "Income Analyst" },
  macro_strategist: { icon: BarChart3, color: "text-blue-500", label: "Macro Strategist" },
  synthesizer: { icon: Sparkles, color: "text-indigo-500", label: "Synthesizer" },
  persona: { icon: Users, color: "text-violet-500", label: "Persona" },
};

export function AgentActivityFeed({ activities }: AgentActivityFeedProps) {
  if (!activities || activities.length === 0) return null;

  // Deduplicate by id, keep last occurrence
  const seen = new Map<string, AgentActivity>();
  for (const a of activities) {
    seen.set(a.id, a);
  }
  const dedupedActivities = Array.from(seen.values());

  return (
    <div className="flex flex-col gap-1.5 p-2">
      {dedupedActivities.map((activity) => {
        const config = AGENT_CONFIG[activity.agent] || AGENT_CONFIG.supervisor;
        const Icon = config.icon;
        const isActive = activity.status === "active";

        return (
          <div
            key={activity.id}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 border text-sm transition-all ${
              isActive
                ? "bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-700 animate-pulse"
                : "bg-white dark:bg-slate-900/30 border-slate-100 dark:border-slate-800"
            }`}
          >
            {/* Status indicator */}
            {isActive ? (
              <Loader2 size={14} className={`animate-spin ${config.color}`} />
            ) : (
              <Check size={14} className="text-emerald-500" />
            )}

            {/* Agent icon */}
            <Icon size={14} className={config.color} />

            {/* Content */}
            <div className="flex-1 min-w-0">
              <span className={`text-xs font-semibold ${config.color}`}>
                {config.label}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400 ml-1.5">
                {activity.message}
              </span>
              {activity.tool && isActive && (
                <span className="ml-1.5 text-xs text-slate-400 dark:text-slate-500">
                  ({activity.tool})
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
