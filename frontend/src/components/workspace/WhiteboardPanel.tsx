"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Eraser, Loader2, Save } from "lucide-react";
import { api } from "@/lib/api";

type Stroke = { x: number; y: number; color: string; size: number };

export function WhiteboardPanel() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const strokes = useRef<Stroke[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [color, setColor] = useState("#4ade80");
  const [size, setSize] = useState(3);

  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#0f1419";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const list = strokes.current;
    for (let i = 1; i < list.length; i++) {
      const a = list[i - 1];
      const b = list[i];
      if (b.x < 0) continue;
      ctx.strokeStyle = b.color;
      ctx.lineWidth = b.size;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }
  }, []);

  useEffect(() => {
    api<{ canvas_data: string }>("/workspace/whiteboard")
      .then((d) => {
        try {
          strokes.current = JSON.parse(d.canvas_data || "[]");
        } catch {
          strokes.current = [];
        }
        redraw();
      })
      .finally(() => setLoading(false));
  }, [redraw]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (!rect) return;
      canvas.width = rect.width;
      canvas.height = Math.max(400, rect.height - 8);
      redraw();
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [loading, redraw]);

  function pos(e: React.MouseEvent | React.TouchEvent) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const pt = "touches" in e ? e.touches[0] : e;
    return { x: pt.clientX - rect.left, y: pt.clientY - rect.top };
  }

  function start(e: React.MouseEvent | React.TouchEvent) {
    drawing.current = true;
    const p = pos(e);
    strokes.current.push({ x: p.x, y: p.y, color, size });
  }

  function move(e: React.MouseEvent | React.TouchEvent) {
    if (!drawing.current) return;
    const p = pos(e);
    strokes.current.push({ x: p.x, y: p.y, color, size });
    redraw();
  }

  function end() {
    if (drawing.current) {
      strokes.current.push({ x: -1, y: -1, color, size });
      drawing.current = false;
    }
  }

  async function save() {
    setSaving(true);
    await api("/workspace/whiteboard", {
      method: "PUT",
      body: JSON.stringify({ canvas_data: JSON.stringify(strokes.current) }),
    });
    setSaving(false);
  }

  function clear() {
    strokes.current = [];
    redraw();
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-sand-200/50">
        <Loader2 className="animate-spin" size={24} />
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="color"
          value={color}
          onChange={(e) => setColor(e.target.value)}
          className="h-9 w-12 cursor-pointer rounded-lg border border-white/10 bg-transparent"
        />
        <input
          type="range"
          min={1}
          max={12}
          value={size}
          onChange={(e) => setSize(Number(e.target.value))}
          className="w-24"
        />
        <button type="button" onClick={save} disabled={saving} className="btn-primary text-xs">
          <Save size={14} /> {saving ? "Saving…" : "Save"}
        </button>
        <button type="button" onClick={clear} className="btn-secondary text-xs">
          <Eraser size={14} /> Clear
        </button>
        <span className="text-xs text-sand-200/40">Synced with Chat — describe your diagram there</span>
      </div>
      <div className="min-h-0 flex-1 rounded-xl border border-white/10 bg-ink-950 overflow-hidden">
        <canvas
          ref={canvasRef}
          className="h-full w-full touch-none cursor-crosshair"
          onMouseDown={start}
          onMouseMove={move}
          onMouseUp={end}
          onMouseLeave={end}
          onTouchStart={start}
          onTouchMove={move}
          onTouchEnd={end}
        />
      </div>
    </div>
  );
}
