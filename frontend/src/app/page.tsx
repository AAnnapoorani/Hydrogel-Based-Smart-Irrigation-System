"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Droplets, Sprout, ShieldCheck, ArrowRight, Check } from "lucide-react";

const features = [
  {
    icon: <Sprout className="w-5 h-5 text-emerald-700" />,
    title: "Terrace Garden Hub",
    desc: "All-in-one container garden management: track active grow bags, discover sunlight-matched container crops, and consult the 24-species botanical catalog.",
    href: "/plants",
  },
  {
    icon: <ShieldCheck className="w-5 h-5 text-emerald-700" />,
    title: "Plant Health AI Diagnostics",
    desc: "Computer vision foliar disease screening and insect pest identification. Instant organic neem and biological remediation protocols.",
    href: "/diagnosis",
  },
  {
    icon: <Droplets className="w-5 h-5 text-emerald-700" />,
    title: "Hydrogel Irrigation Optimization",
    desc: "Calculate precise water requirements with predictive micro-drip control. Save 30.9% to 48.2% water while maintaining optimal container root hydration.",
    href: "/irrigation",
  },
];

const sdgs = [
  "SDG 2 — Zero Hunger",
  "SDG 6 — Clean Water",
  "SDG 12 — Responsible Consumption",
  "SDG 13 — Climate Action",
  "SDG 15 — Life on Land",
];

const stats = [
  { value: "30.9%", label: "Water saved vs SMD (48.2% vs fixed)" },
  { value: "14",   label: "Terrace crops recommended" },
  { value: "24",   label: "Curated container species" },
  { value: "100%", label: "Automated logs" },
];

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

export default function LandingPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.includes("@")) return;
    setLoading(true);
    try {
      await new Promise((r) => setTimeout(r, 600));
      setSubmitted(true);
      setEmail("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="overflow-x-hidden">
      {/* ── HERO ── */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 pt-12 sm:pt-16 pb-14 text-center">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          {/* Logo Brand Crest */}
          <div className="flex justify-center mb-5">
            <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-full p-1 bg-white border-2 border-emerald-600/30 shadow-card flex items-center justify-center hover:scale-105 transition-transform">
              <img
                src="/logo.png"
                alt="IrrigateWise Emblem Logo"
                className="w-full h-full object-contain rounded-full"
              />
            </div>
          </div>

          <span className="inline-flex items-center gap-2 bg-emerald-50 text-emerald-800 border border-emerald-200/80 px-3.5 py-1 rounded-full text-xs font-medium mb-6 shadow-soft">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse" />
            Erumaiyur Village, Tambaram, Tamil Nadu
          </span>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight text-slate-900 mb-5 tracking-tight font-serif">
            Smart Irrigation for<br />
            <span className="text-emerald-700">Smarter Harvests</span>
          </h1>

          <p className="text-base sm:text-lg text-slate-600 max-w-xl mx-auto mb-8 leading-relaxed">
            AI-powered soil analysis, crop recommendation & water optimization — engineered specifically for
            Tamil Nadu&apos;s agricultural microclimates.
          </p>

          <div className="flex gap-3 justify-center flex-wrap">
            <Link
              href="/soil"
              className="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-800 text-white px-6 py-3 rounded-lg font-medium text-sm shadow-soft transition-colors"
            >
              Start Soil Analysis
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 px-6 py-3 rounded-lg font-medium text-sm transition-colors shadow-soft"
            >
              View Dashboard
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ── STATS STRIP ── */}
      <section className="bg-white border-y border-slate-200/80 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.05 }}
            >
              <p className="text-2xl sm:text-3xl font-bold text-slate-900 mb-1 tracking-tight">
                {s.value}
              </p>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{s.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-2 tracking-tight">
            Integrated Precision Agriculture Modules
          </h2>
          <p className="text-slate-600 text-sm max-w-lg mx-auto">
            Three intelligent components working together to conserve water and maximize crop yield.
          </p>
        </div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-3 gap-5"
        >
          {features.map((f) => (
            <motion.div key={f.title} variants={item}>
              <Link href={f.href} className="block h-full group">
                <div className="h-full bg-white border border-slate-200/80 rounded-xl p-6 shadow-soft transition-all hover:border-slate-300 hover:shadow-card flex flex-col">
                  <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200/60 flex items-center justify-center mb-4 transition-colors group-hover:bg-emerald-100">
                    {f.icon}
                  </div>
                  <h3 className="text-base font-semibold text-slate-900 mb-2 group-hover:text-emerald-800 transition-colors">
                    {f.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-600 leading-relaxed flex-1">
                    {f.desc}
                  </p>
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 mt-4">
                    Explore module →
                  </span>
                </div>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="bg-white border-y border-slate-200/80 py-16 sm:py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-2 tracking-tight">
              How the System Operates
            </h2>
            <p className="text-slate-600 text-sm">
              Simple three-step precision loop from test sample to automated water delivery.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
            {[
              { step: "01", title: "Enter Soil Readings", desc: "Input your N, P, K, pH, and organic carbon readings from a standard soil test kit or sensor probe." },
              { step: "02", title: "Generate ML Decisions", desc: "Our models classify fertility, recommend suited crops, and compute exact irrigation requirements." },
              { step: "03", title: "Automate & Conserve", desc: "Execute precision pulse actuation, monitor hydrogel retention, and review verifiable audit reports." },
            ].map((s) => (
              <div key={s.step} className="p-5 rounded-xl bg-slate-50 border border-slate-200/70 flex flex-col items-start">
                <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-100/70 border border-emerald-200 px-2 py-0.5 rounded-md mb-3">
                  Step {s.step}
                </span>
                <h3 className="text-sm font-semibold text-slate-900 mb-1.5">{s.title}</h3>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SDG ── */}
      <section className="py-16 text-center bg-slate-950 text-white border-b border-slate-800">
        <div className="max-w-2xl mx-auto px-4 sm:px-6">
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-2 inline-block">
            Sustainability & Impact
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 tracking-tight">
            Aligned with UN Sustainable Development Goals
          </h2>
          <p className="text-slate-300 mb-6 text-xs sm:text-sm leading-relaxed">
            IrrigateWise contributes directly to food security, clean water preservation, and responsible
            consumption across Tamil Nadu&apos;s agricultural regions.
          </p>
          <div className="flex flex-wrap gap-2.5 justify-center">
            {sdgs.map((sdg) => (
              <span
                key={sdg}
                className="bg-white/10 text-slate-200 border border-white/15 px-3 py-1.5 rounded-full text-xs font-medium"
              >
                {sdg}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── EMAIL CAPTURE ── */}
      <section className="max-w-md mx-auto px-4 sm:px-6 py-16 text-center">
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-1 tracking-tight">
          Stay Informed on Seasonal Reports
        </h2>
        <p className="text-slate-600 text-xs sm:text-sm mb-6">
          Receive seasonal agronomic updates, crop advisories, and water efficiency summaries.
        </p>

        {submitted ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-emerald-800 font-medium text-xs sm:text-sm flex items-center justify-center gap-2"
          >
            <Check className="w-4 h-4 text-emerald-600" />
            <span>You&apos;re subscribed! You will receive our next seasonal bulletin.</span>
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
            <input
              type="email"
              placeholder="Enter your email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="flex-1 px-3.5 py-2.5 border border-slate-200 rounded-lg text-sm bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 transition-colors placeholder:text-slate-400"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-emerald-700 hover:bg-emerald-800 text-white px-5 py-2.5 rounded-lg font-medium text-sm transition-colors disabled:opacity-60 whitespace-nowrap shadow-soft"
            >
              {loading ? "Subscribing…" : "Subscribe"}
            </button>
          </form>
        )}
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-slate-200/80 bg-white py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full overflow-hidden bg-white border border-emerald-600/30 flex items-center justify-center p-0.5 shadow-sm">
              <img
                src="/logo.png"
                alt="IrrigateWise Logo"
                className="w-full h-full object-contain"
              />
            </div>
            <span className="font-semibold text-slate-900 text-sm">IrrigateWise</span>
          </div>
          <p className="text-xs text-slate-500 text-center">
            Erumaiyur Village, Tambaram · Tamil Nadu, India · Smart Precision Irrigation Platform
          </p>
          <div className="flex gap-4 text-xs font-medium text-slate-600">
            <Link href="/dashboard" className="hover:text-emerald-700 transition-colors">Dashboard</Link>
            <Link href="/soil" className="hover:text-emerald-700 transition-colors">Soil Analysis</Link>
            <Link href="/reports" className="hover:text-emerald-700 transition-colors">Reports</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
