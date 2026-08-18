"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface SoilResult {
  fertility_score: number;
  classification: "High" | "Medium" | "Low";
  nutrient_scores: Record<string, number>;
  recommended_crops: { name: string; match_score: number }[];
  recommendations: string[];
}

const classColors = {
  High:   { bg: "bg-green-50",  text: "text-green-700",  ring: "#3b6d11" },
  Medium: { bg: "bg-amber-50",  text: "text-amber-600",  ring: "#ba7517" },
  Low:    { bg: "bg-red-50",    text: "text-red-600",    ring: "#e24b4a" },
};

export default function SoilPage() {
  const [form, setForm] = useState({ nitrogen:"85", phosphorus:"42", potassium:"210", ph:"6.8", organic_carbon:"0.82", soil_texture:"loam" });
  const [result, setResult] = useState<SoilResult | null>(null);

  const mutation = useMutation({
    mutationFn: (data: typeof form) => api.post("/soil/analyze", {
      nitrogen: parseFloat(data.nitrogen),
      phosphorus: parseFloat(data.phosphorus),
      potassium: parseFloat(data.potassium),
      ph: parseFloat(data.ph),
      organic_carbon: parseFloat(data.organic_carbon),
      soil_texture: data.soil_texture,
    }),
    onSuccess: (res) => setResult(res.data),
  });

  const fields = [
    { key:"nitrogen",      label:"Nitrogen (N)",      unit:"mg/kg", hint:"Optimal: 80–120" },
    { key:"phosphorus",    label:"Phosphorus (P)",     unit:"mg/kg", hint:"Optimal: 30–60"  },
    { key:"potassium",     label:"Potassium (K)",      unit:"mg/kg", hint:"Optimal: 120–250"},
    { key:"ph",            label:"pH Level",           unit:"",       hint:"Optimal: 6.0–7.5"},
    { key:"organic_carbon",label:"Organic Carbon",     unit:"%",      hint:"Target: >0.75%" },
  ];

  const circumference = 2 * Math.PI * 52;

  return (
    <main className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-serif font-bold text-green-950 mb-1">Soil Analysis</h1>
      <p className="text-green-700 text-sm mb-8">Enter your soil test values for fertility classification and crop recommendations.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input Card */}
        <motion.div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm"
          initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}>
          <h2 className="text-sm font-semibold text-green-900 mb-5">Soil Parameters</h2>

          <div className="grid grid-cols-2 gap-4">
            {fields.map(f => (
              <div key={f.key} className={f.key === "organic_carbon" ? "col-span-2" : ""}>
                <label className="block text-xs font-medium text-green-600 mb-1.5">
                  {f.label} {f.unit && <span className="text-green-400">{f.unit}</span>}
                </label>
                <input
                  type="number"
                  step={f.key === "ph" ? "0.1" : f.key === "organic_carbon" ? "0.01" : "1"}
                  value={form[f.key as keyof typeof form]}
                  onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                  className="w-full px-3 py-2.5 border border-green-200 rounded-lg text-sm focus:outline-none focus:border-green-500 transition-colors"
                />
                <p className="text-xs text-green-400 mt-1">{f.hint}</p>
              </div>
            ))}
          </div>

          <div className="mt-4">
            <label className="block text-xs font-medium text-green-600 mb-1.5">Soil Texture</label>
            <select
              value={form.soil_texture}
              onChange={e => setForm(prev => ({ ...prev, soil_texture: e.target.value }))}
              className="w-full px-3 py-2.5 border border-green-200 rounded-lg text-sm bg-white focus:outline-none focus:border-green-500"
            >
              <option value="clay">Clay</option>
              <option value="loam">Loam (Sandy Clay)</option>
              <option value="sandy">Sandy</option>
              <option value="silt">Silty Clay</option>
            </select>
          </div>

          <button
            onClick={() => mutation.mutate(form)}
            disabled={mutation.isPending}
            className="w-full mt-5 py-3 bg-green-700 hover:bg-green-900 text-white font-semibold rounded-xl transition-all disabled:opacity-60"
          >
            {mutation.isPending ? "Analyzing…" : "Analyze Soil →"}
          </button>
          {mutation.isError && <p className="text-red-500 text-sm mt-2 text-center">Analysis failed. Please try again.</p>}
        </motion.div>

        {/* Result Card */}
        <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm min-h-80">
          <AnimatePresence mode="wait">
            {mutation.isPending && (
              <motion.div key="skeleton" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="space-y-3 mt-4">
                  {[140,20,80,120].map((h, i) => (
                    <div key={i} className="bg-green-50 rounded-xl animate-pulse" style={{ height: h }} />
                  ))}
                </div>
              </motion.div>
            )}

            {!mutation.isPending && !result && (
              <motion.div key="empty" className="flex flex-col items-center justify-center h-full py-16 text-green-400"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <span className="text-6xl mb-3">🧪</span>
                <p className="text-sm text-center">Enter soil parameters and<br/>click Analyze Soil to see results</p>
              </motion.div>
            )}

            {result && !mutation.isPending && (
              <motion.div key="result" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <h2 className="text-sm font-semibold text-green-900 mb-4">Analysis Results</h2>

                {/* Gauge */}
                <div className="flex flex-col items-center mb-5">
                  <svg width="140" height="140" style={{ transform: "rotate(-90deg)" }}>
                    <circle cx="70" cy="70" r="58" fill="none" stroke="#eaf3de" strokeWidth="10"/>
                    <circle cx="70" cy="70" r="58" fill="none" stroke={classColors[result.classification].ring} strokeWidth="10" strokeLinecap="round" strokeDasharray={`${(result.fertility_score / 100) * circumference} ${circumference}`} style={{ transition: "stroke-dasharray 1s ease" }}/>
                  </svg>
                  {/* Score text centered inside the ring */}
                  <div className="-mt-24 text-center" style={{ zIndex: 1 }}>
                    <p className="text-4xl font-bold" style={{ color: classColors[result.classification].ring }}>
                      {result.fertility_score}
                    </p>
                    <p className="text-xs text-green-500 mt-0.5">Fertility Score</p>
                  </div>
                  <span className={`mt-10 px-4 py-1 rounded-full text-sm font-semibold ${classColors[result.classification].bg} ${classColors[result.classification].text}`}>
                    {result.classification} Fertility
                  </span>
                </div>

                {/* Nutrient bars */}
                <div className="space-y-2 mb-4">
                  {Object.entries(result.nutrient_scores).map(([key, val]) => (
                    <div key={key}>
                      <div className="flex justify-between text-xs text-green-600 mb-1">
                        <span className="capitalize">{key.replace("_"," ")}</span>
                        <span>{val}%</span>
                      </div>
                      <div className="h-2 bg-green-50 rounded-full overflow-hidden">
                        <motion.div className="h-full bg-green-600 rounded-full"
                          initial={{ width: 0 }} animate={{ width: `${val}%` }} transition={{ duration: 0.8, ease: "easeOut" }} />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Crops */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {result.recommended_crops.slice(0, 3).map(c => (
                    <span key={c.name} className="bg-green-50 text-green-700 text-xs font-semibold px-3 py-1 rounded-full">{c.name} {c.match_score}</span>
                  ))}
                </div>

                {/* Recs */}
                <ul className="space-y-2">
                  {result.recommendations.map((r, i) => (
                    <li key={i} className="flex gap-2 text-xs text-green-700">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5 flex-shrink-0" />
                      {r}
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </main>
  );
}
