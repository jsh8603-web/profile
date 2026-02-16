import type { Profile } from '../lib/types';

export const initialProfile: Profile = {
  name: 'Sehoon Jang',
  title: 'Senior FP&A Manager',
  tagline: 'Bridging operational complexity with financial precision.',
  bio: 'Specializing in FP&A and financial modeling with deep expertise in project financing and valuation. Proven track record of building cost models that transform how operations teams think about efficiency — from Coupang\'s logistics network to Hyundai\'s global plant financing. KAIST MBA with hands-on experience across SAP, SQL, and BI tools.',
  photoUrl: '',
  stats: [
    { number: '11+', label: 'Years Experience' },
    { number: '60B', label: 'KRW Monthly Budget' },
    { number: '5', label: 'Industries Covered' },
    { number: '4', label: 'Team Members' },
  ],
  career: [
    {
      period: '2023.01 — Present',
      company: 'Coupang',
      division: 'Logistics FP&A',
      role: 'Senior Manager',
      highlights: [
        'Managed 2 cost groups, 4 team members, KRW 60B/month budget across 20,000+ daily workers',
        'Built process-aligned costing model; sustained 2+ years improving month-end close accuracy',
        'Introduced weekly process-level targets and 3x/week review cadence with Operations',
        'Delivered ROI & CAPEX analysis including KRW 50B auto-sortation investment',
      ],
    },
    {
      period: '2020.08 — 2022.12',
      company: 'Hyundai Engineering',
      division: 'Finance',
      role: 'Senior Manager',
      highlights: [
        'Led global PF structuring for overseas plants and domestic industrial complexes',
        'Built Excel-based PF models; coordinated with legal for contract review',
        'Closed: Poland Olefins (Azoty), Canada Micro Modular Reactor, domestic solar & WtE plants',
      ],
    },
    {
      period: '2019.04 — 2020.08',
      company: 'LG Display',
      division: 'Strategy',
      role: 'Manager',
      highlights: [
        'FP&A for large-scale manufacturing: weekly SAP operation plan revisions',
        'Performed ROI analysis for Guangzhou OLED factory — LG Display\'s largest investment',
      ],
    },
    {
      period: '2014.09 — 2016.08',
      company: 'POSCO',
      division: 'Green Energy Business Group',
      role: 'Manager',
      highlights: [
        'Led financial models for synthetic gas projects (~USD 1.6B)',
        'M&A support: FDD for synthetic gas SPC acquisition',
        'Coverage: semiconductor gases, naphtha, LNG, solar power',
      ],
    },
    {
      period: '2011.07 — 2014.08',
      company: 'POSCO PLANTEC',
      division: 'Strategy',
      role: 'Associate',
      highlights: [
        'Supported solar PF refinancing; provided operational data to foreign lenders',
        'Developed pipeline evaluation process with KPI tracking & managerial accounting',
        'M&A & IR support for EPC company acquisition',
      ],
    },
  ],
  competencies: [
    { label: 'FP&A', detail: 'Budgeting, forecasting, variance analysis, cost modeling' },
    { label: 'Project Financing', detail: 'PF structuring, global banks, ECAs, deal documentation' },
    { label: 'Valuation & M&A', detail: 'Financial modeling, FDD, investment appraisal, ROI/CAPEX' },
    { label: 'Systems', detail: 'SAP, SQL, BI dashboards, advanced Excel modeling' },
    { label: 'Leadership', detail: 'Team of 4, cross-functional partnering, C-suite reporting' },
    { label: 'Industries', detail: 'Logistics, Construction, Manufacturing, Petrochemical, Energy' },
  ],
  education: [
    {
      period: '2017 — 2018',
      school: 'KAIST College of Business',
      degree: 'MBA, Accounting Focus',
      gpa: '3.8 / 4.5',
    },
    {
      period: '2004 — 2010',
      school: 'Handong Global University',
      degree: 'B.A. Business Administration',
      gpa: '3.8 / 4.5',
    },
  ],
  chartData: {
    budgetHistory: [
      { year: '2011', budget: 5 },
      { year: '2013', budget: 12 },
      { year: '2015', budget: 25 },
      { year: '2017', budget: 0 },
      { year: '2019', budget: 45 },
      { year: '2021', budget: 35 },
      { year: '2023', budget: 60 },
    ],
    industryExperience: [
      { name: 'Logistics', years: 2.5 },
      { name: 'Construction', years: 2.5 },
      { name: 'Manufacturing', years: 1.5 },
      { name: 'Petrochemical', years: 2 },
      { name: 'Energy', years: 3 },
    ],
    skillRadar: [
      { skill: 'FP&A', level: 95 },
      { skill: 'Financial Modeling', level: 90 },
      { skill: 'Project Finance', level: 85 },
      { skill: 'Valuation', level: 85 },
      { skill: 'Data Analysis', level: 80 },
      { skill: 'Leadership', level: 80 },
    ],
  },
  contact: {
    email: 'jsh8603@gmail.com',
    phone: '+82 010-2702-8602',
    location: 'Seoul, Korea',
    linkedin: '',
  },
};
