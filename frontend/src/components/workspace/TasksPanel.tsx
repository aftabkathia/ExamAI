"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Circle, Loader2, Plus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Task = {
  id: number;
  title: string;
  description: string;
  status: "todo" | "doing" | "done";
  priority: "low" | "medium" | "high";
};

const STATUS_CYCLE: Task["status"][] = ["todo", "doing", "done"];

export function TasksPanel() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const load = useCallback(() => {
    api<Task[]>("/workspace/tasks")
      .then(setTasks)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function addTask() {
    if (!title.trim()) return;
    await api("/workspace/tasks", {
      method: "POST",
      body: JSON.stringify({ title, description, status: "todo", priority: "medium" }),
    });
    setTitle("");
    setDescription("");
    load();
  }

  async function cycleStatus(task: Task) {
    const idx = STATUS_CYCLE.indexOf(task.status);
    const next = STATUS_CYCLE[(idx + 1) % STATUS_CYCLE.length];
    await api(`/workspace/tasks/${task.id}`, {
      method: "PATCH",
      body: JSON.stringify({ ...task, status: next }),
    });
    load();
  }

  async function remove(id: number) {
    await api(`/workspace/tasks/${id}`, { method: "DELETE" });
    load();
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-sand-200/50">
        <Loader2 className="animate-spin" size={24} />
      </div>
    );
  }

  const open = tasks.filter((t) => t.status !== "done");
  const done = tasks.filter((t) => t.status === "done");

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <div className="flex gap-2">
        <input
          className="input-field flex-1"
          placeholder="New task title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addTask()}
        />
        <button type="button" onClick={addTask} className="btn-primary shrink-0 px-3">
          <Plus size={16} />
        </button>
      </div>
      <input
        className="input-field text-sm"
        placeholder="Description (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto">
        <section>
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-sand-200/40">
            Open ({open.length})
          </h3>
          <div className="space-y-2">
            {open.map((t) => (
              <TaskRow key={t.id} task={t} onCycle={() => cycleStatus(t)} onDelete={() => remove(t.id)} />
            ))}
            {!open.length && (
              <p className="text-sm text-sand-200/40">No open tasks — add from chat or above.</p>
            )}
          </div>
        </section>
        {done.length > 0 && (
          <section>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-sand-200/40">
              Done ({done.length})
            </h3>
            <div className="space-y-2 opacity-60">
              {done.map((t) => (
                <TaskRow key={t.id} task={t} onCycle={() => cycleStatus(t)} onDelete={() => remove(t.id)} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

function TaskRow({
  task,
  onCycle,
  onDelete,
}: {
  task: Task;
  onCycle: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2">
      <button type="button" onClick={onCycle} className="mt-0.5 shrink-0 text-jade-400">
        {task.status === "done" ? <CheckCircle2 size={18} /> : <Circle size={18} />}
      </button>
      <div className="min-w-0 flex-1">
        <p className={cn("text-sm", task.status === "done" && "line-through text-sand-200/50")}>
          {task.title}
        </p>
        {task.description && (
          <p className="mt-0.5 text-xs text-sand-200/50">{task.description}</p>
        )}
        <span className="mt-1 inline-block text-[10px] uppercase text-sand-200/30">
          {task.status} · {task.priority}
        </span>
      </div>
      <button type="button" onClick={onDelete} className="shrink-0 text-sand-200/30 hover:text-red-300">
        <Trash2 size={14} />
      </button>
    </div>
  );
}
