'use client';

import { useEffect, useState } from 'react';
import { Mail, Phone, MapPin, Linkedin } from 'lucide-react';
import { ScrollReveal } from '@/components/ui';
import { getProfile } from '@/lib/firebase/firestore';
import { initialProfile } from '@/data/resume';
import type { Profile } from '@/lib/types';

export default function ContactPage() {
  const [profile, setProfile] = useState<Profile>(initialProfile);

  useEffect(() => {
    getProfile()
      .then((data) => { if (data) setProfile(data); })
      .catch(() => {});
  }, []);

  const contactItems = [
    { icon: Mail, label: 'Email', value: profile.contact.email, href: `mailto:${profile.contact.email}` },
    { icon: Phone, label: 'Phone', value: profile.contact.phone, href: `tel:${profile.contact.phone.replace(/[^+\d]/g, '')}` },
    { icon: MapPin, label: 'Location', value: profile.contact.location, href: null },
    ...(profile.contact.linkedin ? [{ icon: Linkedin, label: 'LinkedIn', value: 'View Profile', href: profile.contact.linkedin }] : []),
  ];

  return (
    <div className="section-padding">
      <div className="max-w-3xl mx-auto px-5 sm:px-8">
        <ScrollReveal>
          <p className="section-label mb-4">Contact</p>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-[#1D1D1F] leading-tight">
            Let&apos;s connect.
          </h1>
          <p className="mt-4 text-lg text-[#86868B] max-w-xl">
            Interested in working together or want to discuss finance and strategy? Feel free to reach out.
          </p>
        </ScrollReveal>

        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {contactItems.map((item, i) => (
            <ScrollReveal key={item.label} delay={i * 0.1}>
              {item.href ? (
                <a href={item.href} target={item.href.startsWith('http') ? '_blank' : undefined} rel="noopener noreferrer" className="card p-6 flex items-start gap-4 h-full">
                  <div className="p-3 rounded-2xl bg-[#0071E3]/10">
                    <item.icon size={22} className="text-[#0071E3]" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-[#86868B] uppercase tracking-wider">{item.label}</p>
                    <p className="mt-1 text-base font-medium text-[#1D1D1F]">{item.value}</p>
                  </div>
                </a>
              ) : (
                <div className="card p-6 flex items-start gap-4 h-full">
                  <div className="p-3 rounded-2xl bg-[#0071E3]/10">
                    <item.icon size={22} className="text-[#0071E3]" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-[#86868B] uppercase tracking-wider">{item.label}</p>
                    <p className="mt-1 text-base font-medium text-[#1D1D1F]">{item.value}</p>
                  </div>
                </div>
              )}
            </ScrollReveal>
          ))}
        </div>
      </div>
    </div>
  );
}
