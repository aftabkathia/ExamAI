"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Flame, LayoutDashboard, LogOut, BookOpen, Menu, X, NotebookPen, ScrollText, FileStack, Bot } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/exams", label: "Practice", icon: BookOpen },
  { href: "/workspace", label: "Workspace", icon: Bot },
  { href: "/notes", label: "Notes", icon: NotebookPen },
  { href: "/essays", label: "Essays", icon: ScrollText },
  { href: "/past-papers", label: "Papers", icon: FileStack },
];

export function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-ink-950/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href={user ? "/dashboard" : "/"} className="group flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-jade-500/20 text-jade-400 ring-1 ring-jade-500/30 transition group-hover:bg-jade-500/30">
            <BookOpen className="h-4.5 w-4.5" size={18} />
          </span>
          <span className="font-display text-xl tracking-tight text-sand-50">
            Exam<span className="text-jade-400">AI</span>
          </span>
        </Link>

        {user ? (
          <>
            <nav className="hidden items-center gap-1 md:flex">
              {links.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition",
                    pathname.startsWith(href)
                      ? "bg-white/10 text-sand-50"
                      : "text-sand-200/60 hover:bg-white/5 hover:text-sand-100"
                  )}
                >
                  <Icon size={16} />
                  {label}
                </Link>
              ))}
            </nav>

            <div className="hidden items-center gap-4 md:flex">
              <div className="flex items-center gap-1.5 rounded-full bg-ember-500/15 px-3 py-1 text-sm text-ember-400 ring-1 ring-ember-500/20">
                <Flame size={14} />
                <span className="font-medium">{user.current_streak}</span>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-sand-50">{user.full_name}</p>
                <p className="text-xs text-sand-200/50">{user.email}</p>
              </div>
              <button
                onClick={logout}
                className="rounded-lg p-2 text-sand-200/50 transition hover:bg-white/5 hover:text-sand-100"
                title="Log out"
              >
                <LogOut size={18} />
              </button>
            </div>

            <button
              className="rounded-lg p-2 text-sand-100 md:hidden"
              onClick={() => setOpen(!open)}
              aria-label="Menu"
            >
              {open ? <X size={22} /> : <Menu size={22} />}
            </button>
          </>
        ) : (
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm text-sand-200/70 transition hover:text-sand-50"
            >
              Log in
            </Link>
            <Link
              href="/register"
              className="rounded-full bg-jade-500 px-4 py-2 text-sm font-medium text-ink-950 transition hover:bg-jade-400"
            >
              Get started
            </Link>
          </div>
        )}
      </div>

      {user && open && (
        <div className="border-t border-white/5 px-4 py-4 md:hidden">
          <nav className="flex flex-col gap-1">
            {links.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm",
                  pathname.startsWith(href)
                    ? "bg-white/10 text-sand-50"
                    : "text-sand-200/70"
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}
            <button
              onClick={() => {
                setOpen(false);
                logout();
              }}
              className="mt-2 flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-red-400"
            >
              <LogOut size={16} />
              Log out
            </button>
          </nav>
        </div>
      )}
    </header>
  );
}
