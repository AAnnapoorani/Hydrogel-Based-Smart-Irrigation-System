"use client";
import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { api } from "@/lib/api";

const features = [
  {
    icon: "🌱",
    title: "Soil Fertility Classification",
    desc: "Analyze N-P-K levels, pH, and organic carbon to classify your soil as High, Medium, or Low fertility with actionable remediation steps.",
    href: "/soil",
    color: "bg-green-50 border-green-100",
  },
  {
    icon: "🌾",
    title: "Crop Recommendation Engine",
    desc: "Data-driven crop matching tailored to Tamil Nadu's climate. Get ranked suggestions from Rice, Sugarcane, Cotton, Groundnut & more.",
    href: "/soil",
    color: "bg-blue-50 border-blue-100",
  },
  {
    icon: "💧",
    title: "Irrigation Optimization",
    desc: "Calculate precise water requirements using the SMD formula. Save up to 35% water while maintaining optimal soil moisture levels.",
    href: "/irrigation",
    color: "bg-teal-50 border-teal-100",
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
  { value: "35%", label: "Average water savings" },
  { value: "8",   label: "Crops recommended" },
  { value: "4",   label: "Soil parameters analysed" },
  { value: "∞",   label: "Historical reports" },
];

const container = { hidden: {}, show: { transition: { staggerChildren: 0.1 } } };
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } };

export default function LandingPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.includes("@")) return;
    setLoading(true);
    try {
      // In production, POST to /subscribe endpoint
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
      <section className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <span className="inline-flex items-center gap-2 bg-green-50 text-green-700 border border-green-100 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
            Erumaiyur Village, Tambaram, Tamil Nadu
          </span>

          <h1
            className="text-5xl md:text-6xl font-bold leading-tight text-green-950 mb-5"
            style={{ fontFamily: "'Fraunces', serif" }}
          >
            Smart Irrigation for<br />
            <em className="not-italic text-green-500">Smarter Harvests</em>
          </h1>

          <p className="text-lg text-green-700 max-w-lg mx-auto mb-8 leading-relaxed">
            AI-powered soil analysis, crop recommendation & water optimization — built specifically for
            Tamil Nadu's farmers.
          </p>

          <div className="flex gap-3 justify-center flex-wrap">
            <Link
              href="/soil"
              className="bg-green-700 hover:bg-green-900 text-white px-7 py-3.5 rounded-xl font-semibold text-base transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-green-900/20"
            >
              Start Soil Analysis
            </Link>
            <Link
              href="/dashboard"
              className="bg-white text-green-700 border-2 border-green-200 hover:border-green-400 hover:bg-green-50 px-7 py-3.5 rounded-xl font-semibold text-base transition-all"
            >
              View Dashboard
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ── STATS STRIP ── */}
      <section className="bg-white border-y border-green-100 py-8">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.07 }}
            >
              <p className="text-3xl font-bold text-green-700 mb-1" style={{ fontFamily: "'Fraunces', serif" }}>
                {s.value}
              </p>
              <p className="text-sm text-green-500">{s.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2
            className="text-3xl md:text-4xl font-bold text-green-950 mb-3"
            style={{ fontFamily: "'Fraunces', serif" }}
          >
            Everything You Need to Farm Smarter
          </h2>
          <p className="text-green-600 text-base">Three powerful modules working together for optimal yield and water conservation.</p>
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
              <Link href={f.href} className="block h-full">
                <div className={`h-full border rounded-2xl p-7 transition-all hover:-translate-y-1 hover:shadow-lg hover:shadow-green-900/10 cursor-pointer bg-white`}>
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-4 ${f.color} border`}>
                    {f.icon}
                  </div>
                  <h3 className="text-base font-semibold text-green-900 mb-2">{f.title}</h3>
                  <p className="text-sm text-green-600 leading-relaxed">{f.desc}</p>
                </div>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="bg-white border-y border-green-100 py-20">
        <div className="max-w-4xl mx-auto px-6">
          <h2
            className="text-3xl font-bold text-green-950 text-center mb-12"
            style={{ fontFamily: "'Fraunces', serif" }}
          >
            How It Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: "01", title: "Enter Soil Data", desc: "Input your N, P, K, pH, and organic carbon readings from a standard soil test kit." },
              { step: "02", title: "Get Recommendations", desc: "Our engine classifies fertility, matches ideal crops, and computes exact irrigation requirements." },
              { step: "03", title: "Schedule & Save", desc: "Schedule precision irrigation, track water savings, and export historical reports." },
            ].map((s) => (
              <div key={s.step} className="flex flex-col items-start">
                <span
                  className="text-5xl font-bold text-green-100 mb-3 leading-none"
                  style={{ fontFamily: "'Fraunces', serif" }}
                >
                  {s.step}
                </span>
                <h3 className="text-base font-semibold text-green-900 mb-2">{s.title}</h3>
                <p className="text-sm text-green-600 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SDG ── */}
      <section
        className="py-20 text-center"
        style={{ background: "linear-gradient(135deg, #173404, #0f6e56)" }}
      >
        <div className="max-w-2xl mx-auto px-6">
          <h2
            className="text-3xl font-bold text-white mb-3"
            style={{ fontFamily: "'Fraunces', serif" }}
          >
            Aligned with UN Sustainable Development Goals
          </h2>
          <p className="text-green-200 mb-8 text-sm leading-relaxed">
            IrrigateWise contributes directly to food security, clean water access, and responsible
            consumption across Tamil Nadu's farming communities.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            {sdgs.map((sdg) => (
              <span
                key={sdg}
                className="bg-white/15 text-white border border-white/25 px-4 py-2 rounded-full text-sm font-medium"
              >
                {sdg}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── EMAIL CAPTURE ── */}
      <section className="max-w-lg mx-auto px-6 py-20 text-center">
        <h2
          className="text-3xl font-bold text-green-950 mb-2"
          style={{ fontFamily: "'Fraunces', serif" }}
        >
          Stay in the Loop
        </h2>
        <p className="text-green-600 text-sm mb-6">
          Get seasonal alerts, soil reports, and irrigation schedules delivered to your inbox.
        </p>

        {submitted ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-green-50 border border-green-100 rounded-xl px-6 py-4 text-green-700 font-medium text-sm"
          >
            ✓ You're subscribed! Watch for your first seasonal report.
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="email"
              placeholder="Enter your email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="flex-1 px-4 py-3 border border-green-200 rounded-xl text-sm focus:outline-none focus:border-green-500 transition-colors bg-white"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-green-700 hover:bg-green-900 text-white px-5 py-3 rounded-xl font-semibold text-sm transition-all disabled:opacity-60 whitespace-nowrap"
            >
              {loading ? "…" : "Subscribe"}
            </button>
          </form>
        )}
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-green-100 bg-white py-8">
        <div className="max-w-5xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-green-700 rounded-lg flex items-center justify-center text-white text-xs font-bold">IW</div>
            <span className="font-bold text-green-900 text-sm" style={{ fontFamily: "'Fraunces', serif" }}>IrrigateWise</span>
          </div>
          <p className="text-xs text-green-400 text-center">
            Built for Erumaiyur Village, Tambaram · Tamil Nadu, India · Smart Irrigation Platform
          </p>
          <div className="flex gap-4 text-xs text-green-500">
            <Link href="/dashboard" className="hover:text-green-700 transition-colors">Dashboard</Link>
            <Link href="/soil" className="hover:text-green-700 transition-colors">Soil Analysis</Link>
            <Link href="/reports" className="hover:text-green-700 transition-colors">Reports</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
