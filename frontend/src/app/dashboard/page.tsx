"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Flame,
  Target,
  Trophy,
  BookOpen,
  TrendingUp,
} from "lucide-react";
import { RequireAuth } from "@/components/RequireAuth";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import type { ProgressDashboard } from "@/lib/types";
import { masteryColor, masteryLabel } from "@/lib/utils";

function ActivityChart({
  data,
}: {
  data: ProgressDashboard["recent_activity"];
}) {
  const max = Math.max(1, ...data.map((d) => d.attempts));
  return (
    <div className="flex h-32 items-end gap-1.5">
      {data.map((d) => {
        const h = (d.attempts / max) * 100;
        const accuracy = d.attempts ? d.correct / d.attempts : 0;
        return (
          <div key={d.date} className="group relative flex flex-1 flex-col items-center">
            <div
              className="w-full rounded-t-md bg-jade-500/80 transition group-hover:bg-jade-400"
              style={{
                height: `${Math.max(h, d.attempts ? 8 : 2)}%`,
                opacity: d.attempts ? 0.4 + accuracy * 0.6 : 0.15,
              }}
              title={`${d.date}: ${d.correct}/${d.attempts}`}
            />
          </div>
        );
      })}
    </div>
  );
}

function DashboardContent() {
  const { user } = useAuth();
  const [data, setData] = useState<ProgressDashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<ProgressDashboard>("/progress/dashboard")
      .then(setData)
      .catch((e) => setError(e.message || "Failed to load"));
  }, []);

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-jade-500 border-t-transparent" />
      </div>
    );
  }

  const stats = [
    {
      label: "Accuracy",
      value: `${data.overall_accuracy}%`,
      icon: Target,
      hint: `${data.total_correct}/${data.total_attempts} correct`,
    },
    {
      label: "Streak",
      value: `${data.current_streak}`,
      icon: Flame,
      hint: `Best ${data.longest_streak} days`,
    },
    {
      label: "Quizzes",
      value: `${data.quizzes_completed}`,
      icon: Trophy,
      hint: "Completed sessions",
    },
    {
      label: "Attempts",
      value: `${data.total_attempts}`,
      icon: BookOpen,
      hint: "Questions answered",
    },
  ];

  return (
    <div className="space-y-8 animate-fade-up">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="section-label">Dashboard</p>
          <h1 className="mt-2 font-display text-4xl text-sand-50">
            Salam, {user?.full_name.split(" ")[0]}
          </h1>
          <p className="mt-2 text-sand-200/60">
            Your strengths, weak spots, and practice rhythm — at a glance.
          </p>
        </div>
        <Link href="/exams" className="btn-primary shrink-0">
          Start practice
          <ArrowRight size={16} />
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="panel p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm text-sand-200/55">{s.label}</p>
              <s.icon size={16} className="text-jade-400" />
            </div>
            <p className="mt-2 font-display text-3xl text-sand-50">{s.value}</p>
            <p className="mt-1 text-xs text-sand-200/45">{s.hint}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="panel p-6 lg:col-span-3">
          <div className="mb-6 flex items-center gap-2">
            <TrendingUp size={18} className="text-jade-400" />
            <h2 className="font-display text-xl">14-day activity</h2>
          </div>
          <ActivityChart data={data.recent_activity} />
          <p className="mt-3 text-xs text-sand-200/40">
            Bar height = attempts · opacity = accuracy
          </p>
        </div>

        <div className="panel p-6 lg:col-span-2">
          <h2 className="font-display text-xl">Focus next</h2>
          <p className="mt-1 text-sm text-sand-200/50">Topics with lowest mastery</p>
          <ul className="mt-5 space-y-3">
            {data.weak_topics.length === 0 && (
              <li className="text-sm text-sand-200/50">
                Take a quiz to unlock personalised focus areas.
              </li>
            )}
            {data.weak_topics.map((t) => (
              <li
                key={t.topic_id}
                className="flex items-center justify-between rounded-xl bg-white/[0.03] px-3 py-2.5"
              >
                <div>
                  <p className="text-sm font-medium text-sand-50">{t.topic_name}</p>
                  <p className="text-xs text-sand-200/45">{t.exam_name}</p>
                </div>
                <span className={`text-xs font-medium ${masteryColor(t.mastery_score)}`}>
                  {masteryLabel(t.mastery_score)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {data.topic_progress.length > 0 && (
        <div className="panel overflow-hidden">
          <div className="border-b border-white/5 px-6 py-4">
            <h2 className="font-display text-xl">Topic mastery</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead>
                <tr className="border-b border-white/5 text-sand-200/45">
                  <th className="px-6 py-3 font-medium">Topic</th>
                  <th className="px-4 py-3 font-medium">Exam</th>
                  <th className="px-4 py-3 font-medium">Accuracy</th>
                  <th className="px-4 py-3 font-medium">Mastery</th>
                </tr>
              </thead>
              <tbody>
                {data.topic_progress.map((t) => (
                  <tr key={t.topic_id} className="border-b border-white/[0.04]">
                    <td className="px-6 py-3 text-sand-50">{t.topic_name}</td>
                    <td className="px-4 py-3 text-sand-200/50">{t.exam_name}</td>
                    <td className="px-4 py-3">{t.accuracy}%</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="h-1.5 w-24 overflow-hidden rounded-full bg-white/10">
                          <div
                            className="h-full rounded-full bg-jade-500"
                            style={{ width: `${t.mastery_score * 100}%` }}
                          />
                        </div>
                        <span className={masteryColor(t.mastery_score)}>
                          {Math.round(t.mastery_score * 100)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardContent />
    </RequireAuth>
  );
}
