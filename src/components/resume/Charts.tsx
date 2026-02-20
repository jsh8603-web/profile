'use client';

import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer
} from 'recharts';
import { ScrollReveal } from '@/components/ui';
import { GraduationCap } from 'lucide-react';
import type { ChartData } from '@/lib/types';

const COLORS = ['#0071E3', '#34C759', '#FF9500', '#AF52DE', '#FF3B30', '#5856D6'];

export function MilestoneTimeline({ data }: { data: ChartData['milestones'] }) {
  if (!data || data.length === 0) return null;
  return (
    <ScrollReveal>
      <div className="card p-6 sm:p-8">
        <h3 className="text-lg font-semibold text-[#1D1D1F] mb-1">Career Milestones</h3>
        <p className="text-sm text-[#86868B] mb-6">Key achievements across companies</p>

        {/* Desktop: Horizontal Timeline */}
        <div className="hidden lg:block">
          <div className="relative">
            {/* Horizontal connector line at dot center (h-20=80px above + 8px half-dot) */}
            <div
              className="absolute left-[8.33%] right-[8.33%] h-0.5 bg-[#E8E8ED]"
              style={{ top: '88px' }}
            />
            <div className="flex">
              {data.map((milestone, i) => {
                const isAbove = i % 2 === 0;
                return (
                  <div
                    key={milestone.year}
                    className="flex flex-col items-center"
                    style={{ width: `${100 / data.length}%` }}
                  >
                    {/* Above label (h-20 = 80px, flex-end to align bottom to line) */}
                    <div className="h-20 flex flex-col items-center justify-end pb-2 text-center px-1">
                      {isAbove && (
                        <>
                          <span className="text-xs font-bold text-[#0071E3] leading-tight">{milestone.metric}</span>
                          <p className="text-[11px] font-medium text-[#1D1D1F] mt-0.5 leading-tight">{milestone.company}</p>
                          <p className="text-[10px] text-[#86868B] mt-0.5 leading-tight">{milestone.achievement}</p>
                        </>
                      )}
                    </div>

                    {/* Dot */}
                    <div
                      className={`relative z-10 w-4 h-4 rounded-full border-2 flex items-center justify-center bg-white ${
                        milestone.isMba
                          ? 'border-[#86868B] border-dashed'
                          : 'border-[#0071E3]'
                      }`}
                    >
                      {milestone.isMba
                        ? <GraduationCap size={8} className="text-[#86868B]" />
                        : <div className="w-2 h-2 rounded-full bg-[#0071E3]" />
                      }
                    </div>

                    {/* Year */}
                    <span className="text-[10px] font-bold text-[#86868B] mt-1.5">{milestone.year}</span>

                    {/* Below label (h-20 = 80px, flex-start from top) */}
                    <div className="h-20 flex flex-col items-center justify-start pt-2 text-center px-1">
                      {!isAbove && (
                        <>
                          <span className="text-xs font-bold text-[#0071E3] leading-tight">{milestone.metric}</span>
                          <p className="text-[11px] font-medium text-[#1D1D1F] mt-0.5 leading-tight">{milestone.company}</p>
                          <p className="text-[10px] text-[#86868B] mt-0.5 leading-tight">{milestone.achievement}</p>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Mobile: Vertical Timeline */}
        <div className="lg:hidden">
          {data.map((milestone, i) => (
            <div key={milestone.year} className="flex gap-4">
              {/* Dot + vertical line */}
              <div className="flex flex-col items-center flex-shrink-0">
                <div
                  className={`w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center bg-white ${
                    milestone.isMba ? 'border-[#86868B]' : 'border-[#0071E3]'
                  }`}
                >
                  {milestone.isMba
                    ? <GraduationCap size={7} className="text-[#86868B]" />
                    : <div className="w-1.5 h-1.5 rounded-full bg-[#0071E3]" />
                  }
                </div>
                {i < data.length - 1 && (
                  <div className="w-0.5 flex-1 bg-[#E8E8ED] my-1" style={{ minHeight: '36px' }} />
                )}
              </div>

              {/* Content */}
              <div className="pb-5">
                <span className="text-[10px] font-bold text-[#86868B]">{milestone.year}</span>
                <p className="text-sm font-bold text-[#0071E3] mt-0.5">{milestone.metric}</p>
                <p className="text-sm font-medium text-[#1D1D1F]">{milestone.company}</p>
                <p className="text-xs text-[#86868B] mt-0.5">{milestone.achievement}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </ScrollReveal>
  );
}

export function IndustryChart({ data }: { data: ChartData['industryExperience'] }) {
  return (
    <ScrollReveal delay={0.1}>
      <div className="card p-6 sm:p-8">
        <h3 className="text-lg font-semibold text-[#1D1D1F] mb-1">Industry Experience</h3>
        <p className="text-sm text-[#86868B] mb-6">Years in each sector</p>
        <div className="h-[280px] flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="years"
                nameKey="name"
              >
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  borderRadius: '12px',
                  border: '1px solid #E8E8ED',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                  fontSize: '13px'
                }}
                formatter={(value) => [`${value} years`, '']}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 mt-2">
          {data.map((item, i) => (
            <div key={item.name} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
              <span className="text-xs text-[#86868B]">{item.name}</span>
            </div>
          ))}
        </div>
      </div>
    </ScrollReveal>
  );
}

export function CompetencyCards({ data }: { data: ChartData['competencyGroups'] }) {
  if (!data || data.length === 0) return null;
  const financeCore = data[0];
  const rest = data.slice(1);

  return (
    <ScrollReveal delay={0.2}>
      <div className="card p-6 sm:p-8 h-full">
        <h3 className="text-lg font-semibold text-[#1D1D1F] mb-1">Core Competencies</h3>
        <p className="text-sm text-[#86868B] mb-6">Evidence-based achievements</p>

        {/* Finance Core — full width */}
        <div>
          <p className="text-[10px] font-bold text-[#0071E3] uppercase tracking-widest mb-3">
            {financeCore.title}
          </p>
          <div className="space-y-3">
            {financeCore.items.map((item) => (
              <div key={item.label}>
                <span className="text-sm font-semibold text-[#1D1D1F]">{item.label}</span>
                <p className="text-xs text-[#86868B] mt-0.5 leading-relaxed">{item.evidence}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-[#E8E8ED] my-4" />

        {/* Technical + Leadership — 2 columns */}
        <div className="grid grid-cols-2 gap-4">
          {rest.map((group) => (
            <div key={group.title}>
              <p className="text-[10px] font-bold text-[#0071E3] uppercase tracking-widest mb-3">
                {group.title}
              </p>
              <div className="space-y-3">
                {group.items.map((item) => (
                  <div key={item.label}>
                    <span className="text-sm font-semibold text-[#1D1D1F]">{item.label}</span>
                    <p className="text-xs text-[#86868B] mt-0.5 leading-relaxed">{item.evidence}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </ScrollReveal>
  );
}
