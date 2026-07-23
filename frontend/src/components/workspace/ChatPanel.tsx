"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Bot,
  Brain,
  Download,
  FileText,
  Mic,
  MicOff,
  Paperclip,
  Send,
  User,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { api, apiForm, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

type GeneratedFile = { name: string; mime: string; data_base64: string };

type Msg = {
  role: "user" | "assistant";
  content: string;
  attachments?: string[];
  previews?: { name: string; url?: string; kind: "pdf" | "image" | "voice" }[];
  generatedImages?: string[];
  generatedFiles?: GeneratedFile[];
  sources?: { filename: string; page?: string }[];
  audioBase64?: string | null;
  audioMime?: string | null;
};

type PendingFile = { file: File; kind: "pdf" | "image"; previewUrl?: string };

type ChatApiRes = {
  reply: string;
  generated_images?: string[];
  generated_files?: GeneratedFile[];
  memory_count?: number;
  sources?: { filename: string; doc_kind?: string; page?: string }[];
  audio_base64?: string | null;
  audio_mime?: string | null;
};

const WELCOME: Msg = {
  role: "assistant",
  content:
    "Salam! **ExamAI Workspace** — chat, notes, tasks, docs & whiteboard sab connected hain.\n\n🧠 Personal memory ON · Ask me to **add a task** or **save a note** anytime.",
};

function downloadBase64File(b64: string, name: string, mime: string) {
  const link = document.createElement("a");
  link.href = `data:${mime};base64,${b64}`;
  link.download = name;
  link.click();
}

function fileKindLabel(name: string) {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "PDF";
  if (ext === "docx" || ext === "doc") return "Word";
  if (ext === "xlsx" || ext === "xls") return "Excel";
  if (ext === "pptx" || ext === "ppt") return "PowerPoint";
  return "File";
}

function renderContent(text: string) {
  return text.split("\n").map((line, i) => {
    if (!line.trim()) return <br key={i} />;
    const html = line
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
    if (line.startsWith("### "))
      return (
        <h4 key={i} className="mt-2 font-display text-base text-sand-50">
          {line.slice(4)}
        </h4>
      );
    if (line.startsWith("## "))
      return (
        <h3 key={i} className="mt-3 font-display text-lg text-sand-50">
          {line.slice(3)}
        </h3>
      );
    if (line.trim().startsWith("- ") || line.trim().startsWith("* "))
      return (
        <p
          key={i}
          className="pl-3"
          dangerouslySetInnerHTML={{ __html: `• ${html.replace(/^[-*]\s*/, "")}` }}
        />
      );
    return (
      <p key={i} className="leading-relaxed" dangerouslySetInnerHTML={{ __html: html }} />
    );
  });
}

function playBase64Audio(b64: string, mime = "audio/mpeg") {
  new Audio(`data:${mime};base64,${b64}`).play().catch(() => {});
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState<PendingFile[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [voiceReply, setVoiceReply] = useState(true);
  const [memoryCount, setMemoryCount] = useState(0);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    api<{ suggestions: string[] }>("/chat/suggestions")
      .then((d) => setSuggestions(d.suggestions))
      .catch(() => {});
    api<{ messages: { role: "user" | "assistant"; content: string }[]; memory_count: number }>(
      "/chat/history"
    )
      .then((d) => {
        setMemoryCount(d.memory_count || 0);
        if (d.messages?.length) {
          setMessages([WELCOME, ...d.messages.map((m) => ({ role: m.role, content: m.content }))]);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    return () => {
      pending.forEach((p) => p.previewUrl && URL.revokeObjectURL(p.previewUrl));
      recorderRef.current?.state === "recording" && recorderRef.current.stop();
    };
  }, [pending]);

  function addFiles(list: FileList | null) {
    if (!list?.length) return;
    setError("");
    const next: PendingFile[] = [...pending];
    for (const file of Array.from(list)) {
      if (next.length >= 4) {
        setError("Max 4 files per message");
        break;
      }
      const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
      const isImage = file.type.startsWith("image/");
      if (!isPdf && !isImage) {
        setError("Only PDF or images");
        continue;
      }
      next.push({
        file,
        kind: isPdf ? "pdf" : "image",
        previewUrl: isImage ? URL.createObjectURL(file) : undefined,
      });
    }
    setPending(next);
    if (fileRef.current) fileRef.current.value = "";
  }

  function removePending(index: number) {
    setPending((prev) => {
      const copy = [...prev];
      const [removed] = copy.splice(index, 1);
      if (removed?.previewUrl) URL.revokeObjectURL(removed.previewUrl);
      return copy;
    });
  }

  async function send(text: string, files: PendingFile[] = pending, fromVoice = false) {
    const message = text.trim();
    if ((!message && files.length === 0) || loading) return;
    setError("");
    setInput("");

    const history = messages.filter((m, i) => !(m.role === "assistant" && i === 0));
    const previews = files.map((f) => ({
      name: f.file.name,
      url: f.previewUrl,
      kind: f.kind as "pdf" | "image",
    }));
    if (fromVoice) previews.push({ name: "Voice", kind: "voice" });

    const display =
      message ||
      (fromVoice
        ? "🎤 Voice message"
        : files.length
          ? `Analyse: ${files.map((f) => f.file.name).join(", ")}`
          : "");

    setMessages((m) => [
      ...m,
      { role: "user", content: display, attachments: files.map((f) => f.kind), previews },
    ]);
    setPending([]);
    setLoading(true);

    try {
      let res: ChatApiRes;
      if (files.length > 0) {
        const form = new FormData();
        form.append("message", message);
        form.append("history", JSON.stringify(history.map(({ role, content }) => ({ role, content }))));
        form.append("voice_reply", String(voiceReply));
        files.forEach((f) => form.append("files", f.file, f.file.name));
        res = await apiForm("/chat/upload", form);
      } else {
        res = await api<ChatApiRes>("/chat/", {
          method: "POST",
          body: JSON.stringify({
            message,
            voice_reply: voiceReply,
            history: history.map(({ role, content }) => ({ role, content })),
          }),
        });
      }

      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.reply,
          generatedImages: res.generated_images,
          generatedFiles: res.generated_files,
          sources: res.sources,
          audioBase64: res.audio_base64,
          audioMime: res.audio_mime,
        },
      ]);
      if (res.memory_count != null) setMemoryCount(res.memory_count);
      if (voiceReply && res.audio_base64) playBase64Audio(res.audio_base64, res.audio_mime || "audio/mpeg");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Chat failed");
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Sorry — kuch masla aa gaya. Dubara try karein." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function toggleRecording() {
    if (recording) {
      recorderRef.current?.stop();
      return;
    }
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const rec = new MediaRecorder(stream, { mimeType: mime });
      chunksRef.current = [];
      rec.ondataavailable = (e) => e.data.size > 0 && chunksRef.current.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        const blob = new Blob(chunksRef.current, { type: mime.split(";")[0] });
        if (blob.size < 500) {
          setError("Recording too short");
          return;
        }
        setLoading(true);
        try {
          const form = new FormData();
          form.append("audio", blob, "voice.webm");
          const tr = await apiForm<{ text: string }>("/chat/transcribe", form);
          await send(tr.text, [], true);
        } catch {
          setError("Voice recognition failed");
          setLoading(false);
        }
      };
      recorderRef.current = rec;
      rec.start();
      setRecording(true);
    } catch {
      setError("Microphone access denied");
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="mb-2 flex shrink-0 items-center justify-end gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-jade-500/25 bg-jade-500/10 px-2.5 py-1 text-xs text-jade-300">
          <Brain size={12} /> Memory {memoryCount > 0 ? memoryCount : "ON"}
        </span>
        <button
          type="button"
          onClick={() => setVoiceReply((v) => !v)}
          className={cn("btn-secondary px-2 py-1 text-xs", voiceReply && "text-jade-300")}
        >
          {voiceReply ? <Volume2 size={14} /> : <VolumeX size={14} />}
        </button>
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-white/10 bg-white/[0.02]">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={cn("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}
            >
              {m.role === "assistant" && (
                <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-jade-500/20 text-jade-400">
                  <Bot size={16} />
                </div>
              )}
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl px-4 py-3 text-sm",
                  m.role === "user"
                    ? "bg-jade-500 text-ink-950"
                    : "bg-white/[0.04] text-sand-100 ring-1 ring-white/10"
                )}
              >
                {m.previews && m.previews.length > 0 && (
                  <div className="mb-2 flex flex-wrap gap-2">
                    {m.previews.map((p, j) =>
                      p.kind === "image" && p.url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img key={p.name} src={p.url} alt="" className="h-16 w-16 rounded-lg object-cover" />
                      ) : (
                        <span key={j} className="rounded-lg bg-black/10 px-2 py-1 text-xs">
                          {p.kind === "voice" ? <Mic size={12} /> : <FileText size={12} />} {p.name}
                        </span>
                      )
                    )}
                  </div>
                )}
                {m.role === "assistant" ? (
                  <div className="space-y-1">{renderContent(m.content)}</div>
                ) : (
                  m.content
                )}
                {m.generatedFiles?.map((f) => (
                  <button
                    key={f.name}
                    type="button"
                    onClick={() => downloadBase64File(f.data_base64, f.name, f.mime)}
                    className="mt-2 flex items-center gap-2 rounded-lg bg-jade-500/15 px-2 py-1 text-xs text-jade-300"
                  >
                    <Download size={12} /> {fileKindLabel(f.name)}
                  </button>
                ))}
                {m.generatedImages?.map((url, j) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img key={j} src={url} alt="" className="mt-2 max-h-64 rounded-xl" />
                ))}
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {m.sources.map((s, j) => (
                      <span
                        key={j}
                        className="rounded-md border border-white/10 px-2 py-0.5 text-[10px] text-sand-200/60"
                      >
                        📄 {s.filename}
                      </span>
                    ))}
                  </div>
                )}
                {m.audioBase64 && (
                  <button
                    type="button"
                    onClick={() => playBase64Audio(m.audioBase64!, m.audioMime || "audio/mpeg")}
                    className="mt-2 text-xs text-jade-300"
                  >
                    <Volume2 size={12} /> Play
                  </button>
                )}
              </div>
              {m.role === "user" && (
                <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/10">
                  <User size={16} />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <p className="text-sm text-sand-200/50">
              <Bot size={14} className="mr-2 inline animate-pulse" />
              Soch raha hoon…
            </p>
          )}
          <div ref={bottomRef} />
        </div>

        {messages.length <= 2 && suggestions.length > 0 && !pending.length && !recording && (
          <div className="flex flex-wrap gap-2 border-t border-white/5 px-3 py-2">
            {suggestions.slice(0, 5).map((s) => (
              <button
                key={s}
                type="button"
                disabled={loading}
                onClick={() => send(s, [])}
                className="rounded-full border border-white/10 px-3 py-1 text-xs text-sand-200/70 hover:border-jade-500/40"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {pending.length > 0 && (
          <div className="flex flex-wrap gap-2 border-t border-white/5 px-3 py-2">
            {pending.map((p, idx) => (
              <div key={idx} className="relative rounded-lg border border-white/10 px-2 py-1 pr-6 text-xs">
                {p.file.name}
                <button
                  type="button"
                  onClick={() => removePending(idx)}
                  className="absolute right-1 top-1"
                >
                  <X size={10} />
                </button>
              </div>
            ))}
          </div>
        )}

        {error && <p className="px-3 text-xs text-red-300">{error}</p>}

        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            send(input, pending);
          }}
          className="flex items-end gap-2 border-t border-white/5 p-3"
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,image/*"
            multiple
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
          <button type="button" onClick={() => fileRef.current?.click()} className="btn-secondary px-2">
            <Paperclip size={16} />
          </button>
          <button
            type="button"
            onClick={toggleRecording}
            className={cn("btn-secondary px-2", recording && "text-red-300")}
          >
            {recording ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
          <input
            className="input-field flex-1"
            placeholder="Chat, add task, create PDF…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading || recording}
          />
          <button type="submit" disabled={loading || (!input.trim() && !pending.length)} className="btn-primary px-3">
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
