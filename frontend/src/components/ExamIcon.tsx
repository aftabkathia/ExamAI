import {
  Landmark,
  HeartPulse,
  Cpu,
  GraduationCap,
  ClipboardList,
  Building2,
  Scale,
  Briefcase,
  BookOpen,
  type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  landmark: Landmark,
  "heart-pulse": HeartPulse,
  cpu: Cpu,
  "graduation-cap": GraduationCap,
  "clipboard-list": ClipboardList,
  "building-2": Building2,
  scale: Scale,
  briefcase: Briefcase,
  book: BookOpen,
};

export function ExamIcon({ name, size = 22 }: { name: string; size?: number }) {
  const Icon = ICONS[name] || BookOpen;
  return <Icon size={size} />;
}
