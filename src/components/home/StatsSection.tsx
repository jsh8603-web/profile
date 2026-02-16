'use client';

import { ScrollReveal } from '@/components/ui';

const STATS = [
  { number: '11+', label: 'Years of Experience', desc: 'In FP&A and Finance' },
  { number: '₩60B', label: 'Monthly Budget', desc: 'Managed at Coupang' },
  { number: '5', label: 'Industries', desc: 'Logistics to Energy' },
  { number: '4', label: 'Team Members', desc: 'Direct reports led' },
];

export default function StatsSection() {
  return (
    <section className="section-padding bg-white">
      <div className="max-w-6xl mx-auto px-5 sm:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          {STATS.map((stat, i) => (
            <ScrollReveal key={stat.label} delay={i * 0.1}>
              <div className="text-center p-6 sm:p-8">
                <div className="stat-number text-4xl sm:text-5xl text-[#1D1D1F]">
                  {stat.number}
                </div>
                <div className="mt-2 text-sm font-semibold text-[#1D1D1F]">
                  {stat.label}
                </div>
                <div className="mt-1 text-xs text-[#86868B]">
                  {stat.desc}
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
