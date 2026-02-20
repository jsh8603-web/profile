'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Edit } from 'lucide-react';
import { Skeleton } from '@/components/ui';
import { getSkills } from '@/lib/firebase/firestore';
import { initialSkills } from '@/data/skills';
import type { SkillDetail } from '@/lib/types';

export default function AdminSkillsPage() {
  const [skills, setSkills] = useState<SkillDetail[]>(initialSkills);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSkills()
      .then((data) => {
        if (data.length > 0) setSkills(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">Skills</h1>
          <p className="text-sm text-[#86868B] mt-1">Edit skill detail pages</p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {skills.map((skill) => (
            <div
              key={skill.slug}
              className="card-flat p-5 flex items-center justify-between gap-4"
            >
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-[#1D1D1F]">
                  {skill.label}
                </h3>
                <p className="text-xs text-[#86868B] mt-0.5 truncate">
                  {skill.summary}
                </p>
                <p className="text-xs text-[#86868B] mt-1">
                  {skill.relatedCareers.length} related careers · {skill.keyAchievements.length} achievements
                </p>
              </div>
              <Link
                href={`/admin/skills/${skill.slug}/edit`}
                className="shrink-0 p-2 rounded-lg hover:bg-[#F5F5F7] transition-colors"
              >
                <Edit size={16} className="text-[#86868B]" />
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
