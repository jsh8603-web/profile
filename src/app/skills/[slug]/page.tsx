'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowLeft, Briefcase, Trophy, Wrench } from 'lucide-react';
import { Skeleton } from '@/components/ui';
import { getSkill } from '@/lib/firebase/firestore';
import { getSkillIcon } from '@/lib/utils/icons';
import { initialSkills } from '@/data/skills';
import type { SkillDetail } from '@/lib/types';

export default function SkillDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [skill, setSkill] = useState<SkillDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;

    getSkill(slug)
      .then((data) => {
        setSkill(data || initialSkills.find(s => s.slug === slug) || null);
      })
      .catch(() => {
        setSkill(initialSkills.find(s => s.slug === slug) || null);
      })
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="section-padding">
        <div className="max-w-4xl mx-auto px-5 sm:px-8">
          <Skeleton className="h-6 w-32 mb-8" />
          <Skeleton className="h-10 w-64 mb-4" />
          <Skeleton className="h-20 w-full mb-8" />
          <Skeleton className="h-48 w-full mb-4" />
          <Skeleton className="h-48 w-full" />
        </div>
      </div>
    );
  }

  if (!skill) {
    return (
      <div className="section-padding text-center">
        <h1 className="text-2xl font-bold text-[#1D1D1F]">Skill not found</h1>
        <p className="mt-2 text-[#86868B]">The skill you&apos;re looking for doesn&apos;t exist.</p>
        <Link href="/" className="mt-4 inline-block text-[#0071E3] font-medium hover:underline">
          Back to Home
        </Link>
      </div>
    );
  }

  const Icon = getSkillIcon(skill.icon);

  return (
    <div className="section-padding">
      <div className="max-w-4xl mx-auto px-5 sm:px-8">
        {/* Back link */}
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-[#86868B] hover:text-[#0071E3] transition-colors mb-8"
          >
            <ArrowLeft size={16} />
            Back
          </Link>
        </motion.div>

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-[#0071E3]/10 flex items-center justify-center">
              <Icon size={24} className="text-[#0071E3]" />
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-[#1D1D1F]">
              {skill.label}
            </h1>
          </div>
          <p className="text-base text-[#424245] leading-relaxed max-w-3xl mt-4">
            {skill.description}
          </p>
        </motion.div>

        {/* Related Careers */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mt-12"
        >
          <div className="flex items-center gap-2 mb-6">
            <Briefcase size={18} className="text-[#86868B]" />
            <h2 className="text-lg font-semibold text-[#1D1D1F]">Related Experience</h2>
          </div>
          <div className="space-y-4">
            {skill.relatedCareers.map((career, i) => (
              <div key={i} className="card-flat p-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-3">
                  <h3 className="text-sm font-semibold text-[#1D1D1F]">{career.company}</h3>
                  <span className="text-xs text-[#86868B]">{career.period}</span>
                </div>
                <p className="text-xs font-medium text-[#0071E3] mb-2">{career.role}</p>
                <p className="text-sm text-[#424245] leading-relaxed">{career.description}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Key Achievements */}
        {skill.keyAchievements.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-12"
          >
            <div className="flex items-center gap-2 mb-6">
              <Trophy size={18} className="text-[#86868B]" />
              <h2 className="text-lg font-semibold text-[#1D1D1F]">Key Achievements</h2>
            </div>
            <div className="card-flat p-6">
              <ul className="space-y-3">
                {skill.keyAchievements.map((achievement, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#0071E3] mt-2 shrink-0" />
                    <span className="text-sm text-[#424245] leading-relaxed">{achievement}</span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        )}

        {/* Tools */}
        {skill.tools.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-12"
          >
            <div className="flex items-center gap-2 mb-6">
              <Wrench size={18} className="text-[#86868B]" />
              <h2 className="text-lg font-semibold text-[#1D1D1F]">Tools & Skills</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {skill.tools.map((tool) => (
                <span
                  key={tool}
                  className="px-3 py-1.5 rounded-full text-xs font-medium bg-[#F5F5F7] text-[#424245] border border-[#E8E8ED]"
                >
                  {tool}
                </span>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
