"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { GoogleSignInButton } from "@/components/GoogleSignIn";
import { ApiError } from "@/lib/api";

export default function RegisterPage() {
  const { register, user, loading } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(fullName, email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col justify-center py-8 animate-fade-up">
      <div className="text-center">
        <p className="section-label">Get started</p>
        <h1 className="mt-3 font-display text-4xl text-sand-50">Create account</h1>
        <p className="mt-2 text-sand-200/60">
          Save progress across devices and unlock adaptive practice.
        </p>
      </div>

      <form onSubmit={onSubmit} className="panel mt-8 space-y-4 p-6 sm:p-8">
        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}
        <div>
          <label className="mb-1.5 block text-sm text-sand-200/70">Full name</label>
          <input
            type="text"
            required
            minLength={2}
            className="input-field"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Ali Khan"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm text-sand-200/70">Email</label>
          <input
            type="email"
            required
            className="input-field"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm text-sand-200/70">Password</label>
          <input
            type="password"
            required
            minLength={6}
            className="input-field"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 6 characters"
          />
        </div>
        <button type="submit" disabled={submitting} className="btn-primary w-full">
          {submitting ? "Creating…" : "Create account"}
        </button>

        <div className="relative py-2 text-center text-xs text-sand-200/40">
          <span className="relative z-10 bg-ink-900 px-3">or</span>
          <div className="absolute inset-x-0 top-1/2 h-px bg-white/10" />
        </div>
        <GoogleSignInButton />
      </form>

      <p className="mt-6 text-center text-sm text-sand-200/55">
        Already registered?{" "}
        <Link href="/login" className="text-jade-400 hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
