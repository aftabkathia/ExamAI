"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Play, NotebookPen, FileStack, ScrollText } from "lucide-react";
import { RequireAuth } from "@/components/RequireAuth";
import { ExamIcon } from "@/components/ExamIcon";
import { api } from "@/lib/api";
import type { ExamTrack, Question, QuizSession } from "@/lib/types";
import { cn } from "@/lib/utils";

function ExamDetailContent() {
  const params = useParams();
  const router = useRouter();
  const examId = Number(params.id);
  const [exam, setExam] = useState<ExamTrack | null>(null);
  const [topicId, setTopicId] = useState<number | null>(null);
  const [count, setCount] = useState(10);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!examId) return;
    api<ExamTrack>(`/exams/${examId}`).then(setExam).catch((e) => setError(e.message));
  }, [examId]);

  async function startQuiz() {
    setStarting(true);
    setError("");
    try {
      const res = await api<{ session: QuizSession; question: Question }>("/quiz/start", {
        method: "POST",
        body: JSON.stringify({
          exam_track_id: examId,
          total_questions: count,
          topic_id: topicId,
        }),
      });
      sessionStorage.setItem(
        `quiz_${res.session.id}`,
        JSON.stringify({
          session: res.session,
          question: res.question,
          index: 0,
          examName: exam?.name,
        })
      );
      router.push(`/quiz/${res.session.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start quiz");
      setStarting(false);
    }
  }

  if (error && !exam) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
        {error}
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-jade-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8 animate-fade-up">
      <Link
        href="/exams"
        className="inline-flex items-center gap-2 text-sm text-sand-200/55 transition hover:text-sand-100"
      >
        <ArrowLeft size={16} />
        All exams
      </Link>

      <div className="panel p-6 sm:p-8">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-jade-500/15 text-jade-400 ring-1 ring-jade-500/25">
            <ExamIcon name={exam.icon} size={26} />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-jade-400">
              {exam.code} · {exam.category}
            </p>
            <h1 className="mt-1 font-display text-3xl text-sand-50">{exam.name}</h1>
            <p className="mt-3 text-sm leading-relaxed text-sand-200/60">
              {exam.description}
            </p>
          </div>
        </div>

        <div className="mt-8 space-y-6 border-t border-white/5 pt-8">
          <div>
            <label className="mb-3 block text-sm font-medium text-sand-100">
              Topic focus
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setTopicId(null)}
                className={cn(
                  "rounded-full px-3 py-1.5 text-xs transition",
                  topicId === null
                    ? "bg-jade-500 text-ink-950 font-semibold"
                    : "bg-white/5 text-sand-200/65 hover:bg-white/10"
                )}
              >
                Adaptive (all topics)
              </button>
              {exam.topics.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTopicId(t.id)}
                  className={cn(
                    "rounded-full px-3 py-1.5 text-xs transition",
                    topicId === t.id
                      ? "bg-jade-500 text-ink-950 font-semibold"
                      : "bg-white/5 text-sand-200/65 hover:bg-white/10"
                  )}
                >
                  {t.name}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-3 block text-sm font-medium text-sand-100">
              Questions: {count}
            </label>
            <input
              type="range"
              min={5}
              max={20}
              step={5}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="w-full accent-jade-500"
            />
            <div className="mt-1 flex justify-between text-xs text-sand-200/40">
              <span>5</span>
              <span>10</span>
              <span>15</span>
              <span>20</span>
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <button
            onClick={startQuiz}
            disabled={starting}
            className="btn-primary w-full"
          >
            <Play size={16} />
            {starting ? "Generating first question…" : "Start adaptive quiz"}
          </button>

          <div className="grid grid-cols-3 gap-2 pt-2">
            <Link href="/notes" className="btn-secondary justify-center px-2 text-xs">
              <NotebookPen size={14} />
              Notes
            </Link>
            <Link href="/past-papers" className="btn-secondary justify-center px-2 text-xs">
              <FileStack size={14} />
              Papers
            </Link>
            <Link href="/essays" className="btn-secondary justify-center px-2 text-xs">
              <ScrollText size={14} />
              Essays
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ExamDetailPage() {
  return (
    <RequireAuth>
      <ExamDetailContent />
    </RequireAuth>
  );
}
