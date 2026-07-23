"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

type Note = {
  id: number;
  title: string;
  content: string;
  source: string;
};

export function NotesPanel() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [selected, setSelected] = useState<Note | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api<Note[]>("/workspace/notes")
      .then(setNotes)
      .catch(() => setError("Could not load notes"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function save() {
    if (!title.trim() || !content.trim()) return;
    setError("");
    try {
      if (selected) {
        await api(`/workspace/notes/${selected.id}`, {
          method: "PATCH",
          body: JSON.stringify({ title, content }),
        });
      } else {
        await api("/workspace/notes", {
          method: "POST",
          body: JSON.stringify({ title, content }),
        });
      }
      setTitle("");
      setContent("");
      setSelected(null);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Save failed");
    }
  }

  async function remove(id: number) {
    await api(`/workspace/notes/${id}`, { method: "DELETE" });
    if (selected?.id === id) {
      setSelected(null);
      setTitle("");
      setContent("");
    }
    load();
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-sand-200/50">
        <Loader2 className="animate-spin" size={24} />
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 gap-4">
      <div className="w-56 shrink-0 space-y-2 overflow-y-auto">
        <button
          type="button"
          onClick={() => {
            setSelected(null);
            setTitle("");
            setContent("");
          }}
          className="btn-primary flex w-full items-center justify-center gap-2 text-xs"
        >
          <Plus size={14} /> New note
        </button>
        {notes.map((n) => (
          <button
            key={n.id}
            type="button"
            onClick={() => {
              setSelected(n);
              setTitle(n.title);
              setContent(n.content);
            }}
            className={cn(
              "w-full rounded-xl border px-3 py-2 text-left text-xs transition",
              selected?.id === n.id
                ? "border-jade-500/40 bg-jade-500/10 text-sand-50"
                : "border-white/10 bg-white/[0.03] text-sand-200/70 hover:border-white/20"
            )}
          >
            <p className="truncate font-medium">{n.title}</p>
            {n.source === "chat" && (
              <span className="text-[10px] text-jade-400">from chat</span>
            )}
          </button>
        ))}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <input
          className="input-field"
          placeholder="Note title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          className="input-field min-h-[280px] flex-1 resize-none font-mono text-sm"
          placeholder="Write notes… (also auto-saved from chat)"
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
        <div className="flex gap-2">
          <button type="button" onClick={save} className="btn-primary text-xs">
            {selected ? "Update" : "Save"} note
          </button>
          {selected && (
            <button
              type="button"
              onClick={() => remove(selected.id)}
              className="btn-secondary text-xs text-red-300"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
        {error && <p className="text-xs text-red-300">{error}</p>}
      </div>
    </div>
  );
}
