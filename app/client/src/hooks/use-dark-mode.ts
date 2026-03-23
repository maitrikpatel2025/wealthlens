"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "wealthlens-dark-mode";

export function useDarkMode(): [boolean, (v: boolean) => void] {
  const [isDark, setIsDark] = useState(false);

  // Initialize from localStorage or system preference
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored !== null) {
      setIsDark(stored === "true");
    } else {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      setIsDark(mq.matches);
    }
  }, []);

  // Listen for system preference changes
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => {
      // Only follow system if no explicit user preference
      if (localStorage.getItem(STORAGE_KEY) === null) {
        setIsDark(e.matches);
      }
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  // Apply class and persist
  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
    localStorage.setItem(STORAGE_KEY, String(isDark));
  }, [isDark]);

  return [isDark, setIsDark];
}
