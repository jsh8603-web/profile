'use client';

import { ScrollReveal } from '@/components/ui';
import type { CareerEntry } from '@/lib/types';

interface TimelineProps {
  career: CareerEntry[];
}

export default function Timeline({ career }: TimelineProps) {
  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-[19px] top-0 bottom-0 w-px bg-[#E8E8ED] hidden sm:block" />

      <div className="space-y-8">
        {career.map((job, i) => (
          <ScrollReveal key={job.company} delay={i * 0.08}>
            <div className="relative flex gap-6 sm:gap-8">
              {/* Dot */}
              <div className="hidden sm:flex items-start pt-2">
                <div className="w-[10px] h-[10px] rounded-full bg-[#0071E3] ring-4 ring-[#EBF5FF] z-10 shrink-0" />
              </div>

              {/* Content */}
              <div className="card p-6 sm:p-8 flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2 mb-4">
                  <div>
                    <h3 className="text-xl sm:text-2xl font-bold text-[#1D1D1F]">
                      {job.company}
                    </h3>
                    <p className="text-sm text-[#86868B] mt-0.5">
                      {job.division} · {job.role}
                    </p>
                  </div>
                  <span className="text-xs font-medium text-[#0071E3] bg-[#0071E3]/10 px-3 py-1 rounded-full whitespace-nowrap">
                    {job.period}
                  </span>
                </div>

                <ul className="space-y-2">
                  {job.highlights.map((h, j) => (
                    <li key={j} className="flex gap-2.5 text-sm text-[#424245] leading-relaxed">
                      <span className="text-[#0071E3] mt-1.5 shrink-0">•</span>
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </ScrollReveal>
        ))}
      </div>
    </div>
  );
}
