"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Check, X, ArrowRight, Lightbulb, Trophy } from "lucide-react";
import { RequireAuth } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import type { AnswerFeedback, Question, QuizSession } from "@/lib/types";
import { cn } from "@/lib/utils";

const OPTIONS = ["A", "B", "C", "D"] as const;

type StoredQuiz = {
  session: QuizSession;
  question: Question;
  index: number;
  examName?: string;
};

function optionText(q: Question, key: string) {
  const map: Record<string, string> = {
    A: q.option_a,
    B: q.option_b,
    C: q.option_c,
    D: q.option_d,
  };
  return map[key];
}

function QuizContent() {
  const params = useParams();
  const router = useRouter();
  const sessionId = Number(params.sessionId);

  const [question, setQuestion] = useState<Question | null>(null);
  const [session, setSession] = useState<QuizSession | null>(null);
  const [index, setIndex] = useState(0);
  const [examName, setExamName] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [finished, setFinished] = useState(false);
  const [score, setScore] = useState({ correct: 0, total: 0 });
  const [error, setError] = useState("");
  const startedAt = useRef(Date.now());

  useEffect(() => {
    const raw = sessionStorage.getItem(`quiz_${sessionId}`);
    if (!raw) {
      router.replace("/exams");
      return;
    }
    const data: StoredQuiz = JSON.parse(raw);
    setQuestion(data.question);
    setSession(data.session);
    setIndex(data.index);
    setExamName(data.examName || "");
    startedAt.current = Date.now();
  }, [sessionId, router]);

  const submit = useCallback(async () => {
    if (!selected || !question || !session || submitting) return;
    setSubmitting(true);
    setError("");
    try {
      const elapsed = Math.round((Date.now() - startedAt.current) / 1000);
      const res = await api<AnswerFeedback>("/quiz/answer", {
        method: "POST",
        body: JSON.stringify({
          session_id: session.id,
          question_id: question.id,
          selected_option: selected,
          time_spent_seconds: elapsed,
        }),
      });
      setFeedback(res);
      if (res.session_completed) {
        setScore({
          correct: res.session_score ?? 0,
          total: res.session_total ?? session.total_questions,
        });
        sessionStorage.removeItem(`quiz_${sessionId}`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submit failed");
    } finally {
      setSubmitting(false);
    }
  }, [selected, question, session, submitting, sessionId]);

  function nextQuestion() {
    if (!feedback || !session) return;
    if (feedback.session_completed || !feedback.next_question) {
      setFinished(true);
      return;
    }
    const next: StoredQuiz = {
      session,
      question: feedback.next_question,
      index: index + 1,
      examName,
    };
    sessionStorage.setItem(`quiz_${sessionId}`, JSON.stringify(next));
    setQuestion(feedback.next_question);
    setIndex(index + 1);
    setSelected(null);
    setFeedback(null);
    startedAt.current = Date.now();
  }

  if (finished) {
    const pct = score.total ? Math.round((score.correct / score.total) * 100) : 0;
    return (
      <div className="mx-auto max-w-lg text-center animate-fade-up">
        <div className="panel p-10">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-jade-500/20 text-jade-400 ring-1 ring-jade-500/30">
            <Trophy size={28} />
          </div>
          <h1 className="font-display text-3xl text-sand-50">Quiz complete</h1>
          <p className="mt-2 text-sand-200/60">{examName}</p>
          <p className="mt-8 font-display text-6xl text-jade-400">{pct}%</p>
          <p className="mt-2 text-sand-200/55">
            {score.correct} of {score.total} correct
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Link href="/dashboard" className="btn-primary">
              View progress
            </Link>
            <Link href="/exams" className="btn-secondary">
              Practice again
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!question || !session) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-jade-500 border-t-transparent" />
      </div>
    );
  }

  const progress = ((index + (feedback ? 1 : 0)) / session.total_questions) * 100;

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-up">
      <div className="flex items-center justify-between gap-4 text-sm text-sand-200/55">
        <span className="truncate">{examName}</span>
        <span>
          {index + 1} / {session.total_questions}
        </span>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-jade-500 transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="panel p-6 sm:p-8">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {question.topic_name && (
            <span className="rounded-md bg-jade-500/15 px-2.5 py-1 text-xs font-medium text-jade-300">
              {question.topic_name}
            </span>
          )}
          <span className="rounded-md bg-white/5 px-2.5 py-1 text-xs capitalize text-sand-200/50">
            {question.difficulty}
          </span>
        </div>

        <h2 className="font-display text-xl leading-snug text-sand-50 sm:text-2xl">
          {question.text}
        </h2>

        <div className="mt-8 space-y-3">
          {OPTIONS.map((key) => {
            const isSelected = selected === key;
            const showResult = !!feedback;
            const isCorrect = feedback?.correct_option === key;
            const isWrongPick =
              showResult && isSelected && !feedback.is_correct;

            return (
              <button
                key={key}
                disabled={!!feedback || submitting}
                onClick={() => setSelected(key)}
                className={cn(
                  "flex w-full items-start gap-3 rounded-xl border px-4 py-3.5 text-left transition",
                  !showResult &&
                    (isSelected
                      ? "border-jade-500/50 bg-jade-500/10"
                      : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"),
                  showResult && isCorrect && "border-jade-500/50 bg-jade-500/15",
                  showResult && isWrongPick && "border-red-500/40 bg-red-500/10",
                  showResult && !isCorrect && !isWrongPick && "border-white/5 opacity-50"
                )}
              >
                <span
                  className={cn(
                    "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold",
                    isSelected || isCorrect
                      ? "bg-jade-500 text-ink-950"
                      : "bg-white/10 text-sand-200/70",
                    isWrongPick && "bg-red-500 text-white"
                  )}
                >
                  {showResult && isCorrect ? (
                    <Check size={14} />
                  ) : showResult && isWrongPick ? (
                    <X size={14} />
                  ) : (
                    key
                  )}
                </span>
                <span className="text-sm leading-relaxed text-sand-100 sm:text-[15px]">
                  {optionText(question, key)}
                </span>
              </button>
            );
          })}
        </div>

        {feedback && (
          <div
            className={cn(
              "mt-6 rounded-xl border p-4",
              feedback.is_correct
                ? "border-jade-500/30 bg-jade-500/10"
                : "border-ember-400/30 bg-ember-400/10"
            )}
          >
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Lightbulb size={16} className="text-ember-400" />
              {feedback.is_correct ? "Correct!" : "Not quite"}
            </div>
            <p className="mt-2 text-sm leading-relaxed text-sand-200/75">
              {feedback.explanation}
            </p>
            <p className="mt-2 text-xs text-sand-200/45">
              Topic mastery now {Math.round(feedback.mastery_score * 100)}%
            </p>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="mt-8">
          {!feedback ? (
            <button
              onClick={submit}
              disabled={!selected || submitting}
              className="btn-primary w-full"
            >
              {submitting ? "Checking…" : "Submit answer"}
            </button>
          ) : (
            <button onClick={nextQuestion} className="btn-primary w-full">
              {feedback.session_completed ? "See results" : "Next question"}
              <ArrowRight size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function QuizPage() {
  return (
    <RequireAuth>
      <QuizContent />
    </RequireAuth>
  );
}
