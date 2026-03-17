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
import { WidgetSpec } from "@/types/widgets";

export default function WealthLensApp() {
  // UI state
  const [showUpload, setShowUpload] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userName, setUserName] = useState<string | undefined>();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [usage, setUsage] = useState<UsageMeter>({ used: 0, limit: 25 });
  const [conversationTitle, setConversationTitle] = useState<string | undefined>();

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

  const { sendMessage } = useCopilotChat();

  // Handlers
  const handleToggleTheme = useCallback(() => {
    setIsDark((prev) => !prev);
  }, []);

  const handleSignIn = useCallback(() => {
    setIsLoggedIn(true);
    setUserName("Alex");
    setConversations([
      { id: "conv_01", title: "New Analysis", timestamp: "Just now", isActive: true },
    ]);
  }, []);

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
    // Auto-login on first message
    if (!isLoggedIn) {
      handleSignIn();
    }
    setUsage((prev) => ({ ...prev, used: prev.used + 1 }));
    setConversationTitle(prompt.slice(0, 40) + (prompt.length > 40 ? "..." : ""));
    await sendMessage({
      id: `suggestion-${Date.now()}`,
      role: "user",
      content: prompt,
    });
  }, [isLoggedIn, handleSignIn, sendMessage]);

  const handleUploadClick = useCallback(() => {
    if (!isLoggedIn) handleSignIn();
    setShowUpload(true);
  }, [isLoggedIn, handleSignIn]);

  const handleRemoveWidget = useCallback((widgetId: string) => {
    setState((prev: any) => ({
      ...prev,
      widgets: (prev.widgets || []).filter((w: WidgetSpec) => w.id !== widgetId),
    }));
  }, [setState]);

  const handleAskAboutWidget = useCallback((widget: WidgetSpec) => {
    console.log("Ask about widget:", widget.title);
  }, []);

  const handleUploadComplete = useCallback((result: any) => {
    setShowUpload(false);
    if (result && result.accounts) {
      setState((prev: any) => {
        const existingHouseholds = prev.households || [];
        const newHousehold = {
          id: `h-${Date.now()}`,
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
        <div ref={containerRef} className="flex h-full bg-slate-50 dark:bg-slate-950">
          {/* Left: Dashboard Canvas */}
          <div
            className="h-full shrink-0 flex-col transition-[width] duration-300 ease-out flex"
            style={{ width: hasWidgets ? `${canvasPercent}%` : "60%" }}
          >
            <DashboardCanvas
              widgets={state?.widgets ?? []}
              onSuggestionSelect={handleSuggestionSelect}
              onUploadClick={handleUploadClick}
              onRemoveWidget={handleRemoveWidget}
              onAskAboutWidget={handleAskAboutWidget}
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
      </main>

      {/* Upload modal */}
      {showUpload && (
        <PdfUpload
          onUploadComplete={handleUploadComplete}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  );
}
