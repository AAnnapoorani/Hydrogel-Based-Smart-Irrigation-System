"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import { api, ApiService } from "@/lib/api";
import { Sprout, ChevronDown, ChevronUp, CheckCircle2, ArrowRight } from "lucide-react";

interface SoilResult {
  fertility_score: number;
  classification: "High" | "Medium" | "Low";
  nutrient_scores: Record<string, number>;
  recommended_crops: { name: string; match_score: number }[];
  recommendations: string[];
}

interface CropMLResult {
  recommended_crop: string;
  confidence: number;
  model_name: string;
  top_candidates: { crop: string; probability: number }[];
  hydrogel_compatibility: string;
  notes: string;
}

interface ContainerSoilResult {
  container_potting_mix: string;
  overall_fertility_index: number;
  fertility_grade: string;
  readings: Array<{
    parameter: string;
    reading_value: number;
    unit: string;
    status: string;
    calibrated_range: string;
    sensor_tolerance: string;
    interpretation: string;
    organic_remediation?: string;
  }>;
  hydrogel_retention_effect: string;
  plant_specific_advisories: Array<{
    plant: string;
    optimal_ph: string;
    growth_stage?: string;
    stage_specific_demand?: string;
  }>;
  sensor_accuracy_notice: string;
}

const classColors = {
  High:   { bg: "bg-emerald-50",  text: "text-emerald-700", ring: "#10b981", badge: "bg-emerald-50 text-emerald-800 border-emerald-200" },
  Medium: { bg: "bg-amber-50",    text: "text-amber-700",   ring: "#f59e0b", badge: "bg-amber-50 text-amber-800 border-amber-200" },
  Low:    { bg: "bg-rose-50",     text: "text-rose-700",    ring: "#ef4444", badge: "bg-rose-50 text-rose-800 border-rose-200" },
};

export default function SoilPage() {
  const [form, setForm] = useState({
    nitrogen: "85",
    phosphorus: "42",
    potassium: "210",
    ph: "6.8",
    organic_carbon: "0.82",
    soil_texture: "loam",
    temperature: "31.5",
    humidity: "68",
    rainfall: "115"
  });

  const [showClimate, setShowClimate] = useState(false);
  const [soilResult, setSoilResult] = useState<SoilResult | null>(null);
  const [mlResult, setMlResult] = useState<CropMLResult | null>(null);
  const [containerResult, setContainerResult] = useState<ContainerSoilResult | null>(null);

  const mutation = useMutation({
    mutationFn: async (data: typeof form) => {
      // 1. Call standard soil fertility analyzer
      const soilPromise = api.post("/soil/analyze", {
        nitrogen: parseFloat(data.nitrogen),
        phosphorus: parseFloat(data.phosphorus),
        potassium: parseFloat(data.potassium),
        ph: parseFloat(data.ph),
        organic_carbon: parseFloat(data.organic_carbon),
        soil_texture: data.soil_texture,
      });

      // 2. Call ML Crop Recommendation Model (Random Forest Classifier)
      const mlPromise = ApiService.predictCrop({
        nitrogen: parseFloat(data.nitrogen),
        phosphorus: parseFloat(data.phosphorus),
        potassium: parseFloat(data.potassium),
        ph: parseFloat(data.ph),
        organic_carbon: parseFloat(data.organic_carbon),
        temperature: parseFloat(data.temperature),
        humidity: parseFloat(data.humidity),
        rainfall: parseFloat(data.rainfall),
        soil_type: data.soil_texture
      }).catch(err => {
        console.warn("ML Crop prediction fallback:", err);
        return null;
      });

      // 3. Call Terrace Garden Container Potting Mix Evaluator
      const containerPromise = ApiService.evaluateSoilPottingMix({
        nitrogen: parseFloat(data.nitrogen),
        phosphorus: parseFloat(data.phosphorus),
        potassium: parseFloat(data.potassium),
        ph: parseFloat(data.ph),
        organic_carbon: parseFloat(data.organic_carbon),
        soil_texture: data.soil_texture,
      }, {
        plant_type: "Tomato",
        growth_stage: "Vegetative",
        moisture: 58.0,
        hydrogel_present: true
      }).catch(err => {
        console.warn("Terrace container soil evaluation fallback:", err);
        return null;
      });

      const [soilRes, mlRes, containerRes] = await Promise.all([soilPromise, mlPromise, containerPromise]);
      return {
        soil: soilRes.data as SoilResult,
        ml: mlRes as CropMLResult | null,
        container: containerRes as ContainerSoilResult | null
      };
    },
    onSuccess: (res) => {
      setSoilResult(res.soil);
      setMlResult(res.ml);
      setContainerResult(res.container);
    },
  });

  const fields = [
    { key: "nitrogen",       label: "Nitrogen (N)",      unit: "mg/kg", hint: "Optimal: 80–120" },
    { key: "phosphorus",     label: "Phosphorus (P)",     unit: "mg/kg", hint: "Optimal: 30–60"  },
    { key: "potassium",      label: "Potassium (K)",      unit: "mg/kg", hint: "Optimal: 120–250"},
    { key: "ph",             label: "pH Level",           unit: "",       hint: "Optimal: 6.0–7.5"},
    { key: "organic_carbon", label: "Organic Carbon",     unit: "%",      hint: "Target: >0.75%" },
  ];

  const circumference = 2 * Math.PI * 52;

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Soil Health & ML Crop Intelligence
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Agronomic fertility scoring combined with Random Forest multi-class crop suitability analysis.
          </p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200/80 px-3 py-1.5 rounded-lg text-xs font-medium text-emerald-900 shadow-soft">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Random Forest Classifier (Accuracy 87.5%, F1 0.875)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Card */}
        <motion.div
          className="lg:col-span-5 bg-white rounded-xl border border-slate-200/80 p-5 sm:p-6 shadow-soft h-fit"
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
            <h2 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Physicochemical Parameters
            </h2>
            <span className="text-xs text-slate-400">Standard Test Protocol</span>
          </div>

          <div className="grid grid-cols-2 gap-3.5">
            {fields.map((f) => (
              <div key={f.key} className={f.key === "organic_carbon" ? "col-span-2" : ""}>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  {f.label} {f.unit && <span className="text-slate-400 text-[11px]">({f.unit})</span>}
                </label>
                <input
                  type="number"
                  step={f.key === "ph" ? "0.1" : f.key === "organic_carbon" ? "0.01" : "1"}
                  value={form[f.key as keyof typeof form]}
                  onChange={(e) => setForm((prev) => ({ ...prev, [f.key]: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 transition-colors placeholder:text-slate-400"
                />
                <p className="text-[11px] text-slate-400 mt-0.5">{f.hint}</p>
              </div>
            ))}
          </div>

          <div className="mt-4">
            <label className="block text-xs font-medium text-slate-700 mb-1">Soil Texture Class</label>
            <select
              value={form.soil_texture}
              onChange={(e) => setForm((prev) => ({ ...prev, soil_texture: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 transition-colors"
            >
              <option value="clay">Clay (High Water Holding)</option>
              <option value="loam">Loam / Sandy Clay (Balanced Drainage)</option>
              <option value="sandy">Sandy (Fast Drainage - High Hydrogel Benefit)</option>
              <option value="silt">Silty Clay (Moderate Drainage)</option>
            </select>
          </div>

          {/* Environmental parameters collapsible */}
          <div className="mt-4 pt-3.5 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setShowClimate(!showClimate)}
              className="flex items-center justify-between w-full text-xs font-medium text-slate-700 hover:text-slate-900 transition-colors py-1"
            >
              <span className="flex items-center gap-1.5">
                🌤️ Climate Context for ML ({showClimate ? "Hide" : "Show"})
              </span>
              <span className="text-slate-400">{showClimate ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}</span>
            </button>

            {showClimate && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="grid grid-cols-3 gap-2.5 mt-3 pt-2"
              >
                <div>
                  <label className="block text-[11px] font-medium text-slate-500 mb-1">Temp (°C)</label>
                  <input
                    type="number"
                    value={form.temperature}
                    onChange={(e) => setForm((prev) => ({ ...prev, temperature: e.target.value }))}
                    className="w-full px-2 py-1.5 border border-slate-200 rounded-lg text-xs bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-500 mb-1">Humidity (%)</label>
                  <input
                    type="number"
                    value={form.humidity}
                    onChange={(e) => setForm((prev) => ({ ...prev, humidity: e.target.value }))}
                    className="w-full px-2 py-1.5 border border-slate-200 rounded-lg text-xs bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-500 mb-1">Rain (mm)</label>
                  <input
                    type="number"
                    value={form.rainfall}
                    onChange={(e) => setForm((prev) => ({ ...prev, rainfall: e.target.value }))}
                    className="w-full px-2 py-1.5 border border-slate-200 rounded-lg text-xs bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
                  />
                </div>
              </motion.div>
            )}
          </div>

          <button
            onClick={() => mutation.mutate(form)}
            disabled={mutation.isPending}
            className="w-full mt-5 py-2.5 bg-emerald-700 hover:bg-emerald-800 active:bg-emerald-900 text-white font-medium rounded-lg shadow-soft transition-colors disabled:opacity-60 flex items-center justify-center gap-2 text-sm"
          >
            {mutation.isPending ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Executing ML Pipeline…
              </>
            ) : (
              <>
                Analyze Health & Recommend Crop
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
          {mutation.isError && (
            <p className="text-rose-600 text-xs mt-2 text-center">Analysis request failed. Please check backend connection.</p>
          )}
        </motion.div>

        {/* Results Column */}
        <div className="lg:col-span-7 space-y-6">
          <AnimatePresence mode="wait">
            {mutation.isPending && (
              <motion.div
                key="skeleton"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="bg-white rounded-xl border border-slate-200/80 p-8 shadow-soft space-y-4"
              >
                <div className="h-5 w-40 bg-slate-100 rounded animate-pulse" />
                <div className="h-28 bg-slate-100 rounded-xl animate-pulse" />
                <div className="h-24 bg-slate-100 rounded-xl animate-pulse" />
              </motion.div>
            )}

            {!mutation.isPending && !soilResult && (
              <motion.div
                key="empty"
                className="bg-white rounded-xl border border-dashed border-slate-200 p-12 text-center flex flex-col items-center justify-center min-h-[400px] shadow-soft"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60 flex items-center justify-center mb-3">
                  <Sprout className="w-6 h-6" />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-1">Awaiting Soil Sample Input</h3>
                <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
                  Provide macronutrients and soil texture on the left panel to execute agronomic fertility scoring and Random Forest crop recommendation.
                </p>
              </motion.div>
            )}

            {soilResult && !mutation.isPending && (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* 1. ML Crop Recommendation Card */}
                {mlResult && (
                  <div className="bg-slate-900 border border-slate-800 text-white rounded-xl p-5 sm:p-6 shadow-soft">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs uppercase tracking-wider font-semibold text-emerald-400 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                        AI Crop Recommendation (Random Forest)
                      </span>
                      <span className="text-xs bg-white/10 border border-white/15 px-2.5 py-0.5 rounded-full text-slate-200">
                        Confidence: {(mlResult.confidence * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-3 mb-4">
                      <div>
                        <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                          {mlResult.recommended_crop}
                        </h3>
                        <p className="text-xs text-slate-300 mt-1 leading-relaxed">{mlResult.notes}</p>
                      </div>
                      <div className="bg-white/5 rounded-lg p-3 border border-white/10 text-left sm:text-right shrink-0">
                        <p className="text-[10px] text-slate-400 uppercase font-medium">Hydrogel Regime</p>
                        <p className="text-xs font-semibold text-emerald-300 mt-0.5">{mlResult.hydrogel_compatibility}</p>
                      </div>
                    </div>

                    {/* Ranked Probability candidates */}
                    <div className="mt-4 pt-3.5 border-t border-slate-800">
                      <p className="text-xs font-semibold text-slate-300 mb-2">
                        Alternative Candidates & Model Probabilities:
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        {mlResult.top_candidates.map((c, i) => (
                          <div
                            key={c.crop}
                            className={`p-2.5 rounded-lg border ${
                              i === 0
                                ? "bg-white/10 border-emerald-500/50"
                                : "bg-white/5 border-white/5"
                            }`}
                          >
                            <div className="flex justify-between text-xs font-medium mb-1">
                              <span className={i === 0 ? "font-semibold text-white" : "text-slate-300"}>
                                #{i + 1} {c.crop}
                              </span>
                              <span className="font-mono text-emerald-300 text-[11px]">
                                {(c.probability * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-emerald-500 rounded-full"
                                style={{ width: `${Math.max(5, c.probability * 100)}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. Agronomic Fertility Analysis Card */}
                <div className="bg-white rounded-xl border border-slate-200/80 p-5 sm:p-6 shadow-soft">
                  <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
                    <h2 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                      Agronomic Soil Fertility Index
                    </h2>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                        classColors[soilResult.classification].badge
                      }`}
                    >
                      {soilResult.classification} Fertility Tier
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                    {/* Gauge */}
                    <div className="md:col-span-5 flex flex-col items-center justify-center">
                      <svg width="130" height="130" style={{ transform: "rotate(-90deg)" }}>
                        <circle cx="65" cy="65" r="50" fill="none" stroke="#f1f5f9" strokeWidth="9" />
                        <circle
                          cx="65"
                          cy="65"
                          r="50"
                          fill="none"
                          stroke={classColors[soilResult.classification].ring}
                          strokeWidth="9"
                          strokeLinecap="round"
                          strokeDasharray={`${(soilResult.fertility_score / 100) * (2 * Math.PI * 50)} ${2 * Math.PI * 50}`}
                          style={{ transition: "stroke-dasharray 0.8s ease" }}
                        />
                      </svg>
                      <div className="-mt-22 text-center">
                        <p
                          className="text-3xl font-bold tracking-tight"
                          style={{ color: classColors[soilResult.classification].ring }}
                        >
                          {soilResult.fertility_score}
                        </p>
                        <p className="text-[11px] text-slate-400 font-medium">Index Score / 100</p>
                      </div>
                    </div>

                    {/* Nutrient bars */}
                    <div className="md:col-span-7 space-y-2.5">
                      {Object.entries(soilResult.nutrient_scores).map(([key, val]) => (
                        <div key={key}>
                          <div className="flex justify-between text-xs text-slate-700 font-medium mb-1">
                            <span className="capitalize">{key.replace("_", " ")}</span>
                            <span className="font-mono text-slate-500">{val}%</span>
                          </div>
                          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <motion.div
                              className="h-full bg-emerald-600 rounded-full"
                              initial={{ width: 0 }}
                              animate={{ width: `${val}%` }}
                              transition={{ duration: 0.6, ease: "easeOut" }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommendations */}
                  <div className="mt-5 pt-3.5 border-t border-slate-100">
                    <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                      Agronomic Amendments & Guidance
                    </h4>
                    <ul className="space-y-1.5">
                      {soilResult.recommendations.map((r, i) => (
                        <li key={i} className="flex gap-2 text-xs text-slate-600 leading-relaxed">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* 3. Terrace Garden Potting Mix Calibration Card */}
                {containerResult && (
                  <div className="bg-white rounded-xl border border-emerald-100 p-5 sm:p-6 shadow-soft space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" />
                          <h3 className="text-sm font-bold text-slate-900">
                            15L Container Potting Mix Evaluation
                          </h3>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {containerResult.container_potting_mix}
                        </p>
                      </div>
                      <span className="self-start sm:self-auto px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {containerResult.fertility_grade} ({containerResult.overall_fertility_index}/100)
                      </span>
                    </div>

                    {/* Potting Mix Parameter Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {containerResult.readings.map((reading) => (
                        <div
                          key={reading.parameter}
                          className="p-3 rounded-lg border border-slate-200/80 bg-slate-50/50"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-semibold text-slate-800">
                              {reading.parameter}
                            </span>
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                reading.status.includes("Optimal")
                                  ? "bg-emerald-100 text-emerald-800"
                                  : reading.status.includes("Deficient")
                                  ? "bg-rose-100 text-rose-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}
                            >
                              {reading.status}
                            </span>
                          </div>
                          <p className="text-sm font-mono font-bold text-slate-900">
                            {reading.reading_value} {reading.unit}
                            <span className="text-[10px] text-slate-500 font-normal ml-1.5">
                              (Target: {reading.calibrated_range})
                            </span>
                          </p>
                          <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                            {reading.interpretation}
                          </p>
                          {reading.organic_remediation && (
                            <p className="text-[11px] text-emerald-800 font-medium mt-1.5 pt-1.5 border-t border-slate-200/60 flex items-start gap-1">
                              <span>🌱</span>
                              <span>{reading.organic_remediation}</span>
                            </p>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* Hydrogel Retention Banner */}
                    <div className="p-3.5 rounded-xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200/80">
                      <div className="flex items-center gap-1.5 mb-1">
                        <span className="text-xs">💧</span>
                        <h4 className="text-xs font-bold text-emerald-950 uppercase tracking-wide">
                          Hydrogel (SAP) Cation Retention Buffer
                        </h4>
                      </div>
                      <p className="text-xs text-emerald-900 leading-relaxed">
                        {containerResult.hydrogel_retention_effect}
                      </p>
                    </div>

                    {/* Sensor Accuracy Notice */}
                    <p className="text-[10px] text-slate-400 italic leading-relaxed">
                      {containerResult.sensor_accuracy_notice}
                    </p>

                    {/* Link to Terrace Recommender */}
                    <div className="pt-2 flex justify-end">
                      <a
                        href="/recommender"
                        className="inline-flex items-center gap-2 text-xs font-semibold px-3.5 py-2 rounded-lg bg-emerald-700 text-white hover:bg-emerald-800 transition-colors shadow-soft"
                      >
                        Explore Suitable Terrace Plants For This Medium
                        <ArrowRight className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </main>
  );
}
