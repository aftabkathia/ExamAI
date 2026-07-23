"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Brain, ChartLine, Sparkles, Target } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const tracks = [
  { label: "Academic", items: "CSS · MDCAT · ECAT · NET" },
  { label: "Government", items: "NTS · PPSC · FPSC · OTS" },
];

const features = [
  {
    icon: Sparkles,
    title: "AI-generated MCQs",
    body: "Unlimited practice questions with plain-language explanations for every answer.",
  },
  {
    icon: Target,
    title: "Adaptive difficulty",
    body: "Questions weight toward your weak topics so every session sharpens what matters.",
  },
  {
    icon: ChartLine,
    title: "Progress that motivates",
    body: "Accuracy by subject, improvement trends, and streaks tied to your profile.",
  },
  {
    icon: Brain,
    title: "Pakistan-first content",
    body: "Built for local syllabi and exam patterns — not generic international prep.",
  },
];

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  return (
    <div className="relative">
      {/* Hero — one composition */}
      <section className="relative overflow-hidden pb-20 pt-10 sm:pt-16">
        <div
          className="pointer-events-none absolute -left-24 top-0 h-72 w-72 rounded-full bg-jade-500/20 blur-3xl animate-pulse-soft"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute -right-16 top-24 h-64 w-64 rounded-full bg-ember-400/10 blur-3xl"
          aria-hidden
        />

        <div className="relative mx-auto max-w-3xl text-center animate-fade-up">
          <p className="section-label mb-6">Adaptive test preparation</p>
          <h1 className="font-display text-5xl leading-[1.05] tracking-tight text-sand-50 sm:text-7xl">
            Exam<span className="text-jade-400">AI</span>
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-lg text-sand-200/70 sm:text-xl">
            Personalised practice for Pakistan&apos;s competitive &amp; government
            job exams — powered by AI that adapts to you.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link href="/register" className="btn-primary">
              Start practicing
              <ArrowRight size={16} />
            </Link>
            <Link href="/login" className="btn-secondary">
              I already have an account
            </Link>
          </div>
        </div>

        <div
          className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-4 sm:grid-cols-2 animate-fade-up"
          style={{ animationDelay: "120ms" }}
        >
          {tracks.map((t) => (
            <div
              key={t.label}
              className="panel px-6 py-5 text-left transition hover:border-jade-500/30 hover:shadow-glow"
            >
              <p className="text-xs font-semibold uppercase tracking-wider text-jade-400">
                {t.label}
              </p>
              <p className="mt-2 font-display text-lg text-sand-50">{t.items}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-white/5 py-16">
        <div className="mb-10 max-w-xl">
          <p className="section-label">Why ExamAI</p>
          <h2 className="mt-3 font-display text-3xl text-sand-50 sm:text-4xl">
            A tutor that never runs out of questions
          </h2>
        </div>
        <div className="grid gap-5 sm:grid-cols-2">
          {features.map((f, i) => (
            <div
              key={f.title}
              className="panel group p-6 transition hover:-translate-y-0.5 hover:border-jade-500/25"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-jade-500/15 text-jade-400 ring-1 ring-jade-500/25 transition group-hover:bg-jade-500/25">
                <f.icon size={20} />
              </div>
              <h3 className="font-display text-xl text-sand-50">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-sand-200/60">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="pb-8 pt-4 text-center">
        <div className="panel mx-auto max-w-2xl overflow-hidden p-10">
          <h2 className="font-display text-3xl text-sand-50">Ready when you are</h2>
          <p className="mt-3 text-sand-200/60">
            Create a free account and take your first adaptive quiz in minutes.
          </p>
          <Link href="/register" className="btn-primary mt-8">
            Create account
            <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  );
}
