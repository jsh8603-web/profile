'use client';

import { motion } from 'framer-motion';
import { ArrowDown } from 'lucide-react';
import Link from 'next/link';

export default function HeroSection() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
      {/* Subtle gradient background */}
      <div className="absolute inset-0 bg-gradient-to-b from-white via-[#FAFAFA] to-[#F5F5F7]" />

      {/* Decorative circles */}
      <div className="absolute top-20 right-[10%] w-[500px] h-[500px] rounded-full bg-[#0071E3]/[0.03] blur-3xl" />
      <div className="absolute bottom-20 left-[5%] w-[400px] h-[400px] rounded-full bg-[#0071E3]/[0.02] blur-3xl" />

      <div className="relative z-10 max-w-6xl mx-auto px-5 sm:px-8 w-full">
        <div className="max-w-3xl">
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="section-label mb-6"
          >
            Senior FP&A Manager
          </motion.p>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-5xl sm:text-6xl lg:text-7xl font-bold text-[#1D1D1F] leading-[1.05] tracking-tight"
          >
            Financial clarity
            <br />
            <span className="text-[#0071E3]">drives growth.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-6 text-lg sm:text-xl text-[#86868B] leading-relaxed max-w-xl"
          >
            11+ years driving financial precision across logistics, manufacturing, energy, and construction — from cost models to C-suite strategy.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-8 flex flex-wrap gap-3"
          >
            <Link
              href="/resume"
              className="inline-flex items-center px-6 py-3 rounded-full text-sm font-semibold bg-[#0071E3] text-white hover:bg-[#0077ED] transition-colors"
            >
              View Resume
            </Link>
            <Link
              href="/blog"
              className="inline-flex items-center px-6 py-3 rounded-full text-sm font-semibold bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] transition-colors"
            >
              Read Blog
            </Link>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.6 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
          >
            <ArrowDown size={20} className="text-[#D2D2D7]" />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
