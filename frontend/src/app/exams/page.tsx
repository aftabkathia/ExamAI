"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { RequireAuth } from "@/components/RequireAuth";
import { ExamIcon } from "@/components/ExamIcon";
import { api } from "@/lib/api";
import type { ExamTrack } from "@/lib/types";
import { cn } from "@/lib/utils";

function ExamsContent() {
  const [exams, setExams] = useState<ExamTrack[]>([]);
  const [filter, setFilter] = useState<"all" | "academic" | "government">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<ExamTrack[]>("/exams")
      .then(setExams)
      .finally(() => setLoading(false));
  }, []);

  const filtered =
    filter === "all" ? exams : exams.filter((e) => e.category === filter);

  return (
    <div className="space-y-8 animate-fade-up">
      <div>
        <p className="section-label">Practice</p>
        <h1 className="mt-2 font-display text-4xl text-sand-50">Choose your exam</h1>
        <p className="mt-2 max-w-xl text-sand-200/60">
          Dual tracks for academic entry tests and government job MCQs. The adaptive
          engine will target your weak topics.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["all", "All exams"],
            ["academic", "Academic entry"],
            ["government", "Government jobs"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={cn(
              "rounded-full px-4 py-2 text-sm transition",
              filter === key
                ? "bg-jade-500 text-ink-950 font-semibold"
                : "bg-white/5 text-sand-200/70 hover:bg-white/10"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-jade-500 border-t-transparent" />
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {filtered.map((exam) => (
            <Link
              key={exam.id}
              href={`/exams/${exam.id}`}
              className="panel group block p-6 transition hover:-translate-y-0.5 hover:border-jade-500/30 hover:shadow-glow"
            >
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-jade-500/15 text-jade-400 ring-1 ring-jade-500/25 transition group-hover:bg-jade-500/25">
                  <ExamIcon name={exam.icon} />
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-md bg-white/5 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-sand-200/60">
                      {exam.code}
                    </span>
                    <span className="text-[11px] uppercase tracking-wider text-jade-400/80">
                      {exam.category}
                    </span>
                  </div>
                  <h2 className="mt-2 font-display text-xl text-sand-50 group-hover:text-jade-300">
                    {exam.name}
                  </h2>
                  <p className="mt-2 line-clamp-2 text-sm text-sand-200/55">
                    {exam.description}
                  </p>
                  <p className="mt-3 text-xs text-sand-200/40">
                    {exam.topics.length} topics
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ExamsPage() {
  return (
    <RequireAuth>
      <ExamsContent />
    </RequireAuth>
  );
}
