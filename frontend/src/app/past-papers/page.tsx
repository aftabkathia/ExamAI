"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Check, X } from "lucide-react";
import { RequireAuth } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import type { PastPaper, PastPaperListItem } from "@/lib/types";
import { cn } from "@/lib/utils";

const OPTIONS = ["A", "B", "C", "D"] as const;

function optionText(q: PastPaper["questions"][0], key: string) {
  const map: Record<string, string> = {
    A: q.option_a,
    B: q.option_b,
    C: q.option_c,
    D: q.option_d,
  };
  return map[key];
}

function PastPapersContent() {
  const [list, setList] = useState<PastPaperListItem[]>([]);
  const [paper, setPaper] = useState<PastPaper | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [revealed, setRevealed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<PastPaperListItem[]>("/learn/past-papers")
      .then(setList)
      .finally(() => setLoading(false));
  }, []);

  async function openPaper(id: number) {
    setRevealed(false);
    setAnswers({});
    const data = await api<PastPaper>(`/learn/past-papers/${id}`);
    setPaper(data);
  }

  const score =
    paper && revealed
      ? paper.questions.filter((q) => answers[q.id] === q.correct_option).length
      : 0;

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-jade-500 border-t-transparent" />
      </div>
    );
  }

  if (paper) {
    return (
      <div className="mx-auto max-w-2xl space-y-6 animate-fade-up">
        <button
          onClick={() => setPaper(null)}
          className="text-sm text-sand-200/55 hover:text-sand-100"
        >
          ← All past papers
        </button>
        <div>
          <p className="section-label">{paper.year}</p>
          <h1 className="mt-2 font-display text-3xl text-sand-50">{paper.title}</h1>
          <p className="mt-2 text-sand-200/60">{paper.description}</p>
          <p className="mt-1 text-xs text-sand-200/40">
            {paper.topic_name} · {paper.exam_name} · {paper.question_count} MCQs
          </p>
        </div>

        {paper.questions.map((q, idx) => {
          const selected = answers[q.id];
          return (
            <div key={q.id} className="panel p-5">
              <p className="text-xs text-jade-400">Q{idx + 1}</p>
              <h2 className="mt-2 font-medium text-sand-50">{q.text}</h2>
              <div className="mt-4 space-y-2">
                {OPTIONS.map((key) => {
                  const isSel = selected === key;
                  const isCorrect = revealed && q.correct_option === key;
                  const isWrong = revealed && isSel && selected !== q.correct_option;
                  return (
                    <button
                      key={key}
                      disabled={revealed}
                      onClick={() => setAnswers((a) => ({ ...a, [q.id]: key }))}
                      className={cn(
                        "flex w-full items-start gap-3 rounded-xl border px-3 py-2.5 text-left text-sm transition",
                        !revealed &&
                          (isSel
                            ? "border-jade-500/50 bg-jade-500/10"
                            : "border-white/10 hover:bg-white/[0.04]"),
                        isCorrect && "border-jade-500/50 bg-jade-500/15",
                        isWrong && "border-red-500/40 bg-red-500/10"
                      )}
                    >
                      <span className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-md bg-white/10 text-xs font-bold">
                        {revealed && isCorrect ? (
                          <Check size={12} />
                        ) : revealed && isWrong ? (
                          <X size={12} />
                        ) : (
                          key
                        )}
                      </span>
                      {optionText(q, key)}
                    </button>
                  );
                })}
              </div>
              {revealed && (
                <p className="mt-3 text-sm text-sand-200/65">{q.explanation}</p>
              )}
            </div>
          );
        })}

        <div className="sticky bottom-4 panel flex flex-wrap items-center justify-between gap-3 p-4">
          {revealed ? (
            <>
              <p className="font-display text-xl text-jade-400">
                Score: {score}/{paper.questions.length}
              </p>
              <button
                className="btn-secondary"
                onClick={() => {
                  setRevealed(false);
                  setAnswers({});
                }}
              >
                Retry
              </button>
            </>
          ) : (
            <button
              className="btn-primary w-full sm:w-auto"
              onClick={() => setRevealed(true)}
              disabled={Object.keys(answers).length < paper.questions.length}
            >
              Check answers
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <p className="section-label">Archives</p>
        <h1 className="mt-2 font-display text-4xl text-sand-50">Past papers</h1>
        <p className="mt-2 max-w-2xl text-sand-200/60">
          Subject-wise past-paper style MCQs for every exam track — practise real
          patterns for Maths, Computer, Science, History, GK, and more.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {list.map((p) => (
          <button
            key={p.id}
            onClick={() => openPaper(p.id)}
            className="panel block p-5 text-left transition hover:-translate-y-0.5 hover:border-jade-500/30"
          >
            <p className="text-xs uppercase tracking-wider text-jade-400">{p.year}</p>
            <h2 className="mt-2 font-display text-lg text-sand-50">{p.title}</h2>
            <p className="mt-2 line-clamp-2 text-sm text-sand-200/55">{p.description}</p>
            <p className="mt-3 text-xs text-sand-200/40">
              {p.topic_name} · {p.question_count} questions
            </p>
          </button>
        ))}
      </div>

      {list.length === 0 && (
        <div className="panel p-8 text-sand-200/55">
          No past papers yet. Restart the API so learning content can seed.{" "}
          <Link href="/exams" className="text-jade-400 hover:underline">
            Or start an adaptive quiz
          </Link>
          .
        </div>
      )}
    </div>
  );
}

export default function PastPapersPage() {
  return (
    <RequireAuth>
      <PastPapersContent />
    </RequireAuth>
  );
}
