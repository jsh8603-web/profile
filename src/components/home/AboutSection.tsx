'use client';

import Link from 'next/link';
import { ScrollReveal } from '@/components/ui';
import {
  TrendingUp, Building2, BarChart3, Database, Users, Factory
} from 'lucide-react';

const COMPETENCIES = [
  {
    icon: TrendingUp,
    label: 'FP&A',
    slug: 'fpa',
    detail: 'Budgeting, forecasting, variance analysis, cost modeling'
  },
  {
    icon: Building2,
    label: 'Project Financing',
    slug: 'project-financing',
    detail: 'PF structuring, global banks, ECAs, deal documentation'
  },
  {
    icon: BarChart3,
    label: 'Valuation & M&A',
    slug: 'valuation-ma',
    detail: 'Financial modeling, FDD, investment appraisal, ROI/CAPEX'
  },
  {
    icon: Database,
    label: 'Systems',
    slug: 'systems',
    detail: 'SAP, SQL, BI dashboards, advanced Excel modeling'
  },
  {
    icon: Users,
    label: 'Leadership',
    slug: 'leadership',
    detail: 'Team of 4, cross-functional partnering, C-suite reporting'
  },
  {
    icon: Factory,
    label: 'Industries',
    slug: 'industries',
    detail: 'Logistics, Construction, Manufacturing, Petrochemical, Energy'
  },
];

export default function AboutSection() {
  return (
    <section id="about" className="section-padding">
      <div className="max-w-6xl mx-auto px-5 sm:px-8">
        <ScrollReveal>
          <p className="section-label mb-4">About</p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-[#1D1D1F] leading-tight max-w-2xl">
            Bridging operational complexity with{' '}
            <span className="text-[#0071E3]">financial precision.</span>
          </h2>
        </ScrollReveal>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-12">
          <ScrollReveal delay={0.1}>
            <p className="text-base text-[#424245] leading-relaxed">
              Specializing in FP&A and financial modeling with deep expertise in project
              financing and valuation. Proven track record of building cost models that
              transform how operations teams think about efficiency — from Coupang&apos;s
              logistics network to Hyundai&apos;s global plant financing.
            </p>
            <p className="mt-4 text-base text-[#424245] leading-relaxed">
              KAIST MBA with hands-on experience across SAP, SQL, and BI tools.
              Comfortable reporting to C-suite and partnering cross-functionally
              with operational leaders.
            </p>
          </ScrollReveal>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {COMPETENCIES.map((comp, i) => (
              <ScrollReveal key={comp.label} delay={0.1 + i * 0.05}>
                <Link href={`/skills/${comp.slug}`} className="block h-full">
                  <div className="card p-5 h-full">
                    <comp.icon size={20} className="text-[#0071E3] mb-3" />
                    <div className="text-sm font-semibold text-[#1D1D1F]">
                      {comp.label}
                    </div>
                    <div className="text-xs text-[#86868B] mt-1 leading-relaxed">
                      {comp.detail}
                    </div>
                  </div>
                </Link>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
