"use client";

import { useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import type { EssayPrompt } from "@/lib/types";
import { cn } from "@/lib/utils";

function EssaysContent() {
  const [essays, setEssays] = useState<EssayPrompt[]>([]);
  const [active, setActive] = useState<EssayPrompt | null>(null);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<EssayPrompt[]>("/learn/essays")
      .then((data) => {
        setEssays(data);
        setActive(data[0] || null);
      })
      .finally(() => setLoading(false));
  }, []);

  const words = draft.trim() ? draft.trim().split(/\s+/).length : 0;

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-jade-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <p className="section-label">Writing</p>
        <h1 className="mt-2 font-display text-4xl text-sand-50">Essay practice</h1>
        <p className="mt-2 max-w-2xl text-sand-200/60">
          CSS/FPSC-style prompts with outlines. Draft here, stay within the word
          limit, and revise structure before the real exam.
        </p>
      </div>

      {essays.length === 0 ? (
        <div className="panel p-8 text-sand-200/55">
          No essay prompts seeded yet. Restart the backend to load learning content.
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          <aside className="panel max-h-[70vh] space-y-1 overflow-y-auto p-3 lg:col-span-2">
            {essays.map((e) => (
              <button
                key={e.id}
                onClick={() => {
                  setActive(e);
                  setDraft("");
                }}
                className={cn(
                  "w-full rounded-xl px-3 py-2.5 text-left transition",
                  active?.id === e.id
                    ? "bg-jade-500/20 text-sand-50"
                    : "text-sand-200/70 hover:bg-white/5"
                )}
              >
                <p className="text-sm font-medium">{e.title}</p>
                <p className="mt-0.5 text-xs text-sand-200/45">
                  {e.topic_name} · {e.word_limit} words · {e.difficulty}
                </p>
              </button>
            ))}
          </aside>

          {active && (
            <div className="space-y-4 lg:col-span-3">
              <div className="panel p-6">
                <p className="text-xs uppercase tracking-wider text-jade-400">
                  {active.exam_name} · {active.topic_name}
                </p>
                <h2 className="mt-2 font-display text-2xl text-sand-50">{active.title}</h2>
                <p className="mt-3 text-sand-200/75">{active.prompt}</p>
                <div className="mt-5 rounded-xl bg-white/[0.03] p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-ember-400">
                    Suggested outline
                  </p>
                  <pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-sand-200/70">
                    {active.outline}
                  </pre>
                </div>
              </div>

              <div className="panel p-6">
                <div className="mb-3 flex items-center justify-between text-sm">
                  <span className="text-sand-200/55">Your draft</span>
                  <span
                    className={cn(
                      words > active.word_limit ? "text-red-400" : "text-jade-400"
                    )}
                  >
                    {words} / {active.word_limit} words
                  </span>
                </div>
                <textarea
                  className="input-field min-h-[240px] resize-y"
                  placeholder="Write your essay draft here…"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                />
                <p className="mt-2 text-xs text-sand-200/40">
                  Drafts stay in this browser session only — copy them if you want to keep them.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function EssaysPage() {
  return (
    <RequireAuth>
      <EssaysContent />
    </RequireAuth>
  );
}
