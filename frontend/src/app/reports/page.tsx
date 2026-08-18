"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";

/* ── Static seed data (mirrors backend seed.sql) ── */
const allRecords = [
  { date: "Apr 18, 2025", crop: "Rice",      fertility: 78, cls: "High",   irr: 14, saved: 32, n: 92,  p: 48, k: 220 },
  { date: "Apr 11, 2025", crop: "Rice",      fertility: 74, cls: "High",   irr: 16, saved: 28, n: 88,  p: 44, k: 210 },
  { date: "Apr 04, 2025", crop: "Sugarcane", fertility: 62, cls: "Medium", irr: 19, saved: 22, n: 72,  p: 38, k: 185 },
  { date: "Mar 28, 2025", crop: "Sugarcane", fertility: 65, cls: "Medium", irr: 18, saved: 24, n: 76,  p: 40, k: 192 },
  { date: "Mar 21, 2025", crop: "Cotton",    fertility: 55, cls: "Medium", irr: 20, saved: 18, n: 64,  p: 32, k: 170 },
  { date: "Mar 14, 2025", crop: "Rice",      fertility: 80, cls: "High",   irr: 13, saved: 35, n: 94,  p: 50, k: 225 },
  { date: "Mar 07, 2025", crop: "Cotton",    fertility: 42, cls: "Low",    irr: 22, saved: 10, n: 52,  p: 26, k: 145 },
  { date: "Feb 28, 2025", crop: "Rice",      fertility: 70, cls: "High",   irr: 15, saved: 30, n: 85,  p: 42, k: 205 },
];

const chartData = [...allRecords].reverse().map((r) => ({
  date:      r.date.split(",")[0],
  fertility: r.fertility,
  saved:     r.saved,
}));

const cropPill: Record<string, string> = {
  Rice:      "bg-blue-50 text-blue-700",
  Sugarcane: "bg-green-50 text-green-700",
  Cotton:    "bg-amber-50 text-amber-600",
};
const clsPill: Record<string, string> = {
  High:   "bg-green-50 text-green-700",
  Medium: "bg-amber-50 text-amber-600",
  Low:    "bg-red-50 text-red-600",
};

export default function ReportsPage() {
  const [cropFilter, setCropFilter] = useState("all");
  const [clsFilter,  setClsFilter]  = useState("all");
  const [exporting,  setExporting]  = useState(false);
  const [exportDone, setExportDone] = useState(false);

  const filtered = allRecords.filter(
    (r) =>
      (cropFilter === "all" || r.crop === cropFilter) &&
      (clsFilter  === "all" || r.cls  === clsFilter),
  );

  async function handleExport() {
    setExporting(true);
    setExportDone(false);
    try {
      // In production, calls GET /reports/export which returns a signed PDF URL
      await new Promise((r) => setTimeout(r, 1800));
      setExportDone(true);
    } finally {
      setExporting(false);
    }
  }

  /* Summary stats */
  const avgFertility = Math.round(allRecords.reduce((a, r) => a + r.fertility, 0) / allRecords.length);
  const avgSaved     = Math.round(allRecords.reduce((a, r) => a + r.saved, 0)     / allRecords.length);
  const totalIrr     = allRecords.reduce((a, r) => a + r.irr, 0);

  return (
    <main className="max-w-6xl mx-auto px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="text-3xl font-bold text-green-950 mb-1" style={{ fontFamily: "'Fraunces', serif" }}>
          Reports & History
        </h1>
        <p className="text-green-700 text-sm mb-8">Historical analysis data, trends, and exportable records.</p>

        {/* Summary strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            { label: "Records",          value: allRecords.length },
            { label: "Avg Fertility",    value: `${avgFertility}%` },
            { label: "Avg Water Saved",  value: `${avgSaved}%`    },
            { label: "Total Irrigation", value: `${totalIrr} L/m²` },
          ].map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
              className="bg-white rounded-2xl border border-green-100 p-5 shadow-sm"
            >
              <p className="text-xs font-semibold uppercase tracking-widest text-green-400 mb-2">{s.label}</p>
              <p className="text-2xl font-bold text-green-800">{s.value}</p>
            </motion.div>
          ))}
        </div>

        {/* Trend chart */}
        <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <h2 className="text-sm font-semibold text-green-900">
              Soil Fertility & Water Savings Trend <span className="font-normal text-green-500">— Last 30 days</span>
            </h2>
            <div className="flex gap-4 text-xs text-green-600">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-green-600 inline-block" /> Fertility Score
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-teal-500 inline-block" /> Water Saved %
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f4ea" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#7a9a5a" }}
                axisLine={false}
                tickLine={false}
                interval={0}
                angle={-35}
                textAnchor="end"
                height={45}
              />
              <YAxis tick={{ fontSize: 11, fill: "#7a9a5a" }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ background: "#fff", border: "1px solid #c0dd97", borderRadius: 8, fontSize: 13 }}
                formatter={(v: number, name: string) => [
                  `${v}${name === "fertility" ? " pts" : "%"}`,
                  name === "fertility" ? "Fertility Score" : "Water Saved",
                ]}
              />
              <Line type="monotone" dataKey="fertility" stroke="#639922" strokeWidth={2.5} dot={{ fill: "#639922", r: 4 }} />
              <Line type="monotone" dataKey="saved"     stroke="#1d9e75" strokeWidth={2.5} dot={{ fill: "#1d9e75", r: 4 }} strokeDasharray="5 3" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-3 mb-4 flex-wrap">
          <select
            value={cropFilter}
            onChange={(e) => setCropFilter(e.target.value)}
            className="px-3 py-2 border border-green-200 rounded-lg text-sm bg-white focus:outline-none focus:border-green-500"
          >
            <option value="all">All Crops</option>
            <option value="Rice">Rice</option>
            <option value="Sugarcane">Sugarcane</option>
            <option value="Cotton">Cotton</option>
          </select>

          <select
            value={clsFilter}
            onChange={(e) => setClsFilter(e.target.value)}
            className="px-3 py-2 border border-green-200 rounded-lg text-sm bg-white focus:outline-none focus:border-green-500"
          >
            <option value="all">All Classifications</option>
            <option value="High">High Fertility</option>
            <option value="Medium">Medium Fertility</option>
            <option value="Low">Low Fertility</option>
          </select>

          <span className="text-xs text-green-400 ml-1">
            {filtered.length} record{filtered.length !== 1 ? "s" : ""}
          </span>

          <button
            onClick={handleExport}
            disabled={exporting}
            className="ml-auto flex items-center gap-2 bg-white border border-green-200 hover:bg-green-50 hover:border-green-400 text-green-700 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-60"
          >
            {exporting ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-green-200 border-t-green-700 rounded-full animate-spin inline-block" />
                Generating…
              </>
            ) : exportDone ? (
              <>✓ PDF Ready</>
            ) : (
              <>↓ Export PDF</>
            )}
          </button>
        </div>

        {/* Table */}
        <div className="bg-white rounded-2xl border border-green-100 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-green-50">
                <tr>
                  {["Date","Crop","Fertility Score","Classification","Irrigation (L/m²)","Water Saved","N / P / K"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-green-600 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-green-400 text-sm">
                      No records match the selected filters.
                    </td>
                  </tr>
                ) : (
                  filtered.map((r, i) => (
                    <motion.tr
                      key={`${r.date}-${r.crop}`}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.04 }}
                      className="border-t border-green-50 hover:bg-green-50/40 transition-colors"
                    >
                      <td className="px-4 py-3 text-green-600 text-xs whitespace-nowrap">{r.date}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${cropPill[r.crop]}`}>
                          {r.crop}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-bold text-green-800">{r.fertility}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${clsPill[r.cls]}`}>
                          {r.cls}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-green-700">{r.irr} L/m²</td>
                      <td className="px-4 py-3">
                        <span className="font-semibold text-teal-700">{r.saved}%</span>
                      </td>
                      <td className="px-4 py-3 text-green-500 text-xs font-mono">{r.n}/{r.p}/{r.k}</td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
