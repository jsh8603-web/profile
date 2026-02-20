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
    milestones: [
      { year: '2011', company: 'POSCO PLANTEC', metric: '₩5B/mo', achievement: '태양광 PF · 파이프라인 평가' },
      { year: '2014', company: 'POSCO', metric: '$1.6B', achievement: '합성가스 PF 모델링' },
      { year: '2017', company: 'KAIST', metric: 'MBA 3.8', achievement: 'Accounting Focus', isMba: true },
      { year: '2019', company: 'LG Display', metric: '₩45B/mo', achievement: 'OLED ROI 분석' },
      { year: '2020', company: 'Hyundai Eng.', metric: '3 PF Deals', achievement: '글로벌 딜 클로징' },
      { year: '2023', company: 'Coupang', metric: '₩60B/mo', achievement: '프로세스 원가 모델' },
    ],
    industryExperience: [
      { name: 'Logistics', years: 2.5 },
      { name: 'Construction', years: 2.5 },
      { name: 'Manufacturing', years: 1.5 },
      { name: 'Petrochemical', years: 2 },
      { name: 'Energy', years: 3 },
    ],
    competencyGroups: [
      {
        title: 'Finance Core',
        items: [
          { label: 'FP&A', evidence: '₩60B/월 프로세스 원가 모델 구축 · 2년 운영' },
          { label: 'Project Finance', evidence: '폴란드 Olefins · 캐나다 MMR 글로벌 PF 클로징' },
          { label: 'Valuation & M&A', evidence: '₩50B CAPEX ROI + $1.6B 합성가스 FDD' },
          { label: 'Financial Modeling', evidence: '5개 회사 전 직장 Excel/SAP 모델 활용' },
        ],
      },
      {
        title: 'Technical',
        items: [
          { label: 'SAP', evidence: 'LG Display 주간 운영계획 수정' },
          { label: 'SQL & BI', evidence: 'Coupang 데이터 추출 · 대시보드 구축' },
          { label: 'Advanced Excel', evidence: 'PF 모델 · DCF · CAPEX 분석 전 직장' },
        ],
      },
      {
        title: 'Leadership',
        items: [
          { label: 'Team Management', evidence: '4명 팀, 2개 원가 그룹 관리 (Coupang)' },
          { label: 'Cross-functional', evidence: '주 3회 Operations 리뷰 · C-suite 보고' },
          { label: 'Deal Coordination', evidence: '국제 PF 딜팀 주도 (Hyundai)' },
        ],
      },
    ],
  },
  contact: {
    email: 'jsh8603@gmail.com',
    phone: '+82 010-2702-8602',
    location: 'Seoul, Korea',
    linkedin: '',
  },
};
