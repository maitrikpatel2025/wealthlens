"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import {
  useCoAgent,
  useCoAgentStateRender,
  useCopilotAction,
  useCopilotChat,
} from "@copilotkit/react-core";
import { GripVertical } from "lucide-react";
import { TopNav } from "./components/top-nav";
import { SideNav } from "./components/side-nav";
import type { Conversation, UsageMeter } from "@/types/api";
import { ChatPanel } from "./components/chat-panel";
import { DashboardCanvas } from "./components/dashboard-canvas";
import { ToolLogs } from "./components/tool-logs";
import { PdfUpload } from "./components/pdf-upload";
import { SimulationPanel } from "./components/simulation-panel";
import { SignInPrompt } from "./components/sign-in-prompt";
import { WidgetSpec } from "@/types/widgets";
import { composeWidgetQuestion, composeDataPointQuestion } from "@/utils/compose-question";
import { TextMessage, Role } from "@copilotkit/runtime-client-gql";
import { useAuth } from "@/hooks/use-auth";
import { useRouter } from "next/navigation";

export default function WealthLensApp() {
  // Auth
  const { user, session, isLoading: authLoading, signOut } = useAuth();
  const router = useRouter();
  const isLoggedIn = !!user;
  const userName = user?.user_metadata?.full_name || user?.email?.split("@")[0];

  // UI state
  const [showUpload, setShowUpload] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [usage, setUsage] = useState<UsageMeter>({ used: 0, limit: 25 });
  const [conversationTitle, setConversationTitle] = useState<string | undefined>();
  const [showSimulation, setShowSimulation] = useState(false);
  const [showSignInPrompt, setShowSignInPrompt] = useState(false);

  // Resizable panel state
  const [canvasPercent, setCanvasPercent] = useState(60);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);

  // CopilotKit agent state
  const { state, setState } = useCoAgent({
    name: "wealthlens",
    initialState: {
      widgets: [] as WidgetSpec[],
      tool_logs: [],
      households: [],
      user_profile: {},
    },
  });

  useCoAgentStateRender({
    name: "wealthlens",
    render: ({ state }) => <ToolLogs logs={state.tool_logs} />,
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
        setState((prev: any) => ({
          ...prev,
          widgets: newWidgets,
        }));
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
          setState((prev: any) => ({
            ...prev,
            households: data.households,
          }));
        }
      } catch (e) {
        console.error("Failed to load portfolios:", e);
      }
    }

    loadUserData();
    setConversations([
      { id: "conv_01", title: "New Analysis", timestamp: "Just now", isActive: true },
    ]);
  }, [user, session]);

  // Dark mode toggle
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    return () => {
      document.documentElement.classList.remove("dark");
    };
  }, [isDark]);

  const { appendMessage } = useCopilotChat() as any;
  const sendMessage = useCallback(async (msg: { id?: string; role: string; content: string }) => {
    const textMsg = new TextMessage({
      id: msg.id || `msg-${Date.now()}`,
      role: msg.role === "user" ? Role.User : Role.Assistant,
      content: msg.content,
    });
    await appendMessage(textMsg);
  }, [appendMessage]);

  // Handlers
  const handleToggleTheme = useCallback(() => {
    setIsDark((prev) => !prev);
  }, []);

  const handleSignIn = useCallback(() => {
    router.push("/auth/login");
  }, [router]);

  const handleSignOut = useCallback(async () => {
    await signOut();
    setState((prev: any) => ({
      ...prev,
      widgets: [],
      households: [],
      user_profile: {},
    }));
    setConversations([]);
  }, [signOut, setState]);

  const handleNewChat = useCallback(() => {
    const newId = `conv_${Date.now()}`;
    setConversations((prev) => [
      { id: newId, title: "New Analysis", timestamp: "Just now", isActive: true },
      ...prev.map((c) => ({ ...c, isActive: false })),
    ]);
    setConversationTitle(undefined);
    setSidebarOpen(false);
  }, []);

  const handleSelectConversation = useCallback((id: string) => {
    setConversations((prev) =>
      prev.map((c) => ({ ...c, isActive: c.id === id }))
    );
    setSidebarOpen(false);
  }, []);

  const handleSuggestionSelect = useCallback(async (prompt: string) => {
    if (!isLoggedIn && usage.used >= usage.limit) {
      setShowSignInPrompt(true);
      return;
    }
    setUsage((prev) => ({ ...prev, used: prev.used + 1 }));
    setConversationTitle(prompt.slice(0, 40) + (prompt.length > 40 ? "..." : ""));
    await sendMessage({
      id: `suggestion-${Date.now()}`,
      role: "user",
      content: prompt,
    });
  }, [isLoggedIn, usage, sendMessage]);

  const handleUploadClick = useCallback(() => {
    if (!isLoggedIn && usage.used >= usage.limit) {
      setShowSignInPrompt(true);
      return;
    }
    setShowUpload(true);
  }, [isLoggedIn, usage]);

  const handleRemoveWidget = useCallback((widgetId: string) => {
    setState((prev: any) => ({
      ...prev,
      widgets: (prev.widgets || []).filter((w: WidgetSpec) => w.id !== widgetId),
    }));
  }, [setState]);

  const handleAskAboutWidget = useCallback((widget: WidgetSpec) => {
    const question = composeWidgetQuestion(widget);
    if (!isLoggedIn && usage.used >= usage.limit) {
      setShowSignInPrompt(true);
      return;
    }
    setUsage((prev) => ({ ...prev, used: prev.used + 1 }));
    setConversationTitle(question.slice(0, 40) + (question.length > 40 ? "..." : ""));
    sendMessage({ id: `widget-${Date.now()}`, role: "user", content: question });
  }, [isLoggedIn, usage, sendMessage]);

  const handleDataPointClick = useCallback((widget: WidgetSpec, dataPoint: Record<string, any>) => {
    const question = composeDataPointQuestion(widget, dataPoint);
    if (!isLoggedIn && usage.used >= usage.limit) {
      setShowSignInPrompt(true);
      return;
    }
    setUsage((prev) => ({ ...prev, used: prev.used + 1 }));
    setConversationTitle(question.slice(0, 40) + (question.length > 40 ? "..." : ""));
    sendMessage({ id: `drill-${Date.now()}`, role: "user", content: question });
  }, [isLoggedIn, usage, sendMessage]);

  const handleRunSimulation = useCallback(async (prompt: string) => {
    setShowSimulation(false);
    if (!isLoggedIn && usage.used >= usage.limit) {
      setShowSignInPrompt(true);
      return;
    }
    setUsage((prev) => ({ ...prev, used: prev.used + 1 }));
    setConversationTitle("Simulation");
    await sendMessage({ id: `sim-${Date.now()}`, role: "user", content: prompt });
  }, [isLoggedIn, usage, sendMessage]);

  const handleUploadComplete = useCallback((result: any) => {
    setShowUpload(false);
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
  }, [setState]);

  // Resizable divider drag handler
  const handleMouseDown = useCallback(() => {
    isDragging.current = true;

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      let pct = ((e.clientX - rect.left) / rect.width) * 100;
      pct = Math.max(30, Math.min(75, pct));
      setCanvasPercent(pct);
    };

    const handleMouseUp = () => {
      isDragging.current = false;
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  const hasWidgets = (state?.widgets ?? []).length > 0;
  const activeConversation = conversations.find((c) => c.isActive);

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
    <div className={`flex h-screen flex-col bg-white dark:bg-slate-950 ${isDark ? "dark" : ""}`}>
      {/* Top Navigation */}
      <TopNav
        conversationTitle={conversationTitle || activeConversation?.title}
        isLoggedIn={isLoggedIn}
        isDarkMode={isDark}
        userName={userName}
        showSignIn={!isLoggedIn}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onNewChat={handleNewChat}
        onToggleTheme={handleToggleTheme}
        onSignIn={handleSignIn}
        onSignOut={handleSignOut}
        onTitleChange={setConversationTitle}
        showHamburger={isLoggedIn}
      />

      {/* Side Navigation */}
      {isLoggedIn && (
        <SideNav
          isOpen={sidebarOpen}
          conversations={conversations}
          usage={usage}
          onClose={() => setSidebarOpen(false)}
          onNewChat={() => {
            handleNewChat();
            setSidebarOpen(false);
          }}
          onUploadStatement={() => {
            handleUploadClick();
            setSidebarOpen(false);
          }}
          onSelectConversation={handleSelectConversation}
        />
      )}

      {/* Main content area */}
      <main
        className={`flex-1 overflow-hidden pt-14 transition-all duration-200 ${
          isLoggedIn && sidebarOpen ? "lg:pl-[280px]" : ""
        }`}
      >
        {!hasWidgets ? (
          /* ── Chat-centered layout (no widgets yet) ── */
          <div className="flex h-full justify-center bg-white dark:bg-slate-950">
            <div className="flex h-full w-full max-w-[720px] flex-col">
              <ChatPanel
                onUploadComplete={handleUploadComplete}
                showWelcome
                onUploadClick={handleUploadClick}
              />
            </div>
          </div>
        ) : (
          /* ── Split layout: canvas (60%) | divider | chat (40%) ── */
          <div ref={containerRef} className="flex h-full bg-slate-50 dark:bg-slate-950">
            {/* Left: Dashboard Canvas */}
            <div
              className="canvas-animate-in h-full shrink-0 flex-col flex"
              style={{ width: `${canvasPercent}%` }}
            >
              <DashboardCanvas
                widgets={state?.widgets ?? []}
                households={state?.households ?? []}
                onSuggestionSelect={handleSuggestionSelect}
                onUploadClick={handleUploadClick}
                onRemoveWidget={handleRemoveWidget}
                onAskAboutWidget={handleAskAboutWidget}
                onDataPointClick={handleDataPointClick}
                onSimulateClick={(state?.households ?? []).length > 0 ? () => setShowSimulation(true) : undefined}
              />
            </div>

            {/* Resizable divider */}
            <div
              className="group relative flex h-full w-3 shrink-0 cursor-col-resize items-center justify-center hover:bg-slate-100 dark:hover:bg-slate-800"
              onMouseDown={handleMouseDown}
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
      {showUpload && (
        <PdfUpload
          onUploadComplete={handleUploadComplete}
          onClose={() => setShowUpload(false)}
        />
      )}

      {/* Simulation panel */}
      <SimulationPanel
        isOpen={showSimulation}
        households={state?.households ?? []}
        onClose={() => setShowSimulation(false)}
        onRunSimulation={handleRunSimulation}
      />

      {/* 25-message auth gate */}
      {showSignInPrompt && (
        <SignInPrompt
          onSignIn={handleSignIn}
          onClose={() => setShowSignInPrompt(false)}
        />
      )}
    </div>
  );
}
