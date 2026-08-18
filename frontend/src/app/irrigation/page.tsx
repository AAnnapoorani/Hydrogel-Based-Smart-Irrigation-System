"use client";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import { api } from "@/lib/api";

const TRADITIONAL_BASELINE = 22; // L/m²

const SOIL_ALPHA: Record<string, number> = {
  clay: 1.1,
  loam: 0.85,
  sandy: 0.65,
  silt: 1.0,
};

const weeklyData = [
  { day: "Mon", smart: 14, traditional: 22 },
  { day: "Tue", smart: 12, traditional: 22 },
  { day: "Wed", smart: 16, traditional: 24 },
  { day: "Thu", smart: 11, traditional: 22 },
  { day: "Fri", smart: 15, traditional: 23 },
  { day: "Sat", smart: 13, traditional: 22 },
  { day: "Sun", smart: 14, traditional: 22 },
];

const schedule = [
  { day: "Mon", time: "6:00 AM", amount: 14, status: "Scheduled" },
  { day: "Tue", time: "6:00 AM", amount: 13, status: "Scheduled" },
  { day: "Wed", time: "—",       amount: null, status: "Rest" },
  { day: "Thu", time: "6:00 AM", amount: 15, status: "Scheduled" },
  { day: "Fri", time: "6:00 AM", amount: 12, status: "Scheduled" },
  { day: "Sat", time: "—",       amount: null, status: "Rest" },
  { day: "Sun", time: "7:00 AM", amount: 14, status: "Scheduled" },
];

export default function IrrigationPage() {
  const [smCurrent, setSmCurrent]   = useState(58);
  const [smOptimal, setSmOptimal]   = useState(70);
  const [texture,   setTexture]     = useState("loam");
  const [fieldArea, setFieldArea]   = useState(500);
  const [scheduled, setScheduled]   = useState(false);

  const alpha = SOIL_ALPHA[texture] ?? 0.85;
  const smd   = Math.max(0, smOptimal - smCurrent);
  const ir    = parseFloat((alpha * smd).toFixed(1));
  const total = Math.round(ir * fieldArea);
  const saved = Math.max(0, Math.round((1 - ir / TRADITIONAL_BASELINE) * 100));

  const efficiency =
    saved >= 30 ? "Excellent" : saved >= 20 ? "Good" : saved >= 10 ? "Moderate" : "Low";
  const effColor =
    saved >= 30 ? "text-green-700" : saved >= 20 ? "text-teal-700" : saved >= 10 ? "text-amber-600" : "text-red-600";

  const scheduleMutation = useMutation({
    mutationFn: () =>
      api.post("/irrigation/schedule", {
        irrigation_required: ir,
        field_area: fieldArea,
        hours_from_now: 12,
      }),
    onSuccess: () => setScheduled(true),
  });

  function handleSchedule() {
    scheduleMutation.mutate();
  }

  return (
    <main className="max-w-6xl mx-auto px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="text-3xl font-bold text-green-950 mb-1" style={{ fontFamily: "'Fraunces', serif" }}>
          Irrigation Optimization
        </h1>
        <p className="text-green-700 text-sm mb-8">
          Calculate precise water requirements using the Soil Moisture Deficit formula.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ── LEFT: inputs ── */}
          <div className="space-y-5">

            {/* Formula card */}
            <div className="rounded-2xl p-5" style={{ background: "#173404" }}>
              <p className="text-xs font-semibold uppercase tracking-widest text-green-400 mb-3">Calculation Method</p>
              <p className="font-mono text-green-200 text-base mb-1">
                SMD = <span className="text-green-400">SM_optimal</span> − <span className="text-green-400">SM_current</span>
              </p>
              <p className="font-mono text-green-200 text-base">
                IR = <span className="text-green-400">α</span> × <span className="text-green-400">SMD</span>
              </p>
              <p className="text-xs text-green-600 mt-3">
                α = soil coefficient · loam 0.85 · clay 1.1 · sandy 0.65 · silt 1.0
              </p>
            </div>

            {/* Sliders */}
            <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm space-y-5">
              <SliderRow
                label="Current Soil Moisture"
                value={smCurrent}
                min={10} max={90}
                onChange={setSmCurrent}
                unit="%"
              />
              <SliderRow
                label="Optimal Soil Moisture"
                value={smOptimal}
                min={30} max={90}
                onChange={setSmOptimal}
                unit="%"
              />

              {/* Soil texture select */}
              <div>
                <label className="flex justify-between text-xs font-medium text-green-600 mb-2">
                  <span>Soil Texture</span>
                  <span className="font-bold text-green-700">α = {alpha.toFixed(2)}</span>
                </label>
                <select
                  value={texture}
                  onChange={(e) => setTexture(e.target.value)}
                  className="w-full px-3 py-2.5 border border-green-200 rounded-lg text-sm bg-white focus:outline-none focus:border-green-500"
                >
                  <option value="loam">Loam (Sandy Clay)  — α 0.85</option>
                  <option value="clay">Clay               — α 1.10</option>
                  <option value="sandy">Sandy              — α 0.65</option>
                  <option value="silt">Silty Clay         — α 1.00</option>
                </select>
              </div>

              <SliderRow
                label="Field Area"
                value={fieldArea}
                min={100} max={2000} step={50}
                onChange={setFieldArea}
                unit=" m²"
              />
            </div>

            {/* Results */}
            <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm">
              <h2 className="text-sm font-semibold text-green-900 mb-4">Results</h2>
              <div className="grid grid-cols-2 gap-3 mb-5">
                <ResultCard label="Soil Moisture Deficit" value={`${smd}%`} />
                <ResultCard label="Irrigation Required"   value={`${ir} L/m²`} />
                <ResultCard label="Total Water (field)"   value={`${total.toLocaleString()} L`} />
                <ResultCard
                  label="Water Saved"
                  value={`${saved}%`}
                  accent
                  sub={<span className={`text-xs font-semibold ${effColor}`}>{efficiency}</span>}
                />
              </div>

              <AnimatePresence mode="wait">
                {scheduled ? (
                  <motion.div
                    key="confirmed"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-teal-50 border border-teal-100 rounded-xl p-4 text-center text-teal-700 text-sm font-medium"
                  >
                    ✓ Irrigation scheduled for 6:00 AM tomorrow · {ir} L/m² over {fieldArea} m²
                  </motion.div>
                ) : (
                  <motion.button
                    key="btn"
                    whileTap={{ scale: 0.97 }}
                    onClick={handleSchedule}
                    disabled={scheduleMutation.isPending}
                    className="w-full py-3 bg-teal-700 hover:bg-teal-900 text-white font-semibold rounded-xl transition-all disabled:opacity-60 text-sm"
                  >
                    {scheduleMutation.isPending ? "Scheduling…" : "Schedule Irrigation →"}
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* ── RIGHT: charts ── */}
          <div className="space-y-5">
            <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm">
              <h2 className="text-sm font-semibold text-green-900 mb-1">Weekly Water Usage Comparison</h2>
              <p className="text-xs text-green-500 mb-4">Smart irrigation vs traditional method · L/m²</p>
              <div className="flex gap-4 mb-3 text-xs text-green-600">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded bg-green-700 inline-block" /> Smart Irrigation
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded bg-green-100 inline-block" /> Traditional
                </span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={weeklyData} barCategoryGap="30%">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f4ea" />
                  <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#7a9a5a" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "#7a9a5a" }} axisLine={false} tickLine={false} domain={[0, 28]} />
                  <Tooltip
                    contentStyle={{ background: "#fff", border: "1px solid #c0dd97", borderRadius: 8, fontSize: 13 }}
                    formatter={(v: number) => [`${v} L/m²`]}
                  />
                  <Bar dataKey="smart"       fill="#3b6d11" radius={[4, 4, 0, 0]} name="Smart" />
                  <Bar dataKey="traditional" fill="#c0dd97" radius={[4, 4, 0, 0]} name="Traditional" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Schedule table */}
            <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm">
              <h2 className="text-sm font-semibold text-green-900 mb-4">
                Irrigation Schedule <span className="font-normal text-green-500">— Next 7 days</span>
              </h2>
              <div className="space-y-2">
                {schedule.map((s) => (
                  <div
                    key={s.day}
                    className="flex items-center justify-between bg-green-50/60 rounded-lg px-4 py-2.5"
                  >
                    <span className="text-sm font-semibold text-green-900 w-10">{s.day}</span>
                    <span className="text-xs text-green-600 w-20">{s.time}</span>
                    <span className="text-xs text-green-600 w-20">
                      {s.amount !== null ? `${s.amount} L/m²` : "—"}
                    </span>
                    <span
                      className={`text-xs font-semibold ${
                        s.status === "Rest" ? "text-green-400" : "text-green-700"
                      }`}
                    >
                      {s.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </main>
  );
}

/* ── Helper sub-components ── */

function SliderRow({
  label, value, min, max, step = 1, onChange, unit,
}: {
  label: string; value: number; min: number; max: number; step?: number;
  onChange: (v: number) => void; unit: string;
}) {
  return (
    <div>
      <label className="flex justify-between text-xs font-medium text-green-600 mb-2">
        <span>{label}</span>
        <span className="font-bold text-green-700">{value}{unit}</span>
      </label>
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}

function ResultCard({
  label, value, accent, sub,
}: {
  label: string; value: string; accent?: boolean; sub?: React.ReactNode;
}) {
  return (
    <div
      className={`rounded-xl p-4 text-center border ${
        accent ? "bg-teal-50 border-teal-100" : "bg-green-50 border-green-100"
      }`}
    >
      <p className={`text-2xl font-bold mb-0.5 ${accent ? "text-teal-700" : "text-green-800"}`}>
        {value}
      </p>
      <p className="text-xs text-green-500">{label}</p>
      {sub && <div className="mt-1">{sub}</div>}
    </div>
  );
}
