import { Timestamp } from 'firebase/firestore';

export interface Post {
  id: string;
  slug: string;
  title: string;
  excerpt: string;
  content: string;
  category: 'finance' | 'economy';
  tags: string[];
  coverImageUrl: string;
  published: boolean;
  authorName: string;
  commentCount: number;
  viewCount: number;
  createdAt: Timestamp;
  updatedAt: Timestamp;
  publishedAt: Timestamp | null;
  attachmentUrl?: string;
  attachmentName?: string;
}

export interface Comment {
  id: string;
  content: string;
  authorId: string;
  authorName: string;
  authorPhotoUrl: string;
  createdAt: Timestamp;
}

export interface CareerEntry {
  period: string;
  company: string;
  division: string;
  role: string;
  highlights: string[];
}

export interface Education {
  period: string;
  school: string;
  degree: string;
  gpa: string;
}

export interface Competency {
  label: string;
  detail: string;
}

export interface StatItem {
  number: string;
  label: string;
}

export interface Milestone {
  year: string;
  company: string;
  metric: string;
  achievement: string;
  isMba?: boolean;
}

export interface CompetencyGroup {
  title: string;
  items: { label: string; evidence: string }[];
}

export interface ChartData {
  milestones: Milestone[];
  industryExperience: { name: string; years: number }[];
  competencyGroups: CompetencyGroup[];
}

export interface ContactInfo {
  email: string;
  phone: string;
  location: string;
  linkedin: string;
}

export interface Profile {
  name: string;
  title: string;
  tagline: string;
  bio: string;
  photoUrl: string;
  stats: StatItem[];
  career: CareerEntry[];
  competencies: Competency[];
  education: Education[];
  chartData: ChartData;
  contact: ContactInfo;
}

export interface RelatedCareer {
  company: string;
  period: string;
  role: string;
  description: string;
}

export interface SkillDetail {
  slug: string;
  label: string;
  icon: string;
  summary: string;
  description: string;
  relatedCareers: RelatedCareer[];
  keyAchievements: string[];
  tools: string[];
}
