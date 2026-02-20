import {
  TrendingUp, Building2, BarChart3, Database, Users, Factory,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

const SKILL_ICONS: Record<string, LucideIcon> = {
  TrendingUp,
  Building2,
  BarChart3,
  Database,
  Users,
  Factory,
};

export function getSkillIcon(name: string): LucideIcon {
  return SKILL_ICONS[name] || Database;
}
