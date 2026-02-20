'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Save, Plus, Trash2, ArrowLeft } from 'lucide-react';
import { Button, Input, Skeleton } from '@/components/ui';
import { getSkill, setSkill } from '@/lib/firebase/firestore';
import { initialSkills } from '@/data/skills';
import type { SkillDetail } from '@/lib/types';

export default function EditSkillPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [skill, setSkillState] = useState<SkillDetail | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;

    getSkill(slug)
      .then((data) => {
        setSkillState(data || initialSkills.find(s => s.slug === slug) || null);
      })
      .catch(() => {
        setSkillState(initialSkills.find(s => s.slug === slug) || null);
      })
      .finally(() => setLoading(false));
  }, [slug]);

  const handleSave = async () => {
    if (!skill) return;
    setSaving(true);
    try {
      await setSkill(slug, skill);
      alert('Skill saved successfully!');
    } catch (err) {
      console.error('Save failed:', err);
      alert('Failed to save skill');
    } finally {
      setSaving(false);
    }
  };

  const updateField = <K extends keyof SkillDetail>(field: K, value: SkillDetail[K]) => {
    setSkillState(prev => prev ? { ...prev, [field]: value } : prev);
  };

  if (loading) {
    return (
      <div className="max-w-4xl">
        <Skeleton className="h-8 w-48 mb-4" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!skill) {
    return (
      <div className="max-w-4xl">
        <h1 className="text-2xl font-bold text-[#1D1D1F]">Skill not found</h1>
        <Link href="/admin/skills" className="mt-2 text-[#0071E3] text-sm hover:underline">
          Back to Skills
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link
            href="/admin/skills"
            className="inline-flex items-center gap-1.5 text-sm text-[#86868B] hover:text-[#0071E3] transition-colors mb-2"
          >
            <ArrowLeft size={14} />
            Back to Skills
          </Link>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">{skill.label}</h1>
          <p className="text-sm text-[#86868B] mt-1">Edit skill detail page</p>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          <Save size={16} />
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      {/* Basic Info */}
      <div className="card-flat p-6 space-y-4 mb-6">
        <h2 className="text-sm font-semibold text-[#1D1D1F]">Basic Info</h2>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Label" value={skill.label} onChange={(e) => updateField('label', e.target.value)} />
          <Input label="Icon (lucide name)" value={skill.icon} onChange={(e) => updateField('icon', e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Summary</label>
          <textarea
            value={skill.summary}
            onChange={(e) => updateField('summary', e.target.value)}
            rows={2}
            className="w-full px-4 py-2.5 rounded-xl border border-[#D2D2D7] bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all resize-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Description</label>
          <textarea
            value={skill.description}
            onChange={(e) => updateField('description', e.target.value)}
            rows={4}
            className="w-full px-4 py-2.5 rounded-xl border border-[#D2D2D7] bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all resize-none"
          />
        </div>
      </div>

      {/* Related Careers */}
      <div className="space-y-4 mb-6">
        <h2 className="text-sm font-semibold text-[#1D1D1F]">Related Careers</h2>
        {skill.relatedCareers.map((career, i) => (
          <div key={i} className="card-flat p-6 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[#86868B]">Career {i + 1}</span>
              <button
                onClick={() => updateField('relatedCareers', skill.relatedCareers.filter((_, j) => j !== i))}
                className="p-1 text-red-400 hover:text-red-600"
              >
                <Trash2 size={16} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Company"
                value={career.company}
                onChange={(e) => {
                  const updated = [...skill.relatedCareers];
                  updated[i] = { ...career, company: e.target.value };
                  updateField('relatedCareers', updated);
                }}
              />
              <Input
                label="Period"
                value={career.period}
                onChange={(e) => {
                  const updated = [...skill.relatedCareers];
                  updated[i] = { ...career, period: e.target.value };
                  updateField('relatedCareers', updated);
                }}
              />
            </div>
            <Input
              label="Role"
              value={career.role}
              onChange={(e) => {
                const updated = [...skill.relatedCareers];
                updated[i] = { ...career, role: e.target.value };
                updateField('relatedCareers', updated);
              }}
            />
            <div>
              <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Description</label>
              <textarea
                value={career.description}
                onChange={(e) => {
                  const updated = [...skill.relatedCareers];
                  updated[i] = { ...career, description: e.target.value };
                  updateField('relatedCareers', updated);
                }}
                rows={3}
                className="w-full px-4 py-2.5 rounded-xl border border-[#D2D2D7] bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all resize-none"
              />
            </div>
          </div>
        ))}
        <Button
          variant="secondary"
          onClick={() =>
            updateField('relatedCareers', [
              ...skill.relatedCareers,
              { company: '', period: '', role: '', description: '' },
            ])
          }
        >
          <Plus size={16} /> Add Career
        </Button>
      </div>

      {/* Key Achievements */}
      <div className="card-flat p-6 mb-6">
        <h2 className="text-sm font-semibold text-[#1D1D1F] mb-3">Key Achievements</h2>
        {skill.keyAchievements.map((achievement, i) => (
          <div key={i} className="flex gap-2 mb-2">
            <input
              value={achievement}
              onChange={(e) => {
                const updated = [...skill.keyAchievements];
                updated[i] = e.target.value;
                updateField('keyAchievements', updated);
              }}
              className="flex-1 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm"
            />
            <button
              onClick={() => updateField('keyAchievements', skill.keyAchievements.filter((_, j) => j !== i))}
              className="p-2 text-red-400 hover:text-red-600"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
        <button
          onClick={() => updateField('keyAchievements', [...skill.keyAchievements, ''])}
          className="text-xs text-[#0071E3] hover:underline"
        >
          + Add achievement
        </button>
      </div>

      {/* Tools */}
      <div className="card-flat p-6">
        <h2 className="text-sm font-semibold text-[#1D1D1F] mb-3">Tools & Skills</h2>
        {skill.tools.map((tool, i) => (
          <div key={i} className="flex gap-2 mb-2">
            <input
              value={tool}
              onChange={(e) => {
                const updated = [...skill.tools];
                updated[i] = e.target.value;
                updateField('tools', updated);
              }}
              className="flex-1 px-3 py-2 rounded-xl border border-[#D2D2D7] text-sm"
            />
            <button
              onClick={() => updateField('tools', skill.tools.filter((_, j) => j !== i))}
              className="p-2 text-red-400 hover:text-red-600"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
        <button
          onClick={() => updateField('tools', [...skill.tools, ''])}
          className="text-xs text-[#0071E3] hover:underline"
        >
          + Add tool
        </button>
      </div>
    </div>
  );
}
