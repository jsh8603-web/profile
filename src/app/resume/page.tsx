'use client';

import { useEffect, useState } from 'react';
import { ScrollReveal } from '@/components/ui';
import Timeline from '@/components/resume/Timeline';
import { BudgetChart, IndustryChart, SkillChart } from '@/components/resume/Charts';
import { getProfile } from '@/lib/firebase/firestore';
import { initialProfile } from '@/data/resume';
import type { Profile } from '@/lib/types';
import { GraduationCap } from 'lucide-react';

export default function ResumePage() {
  const [profile, setProfile] = useState<Profile>(initialProfile);

  useEffect(() => {
    getProfile()
      .then((data) => { if (data) setProfile(data); })
      .catch(() => {});
  }, []);

  return (
    <div className="section-padding">
      <div className="max-w-6xl mx-auto px-5 sm:px-8">
        {/* Header */}
        <ScrollReveal>
          <p className="section-label mb-4">Resume</p>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-[#1D1D1F] leading-tight">
            Career Journey
          </h1>
          <p className="mt-4 text-lg text-[#86868B] max-w-2xl">
            {profile.tagline}
          </p>
        </ScrollReveal>

        {/* Experience Timeline */}
        <div className="mt-16">
          <ScrollReveal>
            <h2 className="text-2xl font-bold text-[#1D1D1F] mb-8">Experience</h2>
          </ScrollReveal>
          <Timeline career={profile.career} />
        </div>

        {/* Charts Section */}
        <div className="mt-20">
          <ScrollReveal>
            <h2 className="text-2xl font-bold text-[#1D1D1F] mb-8">At a Glance</h2>
          </ScrollReveal>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <BudgetChart data={profile.chartData.budgetHistory} />
            <IndustryChart data={profile.chartData.industryExperience} />
          </div>
          <div className="mt-6">
            <SkillChart data={profile.chartData.skillRadar} />
          </div>
        </div>

        {/* Education */}
        <div className="mt-20">
          <ScrollReveal>
            <h2 className="text-2xl font-bold text-[#1D1D1F] mb-8">Education</h2>
          </ScrollReveal>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {profile.education.map((edu, i) => (
              <ScrollReveal key={edu.school} delay={i * 0.1}>
                <div className="card p-6 sm:p-8 h-full">
                  <div className="flex items-start justify-between">
                    <GraduationCap size={24} className="text-[#0071E3]" />
                    <span className="text-xs font-medium text-[#0071E3] bg-[#0071E3]/10 px-3 py-1 rounded-full">
                      {edu.period}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-[#1D1D1F] mt-4">
                    {edu.school}
                  </h3>
                  <p className="text-sm text-[#86868B] mt-1">{edu.degree}</p>
                  <div className="mt-4 flex items-baseline gap-1">
                    <span className="text-2xl font-bold text-[#1D1D1F]">{edu.gpa.split(' ')[0]}</span>
                    <span className="text-sm text-[#86868B]">/ {edu.gpa.split('/ ')[1]}</span>
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
