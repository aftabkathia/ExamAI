"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { RequireAuth } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import type { TopicNote } from "@/lib/types";
import { cn } from "@/lib/utils";

function NotesContent() {
  const [notes, setNotes] = useState<TopicNote[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<TopicNote[]>("/learn/notes")
      .then((data) => {
        setNotes(data);
        if (data[0]) setActiveId(data[0].id);
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = filter.toLowerCase();
    if (!q) return notes;
    return notes.filter(
      (n) =>
        n.title.toLowerCase().includes(q) ||
        (n.topic_name || "").toLowerCase().includes(q) ||
        (n.exam_name || "").toLowerCase().includes(q)
    );
  }, [notes, filter]);

  const active = notes.find((n) => n.id === activeId) || filtered[0];

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
        <p className="section-label">Study</p>
        <h1 className="mt-2 font-display text-4xl text-sand-50">Topic notes</h1>
        <p className="mt-2 max-w-2xl text-sand-200/60">
          Detailed revision sheets for Maths, Computer, Science, History, Pakistan
          Studies, English, and more — organised by exam topic.
        </p>
      </div>

      <input
        className="input-field max-w-md"
        placeholder="Filter by topic or exam…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />

      <div className="grid gap-6 lg:grid-cols-5">
        <aside className="panel max-h-[70vh] overflow-y-auto p-3 lg:col-span-2">
          <ul className="space-y-1">
            {filtered.map((n) => (
              <li key={n.id}>
                <button
                  onClick={() => setActiveId(n.id)}
                  className={cn(
                    "w-full rounded-xl px-3 py-2.5 text-left transition",
                    active?.id === n.id
                      ? "bg-jade-500/20 text-sand-50"
                      : "text-sand-200/70 hover:bg-white/5"
                  )}
                >
                  <p className="text-sm font-medium">{n.title}</p>
                  <p className="mt-0.5 text-xs text-sand-200/45">
                    {n.topic_name} · {n.exam_name}
                  </p>
                </button>
              </li>
            ))}
            {filtered.length === 0 && (
              <li className="px-3 py-6 text-sm text-sand-200/50">No notes match.</li>
            )}
          </ul>
        </aside>

        <article className="panel p-6 lg:col-span-3 sm:p-8">
          {active ? (
            <>
              <p className="text-xs uppercase tracking-wider text-jade-400">
                {active.topic_name}
              </p>
              <h2 className="mt-2 font-display text-3xl text-sand-50">{active.title}</h2>
              <p className="mt-2 text-sand-200/60">{active.summary}</p>

              {active.key_points.length > 0 && (
                <div className="mt-6 rounded-xl border border-jade-500/20 bg-jade-500/10 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-jade-300">
                    Key points
                  </p>
                  <ul className="mt-2 space-y-1.5 text-sm text-sand-100">
                    {active.key_points.map((p) => (
                      <li key={p} className="flex gap-2">
                        <span className="text-jade-400">•</span>
                        {p}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="prose-notes mt-8 space-y-4 text-[15px] leading-relaxed text-sand-200/80">
                {active.content.split("\n").map((line, i) => {
                  if (line.startsWith("## "))
                    return (
                      <h3 key={i} className="font-display text-xl text-sand-50 pt-2">
                        {line.replace("## ", "")}
                      </h3>
                    );
                  if (line.startsWith("- "))
                    return (
                      <p key={i} className="pl-3">
                        • {line.slice(2).replace(/\*\*(.*?)\*\*/g, "$1")}
                      </p>
                    );
                  if (!line.trim()) return null;
                  return (
                    <p key={i}>
                      {line.split(/(\*\*[^*]+\*\*)/).map((part, j) =>
                        part.startsWith("**") ? (
                          <strong key={j} className="font-semibold text-sand-50">
                            {part.slice(2, -2)}
                          </strong>
                        ) : (
                          <span key={j}>{part}</span>
                        )
                      )}
                    </p>
                  );
                })}
              </div>

              <Link
                href="/exams"
                className="btn-secondary mt-8 inline-flex"
              >
                Practice this topic
              </Link>
            </>
          ) : (
            <p className="text-sand-200/50">Select a note to read.</p>
          )}
        </article>
      </div>
    </div>
  );
}

export default function NotesPage() {
  return (
    <RequireAuth>
      <NotesContent />
    </RequireAuth>
  );
}
