import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function masteryLabel(score: number) {
  if (score >= 0.8) return "Mastered";
  if (score >= 0.6) return "Strong";
  if (score >= 0.4) return "Building";
  return "Needs focus";
}

export function masteryColor(score: number) {
  if (score >= 0.8) return "text-jade-400";
  if (score >= 0.6) return "text-jade-300";
  if (score >= 0.4) return "text-ember-400";
  return "text-red-400";
}
