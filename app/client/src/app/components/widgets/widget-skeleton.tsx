"use client";

export function WidgetSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      {/* Title bar */}
      <div className="mb-4 flex items-center justify-between">
        <div className="h-4 w-32 rounded bg-slate-200 dark:bg-slate-700" />
        <div className="h-4 w-16 rounded bg-slate-200 dark:bg-slate-700" />
      </div>
      {/* Chart area */}
      <div className="space-y-3">
        <div className="h-3 w-full rounded bg-slate-200 dark:bg-slate-700" />
        <div className="h-3 w-5/6 rounded bg-slate-200 dark:bg-slate-700" />
        <div className="h-3 w-4/6 rounded bg-slate-200 dark:bg-slate-700" />
        <div className="h-24 w-full rounded bg-slate-100 dark:bg-slate-800" />
      </div>
    </div>
  );
}

export function DashboardSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-2">
      {Array.from({ length: count }).map((_, i) => (
        <WidgetSkeleton key={i} />
      ))}
    </div>
  );
}
