'use client';

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { ScrollReveal } from '@/components/ui';
import type { ChartData } from '@/lib/types';

const COLORS = ['#0071E3', '#34C759', '#FF9500', '#AF52DE', '#FF3B30', '#5856D6'];

export function BudgetChart({ data }: { data: ChartData['budgetHistory'] }) {
  return (
    <ScrollReveal>
      <div className="card p-6 sm:p-8">
        <h3 className="text-lg font-semibold text-[#1D1D1F] mb-1">Budget Under Management</h3>
        <p className="text-sm text-[#86868B] mb-6">KRW Billions per month</p>
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8E8ED" vertical={false} />
              <XAxis
                dataKey="year"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#86868B' }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#86868B' }}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: '12px',
                  border: '1px solid #E8E8ED',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                  fontSize: '13px'
                }}
                formatter={(value) => [`₩${value}B`, 'Budget']}
              />
              <Bar
                dataKey="budget"
                fill="#0071E3"
                radius={[6, 6, 0, 0]}
                maxBarSize={40}
              />
            </BarChart>
          </ResponsiveContainer>
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

export function SkillChart({ data }: { data: ChartData['skillRadar'] }) {
  return (
    <ScrollReveal delay={0.2}>
      <div className="card p-6 sm:p-8">
        <h3 className="text-lg font-semibold text-[#1D1D1F] mb-1">Core Competencies</h3>
        <p className="text-sm text-[#86868B] mb-6">Proficiency level</p>
        <div className="space-y-4">
          {data.map((item) => (
            <div key={item.skill}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-[#1D1D1F]">{item.skill}</span>
                <span className="text-xs font-medium text-[#86868B]">{item.level}%</span>
              </div>
              <div className="h-2 bg-[#F5F5F7] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#0071E3] rounded-full transition-all duration-1000"
                  style={{ width: `${item.level}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </ScrollReveal>
  );
}
