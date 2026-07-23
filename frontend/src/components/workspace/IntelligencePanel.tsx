"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  FileSearch,
  Loader2,
  Search,
  Trash2,
  Upload,
} from "lucide-react";
import { api, apiForm } from "@/lib/api";
import { cn } from "@/lib/utils";

type DocItem = {
  id: number;
  filename: string;
  title: string;
  doc_kind: string;
  page_count: number;
  uploaded_at: string;
};

type Stats = {
  total_documents: number;
  total_chunks: number;
  by_kind: Record<string, number>;
};

type AskResult = {
  answer: string;
  sources: { filename: string; doc_kind: string; page: string }[];
  documents_searched: number;
  matches_found: number;
};

const EXAMPLES = [
  "Find all invoices from April",
  "Which contracts mention late payment?",
  "List documents about payment terms",
  "Show invoices over 50,000",
];

export function IntelligencePanel() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState<AskResult | null>(null);
  const [uploadMsg, setUploadMsg] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    api<{ stats: Stats; documents: DocItem[] }>("/doc-intel/library")
      .then((d) => {
        setStats(d.stats);
        setDocs(d.documents);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onUpload(files: FileList | null) {
    if (!files?.length) return;
    setUploading(true);
    setUploadMsg("");
    const form = new FormData();
    Array.from(files).forEach((f) => form.append("files", f, f.name));
    try {
      const res = await apiForm<{
        added: string[];
        skipped_duplicates: string[];
        errors: string[];
        stats: Stats;
      }>("/doc-intel/upload", form);
      setStats(res.stats);
      setUploadMsg(
        `Added ${res.added.length} PDFs` +
          (res.skipped_duplicates.length
            ? ` · ${res.skipped_duplicates.length} duplicates skipped`
            : "") +
          (res.errors.length ? ` · ${res.errors.length} errors` : "")
      );
      load();
    } catch {
      setUploadMsg("Upload failed — check file size (max 12MB each) and format (PDF only)");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function ask(q?: string) {
    const text = (q || question).trim();
    if (!text) return;
    setQuestion(text);
    setAsking(true);
    setAnswer(null);
    try {
      const res = await api<AskResult>("/doc-intel/ask", {
        method: "POST",
        body: JSON.stringify({ question: text }),
      });
      setAnswer(res);
    } catch {
      setAnswer({
        answer: "Search failed. Upload PDFs first, then try again.",
        sources: [],
        documents_searched: 0,
        matches_found: 0,
      });
    } finally {
      setAsking(false);
    }
  }

  async function remove(id: number) {
    await api(`/doc-intel/library/${id}`, { method: "DELETE" });
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
    <div className="flex h-full min-h-0 flex-col gap-4 lg:flex-row">
      <div className="flex w-full shrink-0 flex-col gap-3 lg:w-72">
        <div
          className={cn(
            "rounded-xl border border-dashed border-jade-500/30 bg-jade-500/5 p-4 text-center",
            uploading && "opacity-60"
          )}
        >
          <FileSearch className="mx-auto mb-2 text-jade-400" size={28} />
          <p className="text-sm font-medium text-sand-100">Upload PDF library</p>
          <p className="mt-1 text-xs text-sand-200/50">
            Up to 50 PDFs per batch · 500 total · invoices, contracts, reports
          </p>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,application/pdf"
            multiple
            className="hidden"
            onChange={(e) => onUpload(e.target.files)}
          />
          <button
            type="button"
            disabled={uploading}
            onClick={() => fileRef.current?.click()}
            className="btn-primary mx-auto mt-3 flex items-center gap-2 text-xs"
          >
            <Upload size={14} />
            {uploading ? "Indexing…" : "Choose PDFs"}
          </button>
          {uploadMsg && <p className="mt-2 text-xs text-jade-300">{uploadMsg}</p>}
        </div>

        {stats && (
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-xs text-sand-200/60">
            <p>
              <strong className="text-sand-100">{stats.total_documents}</strong> documents ·{" "}
              <strong className="text-sand-100">{stats.total_chunks}</strong> searchable chunks
            </p>
            {Object.keys(stats.by_kind).length > 0 && (
              <p className="mt-1">
                {Object.entries(stats.by_kind)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(" · ")}
              </p>
            )}
          </div>
        )}

        <div className="min-h-0 flex-1 overflow-y-auto rounded-xl border border-white/10">
          {docs.length === 0 ? (
            <p className="p-4 text-xs text-sand-200/40">No PDFs yet</p>
          ) : (
            docs.slice(0, 80).map((d) => (
              <div
                key={d.id}
                className="flex items-center gap-2 border-b border-white/5 px-3 py-2 text-xs last:border-0"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sand-100">{d.filename}</p>
                  <p className="text-sand-200/40">
                    {d.doc_kind} · {d.page_count}p
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => remove(d.id)}
                  className="shrink-0 text-sand-200/30 hover:text-red-300"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))
          )}
          {docs.length > 80 && (
            <p className="p-2 text-center text-[10px] text-sand-200/30">
              +{docs.length - 80} more
            </p>
          )}
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="flex gap-2">
          <input
            className="input-field flex-1"
            placeholder='Ask: "Find all invoices from April"'
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            disabled={asking}
          />
          <button
            type="button"
            onClick={() => ask()}
            disabled={asking || !question.trim()}
            className="btn-primary shrink-0 px-4"
          >
            {asking ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => ask(ex)}
              className="rounded-full border border-white/10 px-3 py-1 text-xs text-sand-200/60 hover:border-jade-500/40"
            >
              {ex}
            </button>
          ))}
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto rounded-xl border border-white/10 bg-white/[0.02] p-4">
          {!answer && !asking && (
            <p className="text-sm text-sand-200/50">
              Upload your business PDFs, then ask natural questions. Also works from{" "}
              <strong>Chat</strong> — e.g. &quot;Which contracts mention late payment?&quot;
            </p>
          )}
          {asking && (
            <p className="text-sm text-sand-200/50">
              <Loader2 size={14} className="mr-2 inline animate-spin" />
              Searching {stats?.total_documents || 0} documents…
            </p>
          )}
          {answer && (
            <div className="space-y-4">
              <div className="prose prose-invert max-w-none text-sm text-sand-100 whitespace-pre-wrap">
                {answer.answer}
              </div>
              <p className="text-xs text-sand-200/40">
                Searched {answer.documents_searched} docs · {answer.matches_found} matches
              </p>
              {answer.sources.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wider text-sand-200/40">
                    Sources
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {answer.sources.map((s, i) => (
                      <span
                        key={i}
                        className="rounded-lg border border-white/10 bg-white/[0.04] px-2 py-1 text-xs text-sand-200/70"
                      >
                        {s.filename} {s.page && `· ${s.page}`}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
