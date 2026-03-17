"use client";

import { useState, useRef, useEffect } from "react";
import { Menu, Plus, Sun, Moon, Check, Pencil } from "lucide-react";

interface TopNavProps {
  conversationTitle?: string;
  isLoggedIn?: boolean;
  isDarkMode?: boolean;
  userName?: string;
  showSignIn?: boolean;
  onToggleSidebar?: () => void;
  onNewChat?: () => void;
  onToggleTheme?: () => void;
  onSignIn?: () => void;
  onTitleChange?: (title: string) => void;
  showHamburger?: boolean;
}

export function TopNav({
  conversationTitle,
  isLoggedIn = false,
  isDarkMode = false,
  userName,
  showSignIn = false,
  onToggleSidebar,
  onNewChat,
  onToggleTheme,
  onSignIn,
  onTitleChange,
  showHamburger = false,
}: TopNavProps) {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editValue, setEditValue] = useState(conversationTitle || "");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditingTitle && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditingTitle]);

  function handleTitleClick() {
    if (conversationTitle && onTitleChange) {
      setEditValue(conversationTitle);
      setIsEditingTitle(true);
    }
  }

  function handleTitleSubmit() {
    if (editValue.trim() && editValue !== conversationTitle) {
      onTitleChange?.(editValue.trim());
    }
    setIsEditingTitle(false);
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-14 border-b border-slate-200 bg-white/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/80">
      <div className="flex h-full items-center px-4">
        {/* Left: Hamburger + Logo */}
        <div className="flex items-center gap-3">
          {showHamburger && (
            <button
              onClick={onToggleSidebar}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              aria-label="Toggle sidebar"
            >
              <Menu className="h-5 w-5" />
            </button>
          )}
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-600 dark:bg-emerald-500">
              <span className="text-sm font-bold text-white">W</span>
            </div>
            <span className="text-base font-semibold text-slate-900 dark:text-slate-100">
              WealthLens
            </span>
          </div>
        </div>

        {/* Center: Conversation Title */}
        <div className="flex min-w-0 flex-1 items-center justify-center px-4">
          {conversationTitle &&
            (isEditingTitle ? (
              <div className="flex items-center gap-1.5">
                <input
                  ref={inputRef}
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={handleTitleSubmit}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleTitleSubmit();
                    if (e.key === "Escape") setIsEditingTitle(false);
                  }}
                  className="max-w-xs border-b border-emerald-500 bg-transparent px-1 text-center text-sm font-medium text-slate-900 outline-none dark:text-slate-100"
                />
                <button
                  onClick={handleTitleSubmit}
                  className="flex h-6 w-6 items-center justify-center rounded text-emerald-600 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950"
                >
                  <Check className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <button
                onClick={handleTitleClick}
                className="group flex max-w-xs items-center gap-1.5 truncate rounded-md px-2 py-1 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <span className="truncate text-sm font-medium text-slate-700 dark:text-slate-300">
                  {conversationTitle}
                </span>
                {onTitleChange && (
                  <Pencil className="h-3 w-3 shrink-0 text-slate-400 opacity-0 transition-opacity group-hover:opacity-100" />
                )}
              </button>
            ))}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={onToggleTheme}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
            aria-label={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
          >
            {isDarkMode ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>

          <button
            onClick={onNewChat}
            className="ml-1 hidden h-8 items-center gap-1.5 rounded-lg border border-slate-200 px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 sm:flex dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New chat</span>
          </button>

          {/* User Avatar / Sign In */}
          <div className="ml-2">
            {showSignIn ? (
              <button
                onClick={onSignIn}
                className="flex h-8 items-center rounded-full bg-emerald-600 px-4 text-sm font-medium text-white transition-colors hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600"
              >
                Sign in
              </button>
            ) : (
              <button
                className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-slate-200 transition-colors hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600"
                aria-label={isLoggedIn ? userName || "User menu" : "Account"}
              >
                <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
                  {isLoggedIn && userName
                    ? userName.charAt(0).toUpperCase()
                    : "?"}
                </span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
