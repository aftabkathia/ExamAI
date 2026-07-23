"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, FileText, Loader2, Trash2 } from "lucide-react";
import { api } from "@/lib/api";

type DocMeta = {
  id: number;
  title: string;
  filename: string;
  mime: string;
  source: string;
  created_at: string;
};

function downloadBase64(b64: string, name: string, mime: string) {
  const link = document.createElement("a");
  link.href = `data:${mime};base64,${b64}`;
  link.download = name;
  link.click();
}

export function DocumentsPanel() {
  const [docs, setDocs] = useState<DocMeta[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    api<DocMeta[]>("/workspace/documents")
      .then(setDocs)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function download(id: number, filename: string) {
    const full = await api<{ data_base64: string; mime: string }>(`/workspace/documents/${id}`);
    downloadBase64(full.data_base64, filename, full.mime);
  }

  async function remove(id: number) {
    await api(`/workspace/documents/${id}`, { method: "DELETE" });
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
    <div className="h-full overflow-y-auto">
      {docs.length === 0 ? (
        <p className="text-sm text-sand-200/50">
          No documents yet. Ask in <strong>Chat</strong> to create PDF, Word, Excel, or PowerPoint
          files — they appear here automatically.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {docs.map((d) => (
            <div
              key={d.id}
              className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-4"
            >
              <FileText className="shrink-0 text-jade-400" size={28} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-sand-50">{d.title}</p>
                <p className="truncate text-xs text-sand-200/50">{d.filename}</p>
                <p className="text-[10px] text-sand-200/30">{d.source}</p>
              </div>
              <div className="flex shrink-0 flex-col gap-1">
                <button
                  type="button"
                  onClick={() => download(d.id, d.filename)}
                  className="rounded-lg bg-jade-500/15 p-2 text-jade-300 hover:bg-jade-500/25"
                >
                  <Download size={14} />
                </button>
                <button
                  type="button"
                  onClick={() => remove(d.id)}
                  className="rounded-lg p-2 text-sand-200/30 hover:bg-red-500/10 hover:text-red-300"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
