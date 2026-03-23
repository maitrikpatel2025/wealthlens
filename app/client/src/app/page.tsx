"use client";

import { useRef, useCallback, useEffect } from "react";
import {
  useCoAgent,
  useCoAgentStateRender,
  useCopilotAction,
  useCopilotChat,
} from "@copilotkit/react-core";
import { GripVertical, LayoutDashboard, Columns, MessageSquare } from "lucide-react";
import { TopNav } from "./components/top-nav";
import { SideNav } from "./components/side-nav";
import type { Conversation } from "@/types/api";
import { ChatPanel } from "./components/chat-panel";
import { DashboardCanvas } from "./components/dashboard-canvas";
import { AgentActivityFeed } from "./components/agent-activity-feed";
import { ToolLogs } from "./components/tool-logs";
import { PdfUpload } from "./components/pdf-upload";
import { SimulationPanel } from "./components/simulation-panel";
import { SignInPrompt } from "./components/sign-in-prompt";
import { WidgetSpec } from "@/types/widgets";
import { composeWidgetQuestion, composeDataPointQuestion } from "@/utils/compose-question";
import { TextMessage, Role } from "@copilotkit/runtime-client-gql";
import { useAuth } from "@/hooks/use-auth";
import { useAppState } from "@/hooks/use-app-state";
import { useDarkMode } from "@/hooks/use-dark-mode";
import { useBreakpoint, isMobile, isTablet } from "@/hooks/use-breakpoint";
import { useRouter } from "next/navigation";

export default function WealthLensApp() {
  // Auth
  const { user, session, isLoading: authLoading, signOut } = useAuth();
  const router = useRouter();
  const isLoggedIn = !!user;
  const userName = user?.user_metadata?.full_name || user?.email?.split("@")[0];

  // Dark mode with persistence
  const [isDark, setIsDark] = useDarkMode();

  // Responsive breakpoint
  const breakpoint = useBreakpoint();
  const mobile = isMobile(breakpoint);
  const tablet = isTablet(breakpoint);

  // App state via useReducer
  const [appState, dispatch] = useAppState(isDark);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const chatInputRef = useRef<HTMLInputElement>(null);

  // CopilotKit agent state
  const { state, setState } = useCoAgent({
    name: "wealthlens",
    initialState: {
      widgets: [] as WidgetSpec[],
      tool_logs: [],
      households: [],
      user_profile: {},
      agent_activities: [],
      analysis_mode: "quick",
      active_specialists: [],
      specialist_results: {},
      persona_results: [],
    },
  });

  // Render agent activity feed (prefer agent_activities over tool_logs)
  useCoAgentStateRender({
    name: "wealthlens",
    render: ({ state }) => {
      const activities = state.agent_activities;
      if (activities && activities.length > 0) {
        return <AgentActivityFeed activities={activities} />;
      }
      return <ToolLogs logs={state.tool_logs} />;
    },
  });

  useCopilotAction({
    name: "update_dashboard_widgets",
    description: "Update the dashboard with new or modified widgets",
    parameters: [
      {
        name: "widgets",
        type: "object[]",
        description: "Array of widget specifications to display",
      },
    ],
    handler: async ({ widgets: newWidgets }) => {
      if (newWidgets && Array.isArray(newWidgets)) {
        setState((prev: any) => ({ ...prev, widgets: newWidgets }));
      }
    },
  });

  // Load persisted portfolios on login
  useEffect(() => {
    if (!user || !session) return;
    async function loadUserData() {
      try {
        const res = await fetch("/api/portfolios");
        const data = await res.json();
        if (data.households && data.households.length > 0) {
          setState((prev: any) => ({ ...prev, households: data.households }));
        }
      } catch (e) {
        console.error("Failed to load portfolios:", e);
      }
    }
    loadUserData();
    dispatch({
      type: "SET_CONVERSATIONS",
      payload: [{ id: "conv_01", title: "New Analysis", timestamp: "Just now", isActive: true }],
    });
  }, [user, session]);

  const { appendMessage } = useCopilotChat() as any;
  const sendMessage = useCallback(
    async (msg: { id?: string; role: string; content: string }) => {
      const textMsg = new TextMessage({
        id: msg.id || `msg-${Date.now()}`,
        role: msg.role === "user" ? Role.User : Role.Assistant,
        content: msg.content,
      });
      await appendMessage(textMsg);
    },
    [appendMessage]
  );

  // ── Handlers ──────────────────────────────────────────────────────────

  const handleToggleTheme = useCallback(() => {
    setIsDark(!isDark);
  }, [isDark, setIsDark]);

  const handleSignIn = useCallback(() => {
    router.push("/auth/login");
  }, [router]);

  const handleSignOut = useCallback(async () => {
    await signOut();
    setState((prev: any) => ({ ...prev, widgets: [], households: [], user_profile: {} }));
    dispatch({ type: "RESET" });
  }, [signOut, setState, dispatch]);

  const handleNewChat = useCallback(() => {
    dispatch({ type: "NEW_CHAT" });
  }, [dispatch]);

  const handleSelectConversation = useCallback(
    (id: string) => {
      dispatch({ type: "SELECT_CONVERSATION", payload: id });
    },
    [dispatch]
  );

  const checkUsageGate = useCallback((): boolean => {
    if (!isLoggedIn && appState.usage.used >= appState.usage.limit) {
      dispatch({ type: "SET_SHOW_SIGN_IN_PROMPT", payload: true });
      return false;
    }
    return true;
  }, [isLoggedIn, appState.usage, dispatch]);

  const handleSuggestionSelect = useCallback(
    async (prompt: string) => {
      if (!checkUsageGate()) return;
      dispatch({ type: "INCREMENT_USAGE" });
      dispatch({
        type: "SET_CONVERSATION_TITLE",
        payload: prompt.slice(0, 40) + (prompt.length > 40 ? "..." : ""),
      });
      await sendMessage({ id: `suggestion-${Date.now()}`, role: "user", content: prompt });
    },
    [checkUsageGate, sendMessage, dispatch]
  );

  const handleUploadClick = useCallback(() => {
    if (!checkUsageGate()) return;
    dispatch({ type: "SET_SHOW_UPLOAD", payload: true });
  }, [checkUsageGate, dispatch]);

  const handleRemoveWidget = useCallback(
    (widgetId: string) => {
      setState((prev: any) => ({
        ...prev,
        widgets: (prev.widgets || []).filter((w: WidgetSpec) => w.id !== widgetId),
      }));
    },
    [setState]
  );

  const handleAskAboutWidget = useCallback(
    (widget: WidgetSpec) => {
      const question = composeWidgetQuestion(widget);
      if (!checkUsageGate()) return;
      dispatch({ type: "INCREMENT_USAGE" });
      dispatch({
        type: "SET_CONVERSATION_TITLE",
        payload: question.slice(0, 40) + (question.length > 40 ? "..." : ""),
      });
      sendMessage({ id: `widget-${Date.now()}`, role: "user", content: question });
    },
    [checkUsageGate, sendMessage, dispatch]
  );

  const handleDataPointClick = useCallback(
    (widget: WidgetSpec, dataPoint: Record<string, any>) => {
      const question = composeDataPointQuestion(widget, dataPoint);
      if (!checkUsageGate()) return;
      dispatch({ type: "INCREMENT_USAGE" });
      dispatch({
        type: "SET_CONVERSATION_TITLE",
        payload: question.slice(0, 40) + (question.length > 40 ? "..." : ""),
      });
      sendMessage({ id: `drill-${Date.now()}`, role: "user", content: question });
    },
    [checkUsageGate, sendMessage, dispatch]
  );

  const handleRunSimulation = useCallback(
    async (prompt: string) => {
      dispatch({ type: "SET_SHOW_SIMULATION", payload: false });
      if (!checkUsageGate()) return;
      dispatch({ type: "INCREMENT_USAGE" });
      dispatch({ type: "SET_CONVERSATION_TITLE", payload: "Simulation" });
      await sendMessage({ id: `sim-${Date.now()}`, role: "user", content: prompt });
    },
    [checkUsageGate, sendMessage, dispatch]
  );

  const handleUploadComplete = useCallback(
    (result: any) => {
      dispatch({ type: "SET_SHOW_UPLOAD", payload: false });
      if (result && result.accounts) {
        setState((prev: any) => {
          const existingHouseholds = prev.households || [];
          const newHousehold = {
            id: result.household_id || `h-${Date.now()}`,
            institution: result.institution,
            accounts: result.accounts,
            confidence: result.confidence,
            extracted_at: new Date().toISOString(),
          };
          return {
            ...prev,
            households: [...existingHouseholds, newHousehold],
            widgets: result.widgets || prev.widgets || [],
          };
        });
      }
    },
    [setState, dispatch]
  );

  const handleLayoutChange = useCallback(
    (mode: "split" | "dashboard" | "chat") => {
      dispatch({ type: "SET_LAYOUT_MODE", payload: mode });
    },
    [dispatch]
  );

  // ── Resizable divider with Pointer Events (touch + mouse) ────────────

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      isDragging.current = true;
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    },
    []
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!isDragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const pct = ((e.clientX - rect.left) / rect.width) * 100;
      dispatch({ type: "SET_CANVAS_PERCENT", payload: pct });
    },
    [dispatch]
  );

  const handlePointerUp = useCallback(() => {
    isDragging.current = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }, []);

  // ── Keyboard shortcuts ────────────────────────────────────────────────

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;
      if (mod && e.key === "k") {
        e.preventDefault();
        chatInputRef.current?.focus();
        // Also try CopilotChat input
        const chatInput = document.querySelector(
          ".copilotKitInput textarea, .copilotKitInput input"
        ) as HTMLElement;
        chatInput?.focus();
      }
      if (mod && e.key === "b") {
        e.preventDefault();
        dispatch({ type: "TOGGLE_SIDEBAR" });
      }
      if (mod && e.key === "u") {
        e.preventDefault();
        handleUploadClick();
      }
      if (e.key === "Escape") {
        dispatch({ type: "SET_SHOW_UPLOAD", payload: false });
        dispatch({ type: "SET_SHOW_SIMULATION", payload: false });
        dispatch({ type: "SET_SHOW_SIGN_IN_PROMPT", payload: false });
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [dispatch, handleUploadClick]);

  // ── Derived state ─────────────────────────────────────────────────────

  const hasWidgets = (state?.widgets ?? []).length > 0;
  const activeConversation = appState.conversations.find((c) => c.isActive);
  const layoutMode = appState.layoutMode;

  // On mobile, force tab-based layout
  const effectiveLayout = mobile ? layoutMode : hasWidgets ? layoutMode : "chat";

  // Mobile tab state: show dashboard or chat
  const [mobileTab, setMobileTab] = [
    mobile && layoutMode === "dashboard" ? "dashboard" : mobile && layoutMode === "chat" ? "chat" : "split",
    (tab: string) => dispatch({ type: "SET_LAYOUT_MODE", payload: tab as any }),
  ];

  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white dark:bg-slate-950">
        <div className="flex items-center gap-2 text-slate-500">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
          <span className="text-sm">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-white dark:bg-slate-950">
      {/* Top Navigation */}
      <TopNav
        conversationTitle={appState.conversationTitle || activeConversation?.title}
        isLoggedIn={isLoggedIn}
        isDarkMode={isDark}
        userName={userName}
        showSignIn={!isLoggedIn}
        onToggleSidebar={() => dispatch({ type: "TOGGLE_SIDEBAR" })}
        onNewChat={handleNewChat}
        onToggleTheme={handleToggleTheme}
        onSignIn={handleSignIn}
        onSignOut={handleSignOut}
        onTitleChange={(t) => dispatch({ type: "SET_CONVERSATION_TITLE", payload: t })}
        showHamburger={isLoggedIn}
      />

      {/* Side Navigation */}
      {isLoggedIn && (
        <SideNav
          isOpen={appState.sidebarOpen}
          conversations={appState.conversations}
          usage={appState.usage}
          onClose={() => dispatch({ type: "SET_SIDEBAR_OPEN", payload: false })}
          onNewChat={() => {
            handleNewChat();
            dispatch({ type: "SET_SIDEBAR_OPEN", payload: false });
          }}
          onUploadStatement={() => {
            handleUploadClick();
            dispatch({ type: "SET_SIDEBAR_OPEN", payload: false });
          }}
          onSelectConversation={handleSelectConversation}
        />
      )}

      {/* Mobile tab bar */}
      {mobile && hasWidgets && (
        <div className="flex border-b border-slate-200 bg-white pt-14 dark:border-slate-800 dark:bg-slate-950">
          <button
            onClick={() => dispatch({ type: "SET_LAYOUT_MODE", payload: "dashboard" })}
            className={`flex flex-1 items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
              layoutMode === "dashboard"
                ? "border-b-2 border-emerald-500 text-emerald-600 dark:text-emerald-400"
                : "text-slate-500 dark:text-slate-400"
            }`}
          >
            <LayoutDashboard size={16} />
            Dashboard
          </button>
          <button
            onClick={() => dispatch({ type: "SET_LAYOUT_MODE", payload: "chat" })}
            className={`flex flex-1 items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
              layoutMode === "chat"
                ? "border-b-2 border-emerald-500 text-emerald-600 dark:text-emerald-400"
                : "text-slate-500 dark:text-slate-400"
            }`}
          >
            <MessageSquare size={16} />
            Chat
          </button>
        </div>
      )}

      {/* Main content area */}
      <main
        className={`flex-1 overflow-hidden ${mobile && hasWidgets ? "" : "pt-14"} transition-all duration-200 ${
          isLoggedIn && appState.sidebarOpen ? "lg:pl-[280px]" : ""
        }`}
      >
        {!hasWidgets ? (
          /* ── Chat-centered layout (no widgets yet) ── */
          <div className="flex h-full justify-center bg-white dark:bg-slate-950">
            <div className="flex h-full w-full max-w-[720px] flex-col px-4 sm:px-0">
              <ChatPanel
                onUploadComplete={handleUploadComplete}
                showWelcome
                onUploadClick={handleUploadClick}
              />
            </div>
          </div>
        ) : mobile ? (
          /* ── Mobile: tab-based layout ── */
          <div className="h-full">
            {layoutMode === "dashboard" ? (
              <DashboardCanvas
                widgets={state?.widgets ?? []}
                households={state?.households ?? []}
                onSuggestionSelect={handleSuggestionSelect}
                onUploadClick={handleUploadClick}
                onRemoveWidget={handleRemoveWidget}
                onAskAboutWidget={handleAskAboutWidget}
                onDataPointClick={handleDataPointClick}
                onSimulateClick={
                  (state?.households ?? []).length > 0
                    ? () => dispatch({ type: "SET_SHOW_SIMULATION", payload: true })
                    : undefined
                }
                layoutMode={layoutMode}
                onLayoutChange={handleLayoutChange}
              />
            ) : (
              <ChatPanel onUploadComplete={handleUploadComplete} />
            )}
          </div>
        ) : layoutMode === "dashboard" ? (
          /* ── Desktop: Dashboard only ── */
          <div className="h-full">
            <DashboardCanvas
              widgets={state?.widgets ?? []}
              households={state?.households ?? []}
              onSuggestionSelect={handleSuggestionSelect}
              onUploadClick={handleUploadClick}
              onRemoveWidget={handleRemoveWidget}
              onAskAboutWidget={handleAskAboutWidget}
              onDataPointClick={handleDataPointClick}
              onSimulateClick={
                (state?.households ?? []).length > 0
                  ? () => dispatch({ type: "SET_SHOW_SIMULATION", payload: true })
                  : undefined
              }
              layoutMode={layoutMode}
              onLayoutChange={handleLayoutChange}
            />
          </div>
        ) : layoutMode === "chat" ? (
          /* ── Desktop: Chat only ── */
          <div className="flex h-full flex-col bg-white dark:bg-slate-950">
            {/* Layout switcher bar */}
            <div className="flex items-center justify-center gap-1 border-b border-slate-200 bg-slate-50/90 px-4 py-2 dark:border-slate-800 dark:bg-slate-950/90">
              {([
                { mode: "dashboard" as const, icon: LayoutDashboard, label: "Dashboard" },
                { mode: "split" as const, icon: Columns, label: "Split" },
                { mode: "chat" as const, icon: MessageSquare, label: "Chat" },
              ]).map(({ mode, icon: Icon, label }) => (
                <button
                  key={mode}
                  onClick={() => handleLayoutChange(mode)}
                  className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${
                    layoutMode === mode
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400"
                      : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                  }`}
                >
                  <Icon size={13} />
                  {label}
                </button>
              ))}
            </div>
            <div className="flex flex-1 justify-center overflow-hidden">
              <div className="flex h-full w-full max-w-[720px] flex-col">
                <ChatPanel onUploadComplete={handleUploadComplete} />
              </div>
            </div>
          </div>
        ) : (
          /* ── Split layout: canvas | divider | chat ── */
          <div ref={containerRef} className="flex h-full bg-slate-50 dark:bg-slate-950">
            {/* Left: Dashboard Canvas */}
            <div
              className="canvas-animate-in h-full shrink-0 flex-col flex"
              style={{ width: `${appState.canvasPercent}%` }}
            >
              <DashboardCanvas
                widgets={state?.widgets ?? []}
                households={state?.households ?? []}
                onSuggestionSelect={handleSuggestionSelect}
                onUploadClick={handleUploadClick}
                onRemoveWidget={handleRemoveWidget}
                onAskAboutWidget={handleAskAboutWidget}
                onDataPointClick={handleDataPointClick}
                onSimulateClick={
                  (state?.households ?? []).length > 0
                    ? () => dispatch({ type: "SET_SHOW_SIMULATION", payload: true })
                    : undefined
                }
                layoutMode={layoutMode}
                onLayoutChange={handleLayoutChange}
              />
            </div>

            {/* Resizable divider with Pointer Events for touch support */}
            <div
              className="group relative flex h-full w-3 shrink-0 cursor-col-resize touch-none items-center justify-center hover:bg-slate-100 dark:hover:bg-slate-800"
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
            >
              <div className="flex h-8 w-1 items-center justify-center rounded-full bg-slate-300 transition-colors group-hover:bg-emerald-400 dark:bg-slate-600 dark:group-hover:bg-emerald-500">
                <GripVertical className="h-3 w-3 text-slate-500 opacity-0 transition-opacity group-hover:opacity-100 dark:text-slate-400" />
              </div>
            </div>

            {/* Right: Chat Panel */}
            <div className="h-full min-w-0 flex-1 border-l border-slate-200 dark:border-slate-800">
              <ChatPanel onUploadComplete={handleUploadComplete} />
            </div>
          </div>
        )}
      </main>

      {/* Upload modal */}
      {appState.showUpload && (
        <PdfUpload
          onUploadComplete={handleUploadComplete}
          onClose={() => dispatch({ type: "SET_SHOW_UPLOAD", payload: false })}
        />
      )}

      {/* Simulation panel */}
      <SimulationPanel
        isOpen={appState.showSimulation}
        households={state?.households ?? []}
        onClose={() => dispatch({ type: "SET_SHOW_SIMULATION", payload: false })}
        onRunSimulation={handleRunSimulation}
      />

      {/* 25-message auth gate */}
      {appState.showSignInPrompt && (
        <SignInPrompt
          onSignIn={handleSignIn}
          onClose={() => dispatch({ type: "SET_SHOW_SIGN_IN_PROMPT", payload: false })}
        />
      )}
    </div>
  );
}
