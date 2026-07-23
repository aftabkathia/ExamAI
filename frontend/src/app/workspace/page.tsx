"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  CheckSquare,
  FileSearch,
  FileText,
  LayoutGrid,
  MessageSquare,
  NotebookPen,
  PenTool,
} from "lucide-react";
import { RequireAuth } from "@/components/RequireAuth";
import { ChatPanel } from "@/components/workspace/ChatPanel";
import { NotesPanel } from "@/components/workspace/NotesPanel";
import { TasksPanel } from "@/components/workspace/TasksPanel";
import { DocumentsPanel } from "@/components/workspace/DocumentsPanel";
import { WhiteboardPanel } from "@/components/workspace/WhiteboardPanel";
import { IntelligencePanel } from "@/components/workspace/IntelligencePanel";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "notes", label: "Notes", icon: NotebookPen },
  { id: "tasks", label: "Tasks", icon: CheckSquare },
  { id: "documents", label: "Documents", icon: FileText },
  { id: "intel", label: "Doc Intel", icon: FileSearch },
  { id: "whiteboard", label: "Whiteboard", icon: PenTool },
] as const;

type TabId = (typeof TABS)[number]["id"];

type Summary = {
  notes_count: number;
  tasks_open: number;
  documents_count: number;
  intel_documents: number;
  has_whiteboard: boolean;
};

function WorkspaceContent() {
  const searchParams = useSearchParams();
  const initial = (searchParams.get("tab") as TabId) || "chat";
  const [tab, setTab] = useState<TabId>(
    TABS.some((t) => t.id === initial) ? initial : "chat"
  );
  const [summary, setSummary] = useState<Summary | null>(null);

  const refreshSummary = useCallback(() => {
    api<Summary>("/workspace/summary").then(setSummary).catch(() => {});
  }, []);

  useEffect(() => {
    refreshSummary();
  }, [refreshSummary, tab]);

  function badge(id: TabId): string | null {
    if (!summary) return null;
    if (id === "notes" && summary.notes_count) return String(summary.notes_count);
    if (id === "tasks" && summary.tasks_open) return String(summary.tasks_open);
    if (id === "documents" && summary.documents_count) return String(summary.documents_count);
    if (id === "intel" && summary.intel_documents) return String(summary.intel_documents);
    return null;
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-6xl flex-col animate-fade-up">
      <div className="mb-4 shrink-0">
        <p className="section-label flex items-center gap-2">
          <LayoutGrid size={12} /> AI Workspace
        </p>
        <h1 className="mt-2 font-display text-3xl text-sand-50 sm:text-4xl">
          Everything connected
        </h1>
        <p className="mt-1 text-sm text-sand-200/55">
          Chat · Notes · Tasks · Documents · Doc Intel · Whiteboard
        </p>
      </div>

      <div className="panel flex min-h-0 flex-1 flex-col overflow-hidden">
        <nav className="flex shrink-0 gap-1 overflow-x-auto border-b border-white/5 p-2">
          {TABS.map(({ id, label, icon: Icon }) => {
            const count = badge(id);
            return (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                className={cn(
                  "flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-sm transition",
                  tab === id
                    ? "bg-jade-500/15 text-jade-300 ring-1 ring-jade-500/30"
                    : "text-sand-200/60 hover:bg-white/5 hover:text-sand-100"
                )}
              >
                <Icon size={16} />
                {label}
                {count && (
                  <span className="rounded-full bg-jade-500/20 px-1.5 text-[10px] font-medium text-jade-300">
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="min-h-0 flex-1 overflow-hidden p-4 sm:p-5">
          {tab === "chat" && (
            <div className="-m-4 flex h-[calc(100%+2rem)] flex-col sm:-m-5">
              <ChatPanel />
            </div>
          )}
          {tab === "notes" && <NotesPanel />}
          {tab === "tasks" && <TasksPanel />}
          {tab === "documents" && <DocumentsPanel />}
          {tab === "intel" && <IntelligencePanel />}
          {tab === "whiteboard" && <WhiteboardPanel />}
        </div>
      </div>
    </div>
  );
}

export default function WorkspacePage() {
  return (
    <RequireAuth>
      <Suspense
        fallback={
          <div className="flex h-64 items-center justify-center text-sand-200/50">Loading workspace…</div>
        }
      >
        <WorkspaceContent />
      </Suspense>
    </RequireAuth>
  );
}
