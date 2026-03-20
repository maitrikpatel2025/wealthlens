"use client";

import { X } from "lucide-react";

interface SignInPromptProps {
  onSignIn: () => void;
  onClose: () => void;
}

export function SignInPrompt({ onSignIn, onClose }: SignInPromptProps) {
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative mx-4 w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 shadow-2xl dark:border-slate-700 dark:bg-slate-900">
        <button
          onClick={onClose}
          className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-900/40">
            <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">W</span>
          </div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            You&apos;ve used 25 free messages
          </h2>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Sign in to continue using WealthLens with unlimited messages and saved portfolios.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <button
            onClick={onSignIn}
            className="flex h-11 w-full items-center justify-center rounded-xl bg-emerald-600 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600"
          >
            Sign in
          </button>
          <button
            onClick={onSignIn}
            className="flex h-11 w-full items-center justify-center rounded-xl border border-slate-200 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Create an account
          </button>
        </div>
      </div>
    </div>
  );
}
