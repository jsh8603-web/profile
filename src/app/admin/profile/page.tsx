'use client';

import { useState, useEffect } from 'react';
import { Save, Plus, Trash2 } from 'lucide-react';
import { Button, Input } from '@/components/ui';
import { getProfile, updateProfile } from '@/lib/firebase/firestore';
import { initialProfile } from '@/data/resume';
import type { Profile } from '@/lib/types';
import { doc, setDoc } from 'firebase/firestore';
import { requireDb } from '@/lib/firebase/config';

export default function AdminProfilePage() {
  const [profile, setProfile] = useState<Profile>(initialProfile);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'basic' | 'career' | 'education' | 'competencies' | 'charts' | 'contact'>('basic');
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    getProfile()
      .then((data) => {
        if (data) {
          setProfile(data);
          setInitialized(true);
        }
      })
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      if (!initialized) {
        await setDoc(doc(requireDb(), 'profile', 'main'), profile);
        setInitialized(true);
      } else {
        await updateProfile(profile);
      }
      alert('Profile saved successfully!');
    } catch (err) {
      console.error('Save failed:', err);
      alert('Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const updateField = (field: keyof Profile, value: Profile[keyof Profile]) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  const tabs = [
    { key: 'basic', label: 'Basic Info' },
    { key: 'career', label: 'Career' },
    { key: 'education', label: 'Education' },
    { key: 'competencies', label: 'Competencies' },
    { key: 'charts', label: 'Chart Data' },
    { key: 'contact', label: 'Contact' },
  ] as const;

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">Profile</h1>
          <p className="text-sm text-[#86868B] mt-1">Edit your resume and profile data</p>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          <Save size={16} />
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-8 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
              activeTab === tab.key
                ? 'bg-[#1D1D1F] text-white'
                : 'bg-[#F5F5F7] text-[#424245] hover:bg-[#E8E8ED]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Basic Info Tab */}
      {activeTab === 'basic' && (
        <div className="space-y-4 card-flat p-6">
          <Input label="Name" value={profile.name} onChange={(e) => updateField('name', e.target.value)} />
          <Input label="Title" value={profile.title} onChange={(e) => updateField('title', e.target.value)} />
          <Input label="Tagline" value={profile.tagline} onChange={(e) => updateField('tagline', e.target.value)} />
          <div>
            <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Bio</label>
            <textarea
              value={profile.bio}
              onChange={(e) => updateField('bio', e.target.value)}
              rows={4}
              className="w-full px-4 py-2.5 rounded-xl border border-[#D2D2D7] bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all resize-none"
            />
          </div>
          {/* Stats */}
          <div>
            <label className="block text-sm font-medium text-[#1D1D1F] mb-3">Stats</label>
            {profile.stats.map((stat, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input
                  value={stat.number}
                  onChange={(e) => {
                    const updated = [...profile.stats];
                    updated[i] = { ...stat, number: e.target.value };
                    updateField('stats', updated);
                  }}
                  placeholder="Number"
                  className="w-24 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm"
                />
                <input
                  value={stat.label}
                  onChange={(e) => {
                    const updated = [...profile.stats];
                    updated[i] = { ...stat, label: e.target.value };
                    updateField('stats', updated);
                  }}
                  placeholder="Label"
                  className="flex-1 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm"
                />
                <button
                  onClick={() => updateField('stats', profile.stats.filter((_, j) => j !== i))}
                  className="p-2 text-red-400 hover:text-red-600"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => updateField('stats', [...profile.stats, { number: '', label: '' }])}
            >
              <Plus size={14} /> Add Stat
            </Button>
          </div>
        </div>
      )}

      {/* Career Tab */}
      {activeTab === 'career' && (
        <div className="space-y-4">
          {profile.career.map((job, i) => (
            <div key={i} className="card-flat p-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-[#1D1D1F]">Position {i + 1}</span>
                <button
                  onClick={() => updateField('career', profile.career.filter((_, j) => j !== i))}
                  className="p-1 text-red-400 hover:text-red-600"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Input label="Period" value={job.period} onChange={(e) => {
                  const updated = [...profile.career]; updated[i] = { ...job, period: e.target.value }; updateField('career', updated);
                }} />
                <Input label="Company" value={job.company} onChange={(e) => {
                  const updated = [...profile.career]; updated[i] = { ...job, company: e.target.value }; updateField('career', updated);
                }} />
                <Input label="Division" value={job.division} onChange={(e) => {
                  const updated = [...profile.career]; updated[i] = { ...job, division: e.target.value }; updateField('career', updated);
                }} />
                <Input label="Role" value={job.role} onChange={(e) => {
                  const updated = [...profile.career]; updated[i] = { ...job, role: e.target.value }; updateField('career', updated);
                }} />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Highlights</label>
                {job.highlights.map((h, j) => (
                  <div key={j} className="flex gap-2 mb-2">
                    <input
                      value={h}
                      onChange={(e) => {
                        const updated = [...profile.career];
                        const highlights = [...job.highlights];
                        highlights[j] = e.target.value;
                        updated[i] = { ...job, highlights };
                        updateField('career', updated);
                      }}
                      className="flex-1 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm"
                    />
                    <button onClick={() => {
                      const updated = [...profile.career];
                      updated[i] = { ...job, highlights: job.highlights.filter((_, k) => k !== j) };
                      updateField('career', updated);
                    }} className="p-2 text-red-400"><Trash2 size={14} /></button>
                  </div>
                ))}
                <button onClick={() => {
                  const updated = [...profile.career];
                  updated[i] = { ...job, highlights: [...job.highlights, ''] };
                  updateField('career', updated);
                }} className="text-xs text-[#0071E3] hover:underline">+ Add highlight</button>
              </div>
            </div>
          ))}
          <Button
            variant="secondary"
            onClick={() => updateField('career', [...profile.career, { period: '', company: '', division: '', role: '', highlights: [''] }])}
          >
            <Plus size={16} /> Add Position
          </Button>
        </div>
      )}

      {/* Education Tab */}
      {activeTab === 'education' && (
        <div className="space-y-4">
          {profile.education.map((edu, i) => (
            <div key={i} className="card-flat p-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-[#1D1D1F]">Education {i + 1}</span>
                <button onClick={() => updateField('education', profile.education.filter((_, j) => j !== i))} className="p-1 text-red-400"><Trash2 size={16} /></button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Input label="Period" value={edu.period} onChange={(e) => {
                  const updated = [...profile.education]; updated[i] = { ...edu, period: e.target.value }; updateField('education', updated);
                }} />
                <Input label="School" value={edu.school} onChange={(e) => {
                  const updated = [...profile.education]; updated[i] = { ...edu, school: e.target.value }; updateField('education', updated);
                }} />
                <Input label="Degree" value={edu.degree} onChange={(e) => {
                  const updated = [...profile.education]; updated[i] = { ...edu, degree: e.target.value }; updateField('education', updated);
                }} />
                <Input label="GPA" value={edu.gpa} onChange={(e) => {
                  const updated = [...profile.education]; updated[i] = { ...edu, gpa: e.target.value }; updateField('education', updated);
                }} />
              </div>
            </div>
          ))}
          <Button variant="secondary" onClick={() => updateField('education', [...profile.education, { period: '', school: '', degree: '', gpa: '' }])}>
            <Plus size={16} /> Add Education
          </Button>
        </div>
      )}

      {/* Competencies Tab */}
      {activeTab === 'competencies' && (
        <div className="space-y-3">
          {profile.competencies.map((comp, i) => (
            <div key={i} className="card-flat p-4 flex gap-3 items-start">
              <div className="flex-1 grid grid-cols-2 gap-3">
                <Input label="Label" value={comp.label} onChange={(e) => {
                  const updated = [...profile.competencies]; updated[i] = { ...comp, label: e.target.value }; updateField('competencies', updated);
                }} />
                <Input label="Detail" value={comp.detail} onChange={(e) => {
                  const updated = [...profile.competencies]; updated[i] = { ...comp, detail: e.target.value }; updateField('competencies', updated);
                }} />
              </div>
              <button onClick={() => updateField('competencies', profile.competencies.filter((_, j) => j !== i))} className="p-2 text-red-400 mt-6"><Trash2 size={16} /></button>
            </div>
          ))}
          <Button variant="secondary" onClick={() => updateField('competencies', [...profile.competencies, { label: '', detail: '' }])}>
            <Plus size={16} /> Add Competency
          </Button>
        </div>
      )}

      {/* Charts Tab */}
      {activeTab === 'charts' && (
        <div className="space-y-8">
          {/* Budget History */}
          <div className="card-flat p-6">
            <h3 className="text-sm font-semibold text-[#1D1D1F] mb-3">Budget History</h3>
            {profile.chartData.budgetHistory.map((item, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input value={item.year} onChange={(e) => {
                  const updated = [...profile.chartData.budgetHistory]; updated[i] = { ...item, year: e.target.value };
                  updateField('chartData', { ...profile.chartData, budgetHistory: updated });
                }} placeholder="Year" className="w-24 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm" />
                <input type="number" value={item.budget} onChange={(e) => {
                  const updated = [...profile.chartData.budgetHistory]; updated[i] = { ...item, budget: Number(e.target.value) };
                  updateField('chartData', { ...profile.chartData, budgetHistory: updated });
                }} placeholder="Budget" className="w-32 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm" />
                <button onClick={() => {
                  updateField('chartData', { ...profile.chartData, budgetHistory: profile.chartData.budgetHistory.filter((_, j) => j !== i) });
                }} className="p-2 text-red-400"><Trash2 size={14} /></button>
              </div>
            ))}
            <button onClick={() => {
              updateField('chartData', { ...profile.chartData, budgetHistory: [...profile.chartData.budgetHistory, { year: '', budget: 0 }] });
            }} className="text-xs text-[#0071E3] hover:underline">+ Add entry</button>
          </div>

          {/* Industry Experience */}
          <div className="card-flat p-6">
            <h3 className="text-sm font-semibold text-[#1D1D1F] mb-3">Industry Experience</h3>
            {profile.chartData.industryExperience.map((item, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input value={item.name} onChange={(e) => {
                  const updated = [...profile.chartData.industryExperience]; updated[i] = { ...item, name: e.target.value };
                  updateField('chartData', { ...profile.chartData, industryExperience: updated });
                }} placeholder="Industry" className="flex-1 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm" />
                <input type="number" step="0.5" value={item.years} onChange={(e) => {
                  const updated = [...profile.chartData.industryExperience]; updated[i] = { ...item, years: Number(e.target.value) };
                  updateField('chartData', { ...profile.chartData, industryExperience: updated });
                }} placeholder="Years" className="w-24 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm" />
                <button onClick={() => {
                  updateField('chartData', { ...profile.chartData, industryExperience: profile.chartData.industryExperience.filter((_, j) => j !== i) });
                }} className="p-2 text-red-400"><Trash2 size={14} /></button>
              </div>
            ))}
            <button onClick={() => {
              updateField('chartData', { ...profile.chartData, industryExperience: [...profile.chartData.industryExperience, { name: '', years: 0 }] });
            }} className="text-xs text-[#0071E3] hover:underline">+ Add entry</button>
          </div>

          {/* Skill Radar */}
          <div className="card-flat p-6">
            <h3 className="text-sm font-semibold text-[#1D1D1F] mb-3">Skills</h3>
            {profile.chartData.skillRadar.map((item, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input value={item.skill} onChange={(e) => {
                  const updated = [...profile.chartData.skillRadar]; updated[i] = { ...item, skill: e.target.value };
                  updateField('chartData', { ...profile.chartData, skillRadar: updated });
                }} placeholder="Skill" className="flex-1 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm" />
                <input type="number" min="0" max="100" value={item.level} onChange={(e) => {
                  const updated = [...profile.chartData.skillRadar]; updated[i] = { ...item, level: Number(e.target.value) };
                  updateField('chartData', { ...profile.chartData, skillRadar: updated });
                }} placeholder="Level" className="w-24 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm" />
                <button onClick={() => {
                  updateField('chartData', { ...profile.chartData, skillRadar: profile.chartData.skillRadar.filter((_, j) => j !== i) });
                }} className="p-2 text-red-400"><Trash2 size={14} /></button>
              </div>
            ))}
            <button onClick={() => {
              updateField('chartData', { ...profile.chartData, skillRadar: [...profile.chartData.skillRadar, { skill: '', level: 0 }] });
            }} className="text-xs text-[#0071E3] hover:underline">+ Add entry</button>
          </div>
        </div>
      )}

      {/* Contact Tab */}
      {activeTab === 'contact' && (
        <div className="card-flat p-6 space-y-4">
          <Input label="Email" value={profile.contact.email} onChange={(e) => updateField('contact', { ...profile.contact, email: e.target.value })} />
          <Input label="Phone" value={profile.contact.phone} onChange={(e) => updateField('contact', { ...profile.contact, phone: e.target.value })} />
          <Input label="Location" value={profile.contact.location} onChange={(e) => updateField('contact', { ...profile.contact, location: e.target.value })} />
          <Input label="LinkedIn URL" value={profile.contact.linkedin} onChange={(e) => updateField('contact', { ...profile.contact, linkedin: e.target.value })} />
        </div>
      )}
    </div>
  );
}
