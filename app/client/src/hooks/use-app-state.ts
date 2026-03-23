"use client";

import { useReducer, Dispatch } from "react";
import type { Conversation, UsageMeter } from "@/types/api";

export type LayoutMode = "split" | "dashboard" | "chat";

export interface AppState {
  showUpload: boolean;
  isDark: boolean;
  sidebarOpen: boolean;
  showSimulation: boolean;
  showSignInPrompt: boolean;
  layoutMode: LayoutMode;
  canvasPercent: number;
  conversations: Conversation[];
  usage: UsageMeter;
  conversationTitle: string | undefined;
}

export type AppAction =
  | { type: "SET_SHOW_UPLOAD"; payload: boolean }
  | { type: "SET_DARK"; payload: boolean }
  | { type: "TOGGLE_DARK" }
  | { type: "SET_SIDEBAR_OPEN"; payload: boolean }
  | { type: "TOGGLE_SIDEBAR" }
  | { type: "SET_SHOW_SIMULATION"; payload: boolean }
  | { type: "SET_SHOW_SIGN_IN_PROMPT"; payload: boolean }
  | { type: "SET_LAYOUT_MODE"; payload: LayoutMode }
  | { type: "SET_CANVAS_PERCENT"; payload: number }
  | { type: "SET_CONVERSATIONS"; payload: Conversation[] }
  | { type: "SET_USAGE"; payload: UsageMeter }
  | { type: "INCREMENT_USAGE" }
  | { type: "SET_CONVERSATION_TITLE"; payload: string | undefined }
  | { type: "NEW_CHAT" }
  | { type: "SELECT_CONVERSATION"; payload: string }
  | { type: "RESET" };

const initialState: AppState = {
  showUpload: false,
  isDark: false,
  sidebarOpen: false,
  showSimulation: false,
  showSignInPrompt: false,
  layoutMode: "split",
  canvasPercent: 60,
  conversations: [],
  usage: { used: 0, limit: 25 },
  conversationTitle: undefined,
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "SET_SHOW_UPLOAD":
      return { ...state, showUpload: action.payload };
    case "SET_DARK":
      return { ...state, isDark: action.payload };
    case "TOGGLE_DARK":
      return { ...state, isDark: !state.isDark };
    case "SET_SIDEBAR_OPEN":
      return { ...state, sidebarOpen: action.payload };
    case "TOGGLE_SIDEBAR":
      return { ...state, sidebarOpen: !state.sidebarOpen };
    case "SET_SHOW_SIMULATION":
      return { ...state, showSimulation: action.payload };
    case "SET_SHOW_SIGN_IN_PROMPT":
      return { ...state, showSignInPrompt: action.payload };
    case "SET_LAYOUT_MODE":
      return { ...state, layoutMode: action.payload };
    case "SET_CANVAS_PERCENT":
      return { ...state, canvasPercent: Math.max(30, Math.min(75, action.payload)) };
    case "SET_CONVERSATIONS":
      return { ...state, conversations: action.payload };
    case "SET_USAGE":
      return { ...state, usage: action.payload };
    case "INCREMENT_USAGE":
      return { ...state, usage: { ...state.usage, used: state.usage.used + 1 } };
    case "SET_CONVERSATION_TITLE":
      return { ...state, conversationTitle: action.payload };
    case "NEW_CHAT": {
      const newId = `conv_${Date.now()}`;
      return {
        ...state,
        conversations: [
          { id: newId, title: "New Analysis", timestamp: "Just now", isActive: true },
          ...state.conversations.map((c) => ({ ...c, isActive: false })),
        ],
        conversationTitle: undefined,
        sidebarOpen: false,
      };
    }
    case "SELECT_CONVERSATION":
      return {
        ...state,
        conversations: state.conversations.map((c) => ({
          ...c,
          isActive: c.id === action.payload,
        })),
        sidebarOpen: false,
      };
    case "RESET":
      return { ...initialState, isDark: state.isDark };
    default:
      return state;
  }
}

export function useAppState(darkFromStorage?: boolean): [AppState, Dispatch<AppAction>] {
  const init = { ...initialState, isDark: darkFromStorage ?? false };
  return useReducer(appReducer, init);
}
