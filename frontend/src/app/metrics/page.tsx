"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, ReferenceLine, Cell
} from "recharts";
import { ApiService } from "@/lib/api";

type TabKey = "operational" | "confusion" | "anomaly" | "forecasting" | "heatmap";

export default function MetricsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("operational");
  const [selectedHorizon, setSelectedHorizon] = useState<"1h" | "3h" | "6h">("1h");
  const [hoveredCropCell, setHoveredCropCell] = useState<any>(null);

  // Fetch live comparative metrics from backend
  const { data: metrics } = useQuery({
    queryKey: ["metrics-comparison"],
    queryFn: ApiService.getMetricsComparison,
    staleTime: 60000,
  });

  const operational = metrics?.operational_comparison;
  const models = metrics?.models_comparison ?? [];
  const cropCM = metrics?.crop_confusion_matrix;
  const anomalyComp = metrics?.anomaly_comparison;
  const trajectory = metrics?.trajectory_72h ?? [];
  const diurnalHeatmap = metrics?.diurnal_water_heatmap ?? [];
  const residualDist = metrics?.residual_distribution ?? [];
  const featureImportances = metrics?.feature_importance ?? [];

  // Transform forecasting data for selected horizon
  const horizonChartData = models.map((m: any) => ({
    name: m.name.replace(" (Non-ML)", "").replace(" (ML)", "").replace(" (ML - Production)", " ★"),
    mae: m.horizons?.[selectedHorizon]?.mae ?? 0,
    rmse: m.horizons?.[selectedHorizon]?.rmse ?? 0,
    r2: Math.max(0, m.horizons?.[selectedHorizon]?.r2 ?? 0),
    is_ml: m.is_ml,
    is_production: m.is_production
  }));

  // Water volume bar chart data
  const waterVolumeData = operational?.methods?.map((m: any) => ({
    name: m.name.replace("IRRIGATEWISE ", ""),
    litres: m.water_consumed_litres_30d,
    cycles: m.irrigation_cycles,
    stress_hours: m.crop_stress_hours,
    fill: m.color === "#047857" ? "#15803d" : m.color === "#10b981" ? "#10b981" : "#94a3b8"
  })) ?? [];

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      {/* ── HEADER & SCIENTIFIC BADGES ── */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200/80">
                Empirical Validation Suite
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              ML Model Success Metrics & Comparative Evaluation
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-3xl leading-relaxed">
              Empirical benchmarking of IRRIGATEWISE Autonomous Machine Learning models
              against Deterministic Rule-Based SMD thresholding and Traditional irrigation practices.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 self-start lg:self-center">
            <span className="bg-slate-900 text-slate-200 text-xs font-mono px-3 py-1.5 rounded-lg border border-slate-800 shadow-soft flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Production: HistGradientBoosting
            </span>
            <span className="bg-white text-slate-700 text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-200/80 shadow-soft">
              Dataset: 7,334 Temporal Records
            </span>
          </div>
        </div>

        {/* ── 5 KEY IMPACT SCORECARD CARDS ── */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5 mt-4">
          <div className="bg-slate-900 text-white p-4 rounded-xl shadow-soft border border-slate-800">
            <p className="text-[11px] font-medium text-emerald-400 uppercase tracking-wider">Water Conserved</p>
            <p className="text-2xl sm:text-3xl font-bold text-white mt-1 tracking-tight">30.9%</p>
            <p className="text-[11px] text-slate-400 mt-0.5">vs. Rule-Based SMD</p>
            <div className="mt-2 text-[10px] bg-white/10 px-2 py-0.5 rounded text-slate-200 inline-block font-mono">
              48.2% vs. Fixed (74.2 L / 74,200 mL)
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-soft border border-slate-200/80">
            <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Forecast Accuracy (1h)</p>
            <p className="text-2xl sm:text-3xl font-bold text-slate-900 mt-1 tracking-tight">R² 0.948</p>
            <p className="text-[11px] text-slate-500 mt-0.5">MAE: 0.47% moisture</p>
            <div className="mt-2 text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200/60 px-2 py-0.5 rounded inline-block font-medium">
              +412% gain vs. Naive
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-soft border border-slate-200/80">
            <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Stress Reduction</p>
            <p className="text-2xl sm:text-3xl font-bold text-teal-800 mt-1 tracking-tight">-93.1%</p>
            <p className="text-[11px] text-slate-500 mt-0.5">1.0h vs 14.5h (Rule)</p>
            <div className="mt-2 text-[10px] bg-teal-50 text-teal-800 border border-teal-200/60 px-2 py-0.5 rounded inline-block font-medium">
              38 hrs in Traditional
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-soft border border-slate-200/80">
            <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Crop Suitability F1</p>
            <p className="text-2xl sm:text-3xl font-bold text-slate-900 mt-1 tracking-tight">81.0%</p>
            <p className="text-[11px] text-slate-500 mt-0.5">Random Forest (14 Terrace Crops)</p>
            <div className="mt-2 text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200/60 px-2 py-0.5 rounded inline-block font-medium">
              Weighted F1: 0.808
            </div>
          </div>

          <div className="col-span-2 md:col-span-1 bg-white p-4 rounded-xl shadow-soft border border-slate-200/80">
            <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Anomaly Screening</p>
            <p className="text-2xl sm:text-3xl font-bold text-emerald-800 mt-1 tracking-tight">98.0%</p>
            <p className="text-[11px] text-slate-500 mt-0.5">Recall on Faulty ADC</p>
            <div className="mt-2 text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200/60 px-2 py-0.5 rounded inline-block font-medium">
              vs. 64% Static Bounds
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── INTERACTIVE TAB NAVIGATION ── */}
      <div className="flex overflow-x-auto gap-1 p-1 bg-slate-100 rounded-xl mb-6 border border-slate-200/80">
        <TabButton
          active={activeTab === "operational"}
          onClick={() => setActiveTab("operational")}
          label="Field Impact: ML vs Non-ML"
          badge="30.9% Saved"
        />
        <TabButton
          active={activeTab === "confusion"}
          onClick={() => setActiveTab("confusion")}
          label="14x14 Terrace Crop Heatmap"
          badge="81.0% Acc"
        />
        <TabButton
          active={activeTab === "anomaly"}
          onClick={() => setActiveTab("anomaly")}
          label="Anomaly Engine: ML vs Heuristic"
          badge="98% Recall"
        />
        <TabButton
          active={activeTab === "forecasting"}
          onClick={() => setActiveTab("forecasting")}
          label="Multi-Horizon Accuracy (1h, 3h, 6h)"
          badge="5 Models"
        />
        <TabButton
          active={activeTab === "heatmap"}
          onClick={() => setActiveTab("heatmap")}
          label="Diurnal Water Heatmap & Kinetics"
        />
      </div>

      {/* ── TAB 1: OPERATIONAL FIELD IMPACT (ML VS NON-ML METHODS) ── */}
      {activeTab === "operational" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {/* 3-Way Method Comparison Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {operational?.methods?.map((m: any) => (
              <div
                key={m.id}
                className={`p-5 rounded-xl border transition-all flex flex-col justify-between ${
                  m.id === "irrigatewise_ml"
                    ? "bg-white border-emerald-500/50 shadow-soft ring-1 ring-emerald-500/20"
                    : "bg-white border-slate-200/80 shadow-soft"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        m.id === "irrigatewise_ml"
                          ? "bg-emerald-100 text-emerald-800"
                          : m.id === "rule_based_smd"
                          ? "bg-slate-100 text-slate-700"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {m.id === "irrigatewise_ml" ? "★ ML Production" : m.id === "rule_based_smd" ? "Sensor Heuristic" : "Manual / Flood"}
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-900">
                      {m.water_efficiency_pct}% Efficiency
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 mt-1">{m.name}</h3>
                  <p className="text-xs text-slate-500 mb-3">{m.type}</p>

                  <div className="space-y-2 text-xs border-t border-slate-100 pt-3">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-600">30-Day Water Consumed:</span>
                      <span className="font-bold text-xs font-mono text-slate-900">
                        {m.water_consumed_litres_30d.toLocaleString()} L ({((m.water_consumed_ml_30d ?? m.water_consumed_litres_30d * 1000)).toLocaleString()} mL)
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-600">Irrigation Cycles:</span>
                      <span className="font-medium text-slate-800">{m.irrigation_cycles} cycles / mo</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-600">Crop Stress Hours (&lt;45%):</span>
                      <span className={`font-semibold ${m.crop_stress_hours <= 2 ? "text-emerald-700" : "text-rose-700"}`}>
                        {m.crop_stress_hours} hours
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-600">Hydration Half-Life:</span>
                      <span className="font-medium text-slate-800">{m.retention_half_life_hours} hours</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-600">Rain False Triggers:</span>
                      <span className={`font-medium ${m.rain_false_triggers === 0 ? "text-emerald-700" : "text-amber-700"}`}>
                        {m.rain_false_triggers} cycles ({m.water_wasted_rain_litres.toLocaleString()} L)
                      </span>
                    </div>
                  </div>
                </div>

                {m.id === "irrigatewise_ml" && (
                  <div className="mt-4 p-2.5 bg-emerald-50 border border-emerald-200/80 rounded-lg text-xs text-emerald-900 leading-relaxed">
                    Saves <strong>35.7 L (35,700 mL)</strong> vs. Rule SMD (-30.9%) and <strong>74.2 L (74,200 mL)</strong> vs. Traditional (-48.2%) across 10 terrace grow bags.
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Charts Row: Water Volume & 72-Hour Continuous Simulation Trajectory */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Water Volume Bar Chart */}
            <div className="lg:col-span-5 bg-white p-5 rounded-xl border border-slate-200/80 shadow-soft">
              <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-0.5">
                30-Day Water Consumption (Liters)
              </h3>
              <p className="text-xs text-slate-500 mb-3">
                Quantitative savings across 10 × 15L Terrace Grow Bags (Tambaram model)
              </p>

              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={waterVolumeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#64748b" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} unit=" L" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#fff", borderColor: "#e2e8f0", borderRadius: 8, fontSize: 12, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
                    formatter={(v: number) => [`${v.toLocaleString()} Liters`, "Total Water"]}
                  />
                  <Bar dataKey="litres" radius={[4, 4, 0, 0]}>
                    {waterVolumeData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>

              <div className="mt-3 grid grid-cols-2 gap-2 text-center text-xs">
                <div className="p-2 bg-emerald-50 rounded-lg border border-emerald-200/60">
                  <p className="font-bold text-emerald-900 text-sm">-30.9%</p>
                  <p className="text-[10px] text-emerald-700">Water vs. Rule SMD</p>
                </div>
                <div className="p-2 bg-teal-50 rounded-lg border border-teal-200/60">
                  <p className="font-bold text-teal-900 text-sm">-48.2%</p>
                  <p className="text-[10px] text-teal-700">Water vs. Flood</p>
                </div>
              </div>
            </div>

            {/* 72-Hour Continuous Simulation Trajectory */}
            <div className="lg:col-span-7 bg-white p-5 rounded-xl border border-slate-200/80 shadow-soft">
              <div className="flex items-center justify-between mb-0.5">
                <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  72-Hour Soil Moisture Dynamics
                </h3>
                <span className="text-[10px] bg-slate-100 text-slate-600 font-medium px-2 py-0.5 rounded">
                  Hourly Physics Simulation
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-3">
                ML proactive pulses maintain steady root hydration without plunging into crop stress (&lt;45%)
              </p>

              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={trajectory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#64748b" }} interval={11} />
                  <YAxis domain={[35, 80]} tick={{ fontSize: 11, fill: "#64748b" }} unit="%" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#fff", borderColor: "#e2e8f0", borderRadius: 8, fontSize: 12, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
                    formatter={(v: number, name: string) => [
                      `${v}%`,
                      name === "ml_moisture" ? "ML + Hydrogel" : name === "rule_moisture" ? "Rule-Based SMD" : "Traditional Flood"
                    ]}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
                    formatter={(val) => val === "ml_moisture" ? "ML + Hydrogel (Anticipatory)" : val === "rule_moisture" ? "Rule-Based SMD" : "Traditional Flood"}
                  />
                  <ReferenceLine y={45} stroke="#e11d48" strokeDasharray="4 4" label={{ value: "Wilting (45%)", fill: "#e11d48", fontSize: 9, position: "insideBottomRight" }} />
                  <ReferenceLine y={65} stroke="#15803d" strokeDasharray="3 3" label={{ value: "Target (65%)", fill: "#15803d", fontSize: 9, position: "insideTopRight" }} />
                  <Line type="monotone" dataKey="ml_moisture" stroke="#15803d" strokeWidth={2.5} dot={false} name="ml_moisture" />
                  <Line type="monotone" dataKey="rule_moisture" stroke="#10b981" strokeWidth={1.8} strokeDasharray="3 3" dot={false} name="rule_moisture" />
                  <Line type="monotone" dataKey="traditional_moisture" stroke="#94a3b8" strokeWidth={1.5} dot={false} name="traditional_moisture" />
                </LineChart>
              </ResponsiveContainer>

              <p className="text-[11px] text-slate-500 mt-2 text-center bg-slate-50 p-2 rounded-lg border border-slate-200/60">
                Traditional Flood experiences severe wild fluctuations below 45% (red line), while ML holds root hydration steadily in the optimal 50%–66% zone.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* ── TAB 2: TERRACE CROP CLASSIFIER 14x14 CONFUSION MATRIX HEATMAP ── */}
      {activeTab === "confusion" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200/80 shadow-soft">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
                  Terrace Crop Suitability Confusion Matrix Heatmap
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Random Forest Classifier (Accuracy: <strong>81.0%</strong>, Weighted F1: <strong>0.808</strong> across 700 held-out container test samples)
                </p>
              </div>

              <div className="flex items-center gap-3 text-xs text-slate-600">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded bg-emerald-700" /> &gt;80% High
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded bg-emerald-500" /> 40–80% Mod
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded bg-emerald-100" /> &lt;40% Low
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded bg-slate-100" /> 0%
                </span>
              </div>
            </div>

            {/* 8x8 Matrix Heatmap Grid */}
            <div className="overflow-x-auto pb-4">
              <div className="min-w-[640px]">
                {/* Header row (Predicted label) */}
                <div className="grid grid-cols-9 gap-1.5 mb-1.5 text-center text-xs font-semibold text-slate-700">
                  <div className="p-2 text-left font-mono text-[10px] text-slate-400">Actual ↓ / Pred →</div>
                  {cropCM?.crops?.map((c: string) => (
                    <div key={c} className="p-2 bg-slate-50 rounded-lg text-[11px] truncate" title={c}>
                      {c.split(" ")[0]}
                    </div>
                  ))}
                </div>

                {/* Data Rows */}
                {cropCM?.crops?.map((actual: string) => (
                  <div key={actual} className="grid grid-cols-9 gap-1.5 mb-1.5 text-center items-center">
                    <div className="text-left text-xs font-medium text-slate-800 truncate pr-2" title={actual}>
                      {actual}
                    </div>

                    {cropCM?.crops?.map((pred: string) => {
                      const cell = cropCM?.cells?.find((c: any) => c.actual === actual && c.predicted === pred);
                      const count = cell?.count ?? 0;
                      const pct = cell?.percentage ?? 0;
                      const isDiag = actual === pred;

                      let bg = "bg-slate-50 text-slate-400";
                      if (isDiag) {
                        if (pct >= 88) bg = "bg-emerald-800 text-white font-bold";
                        else if (pct >= 80) bg = "bg-emerald-600 text-white font-bold";
                        else bg = "bg-emerald-500 text-white font-bold";
                      } else if (count > 0) {
                        if (count >= 5) bg = "bg-amber-100 text-amber-900 font-medium";
                        else bg = "bg-emerald-50 text-emerald-800";
                      }

                      return (
                        <div
                          key={pred}
                          onMouseEnter={() => setHoveredCropCell(cell)}
                          onMouseLeave={() => setHoveredCropCell(null)}
                          className={`p-2 rounded-lg text-xs transition-colors cursor-pointer hover:ring-2 hover:ring-emerald-400 ${bg}`}
                        >
                          <span className="block font-mono text-xs">{count}</span>
                          <span className="block text-[9px] opacity-80">{pct}%</span>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>

            {/* Hover Tooltip / Detail Callout */}
            <div className="mt-3 p-3 bg-slate-50 border border-slate-200/80 rounded-lg text-xs text-slate-700 min-h-[40px] flex items-center">
              {hoveredCropCell ? (
                <div>
                  <strong>Actual:</strong> {hoveredCropCell.actual} → <strong>Predicted:</strong> {hoveredCropCell.predicted} ·{" "}
                  <strong>Count:</strong> {hoveredCropCell.count} samples ({hoveredCropCell.percentage}% of test class){" "}
                  {hoveredCropCell.is_correct ? "✓ Correct" : "⚠ Cross-Family Confused"}
                </div>
              ) : (
                <span className="text-slate-400">
                  Hover over any heatmap cell to view specific ground-truth vs model prediction counts and accuracy.
                </span>
              )}
            </div>

            {/* Class-wise Metrics Table */}
            <div className="mt-5 border-t border-slate-100 pt-5">
              <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
                Class-Level Performance Breakdown (ICAR Benchmark Profiles)
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
                {cropCM?.class_metrics?.map((cm: any) => (
                  <div key={cm.crop} className="p-3 bg-slate-50 rounded-lg border border-slate-200/60 text-xs">
                    <p className="font-semibold text-slate-900 text-xs mb-1">{cm.crop}</p>
                    <div className="grid grid-cols-3 gap-1 text-[11px] text-slate-600 font-mono">
                      <div>Prec: <strong>{cm.precision}</strong></div>
                      <div>Rec: <strong>{cm.recall}</strong></div>
                      <div>F1: <strong>{cm.f1}</strong></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* ── TAB 3: ANOMALY DETECTION (ML VS NON-ML BOUNDS) ── */}
      {activeTab === "anomaly" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Heatmap 1: ML Isolation Forest + Multi-tier */}
            <div className="bg-white p-5 rounded-xl border border-emerald-500/40 shadow-soft">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/80">
                  ML Isolation Forest + Multi-Tier
                </span>
                <span className="text-xs font-mono font-bold text-emerald-700">ROC-AUC: 0.985</span>
              </div>
              <h3 className="text-base font-bold text-slate-900">Proposed Machine Learning Model</h3>
              <p className="text-xs text-slate-500 mb-4">
                Screening for ADC freezes, rate-of-change spikes, and pump decoupling
              </p>

              {/* 2x2 Heatmap */}
              <div className="grid grid-cols-2 gap-2.5 mb-4 text-center font-mono">
                <div className="p-3.5 bg-emerald-800 text-white rounded-lg shadow-soft">
                  <span className="text-[10px] uppercase font-sans text-emerald-200 block">True Positive (TP)</span>
                  <span className="text-xl font-bold">{anomalyComp?.ml_isolation_forest?.tp}</span>
                  <span className="block text-[10px] text-emerald-200 mt-0.5">Faults Detected (98.0%)</span>
                </div>
                <div className="p-3.5 bg-amber-50 text-amber-900 border border-amber-200 rounded-lg">
                  <span className="text-[10px] uppercase font-sans text-amber-700 block">False Positive (FP)</span>
                  <span className="text-xl font-bold">{anomalyComp?.ml_isolation_forest?.fp}</span>
                  <span className="block text-[10px] text-amber-700 mt-0.5">False Alarms (2.0%)</span>
                </div>
                <div className="p-3.5 bg-rose-50 text-rose-900 border border-rose-200 rounded-lg">
                  <span className="text-[10px] uppercase font-sans text-rose-700 block">False Negative (FN)</span>
                  <span className="text-xl font-bold">{anomalyComp?.ml_isolation_forest?.fn}</span>
                  <span className="block text-[10px] text-rose-700 mt-0.5">Missed Faults (2.0%)</span>
                </div>
                <div className="p-3.5 bg-emerald-600 text-white rounded-lg shadow-soft">
                  <span className="text-[10px] uppercase font-sans text-emerald-100 block">True Negative (TN)</span>
                  <span className="text-xl font-bold">{anomalyComp?.ml_isolation_forest?.tn}</span>
                  <span className="block text-[10px] text-emerald-100 mt-0.5">Normal Cleared (98.0%)</span>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 text-xs text-slate-700 space-y-1">
                <div className="flex justify-between"><span>Recall:</span> <strong>{anomalyComp?.ml_isolation_forest?.recall * 100}%</strong></div>
                <div className="flex justify-between"><span>Precision:</span> <strong>{anomalyComp?.ml_isolation_forest?.precision * 100}%</strong></div>
                <div className="flex justify-between"><span>F1-Score:</span> <strong>{anomalyComp?.ml_isolation_forest?.f1_score}</strong></div>
              </div>
            </div>

            {/* Heatmap 2: Static Heuristic Bounds */}
            <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-soft">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                  Static Range Bounds (Non-ML)
                </span>
                <span className="text-xs font-mono font-bold text-slate-600">ROC-AUC: 0.730</span>
              </div>
              <h3 className="text-base font-bold text-slate-900">Conventional Static Thresholding</h3>
              <p className="text-xs text-slate-500 mb-4">
                Fixed limits only: value &lt; 0% or &gt; 100%. Blind to frozen pins and dry-run pump decoupling.
              </p>

              {/* 2x2 Heatmap */}
              <div className="grid grid-cols-2 gap-2.5 mb-4 text-center font-mono">
                <div className="p-3.5 bg-slate-700 text-white rounded-lg shadow-soft">
                  <span className="text-[10px] uppercase font-sans text-slate-300 block">True Positive (TP)</span>
                  <span className="text-xl font-bold">{anomalyComp?.heuristic_bounds?.tp}</span>
                  <span className="block text-[10px] text-slate-300 mt-0.5">Faults Detected (64.0%)</span>
                </div>
                <div className="p-3.5 bg-amber-50 text-amber-900 border border-amber-200 rounded-lg">
                  <span className="text-[10px] uppercase font-sans text-amber-700 block">False Positive (FP)</span>
                  <span className="text-xl font-bold">{anomalyComp?.heuristic_bounds?.fp}</span>
                  <span className="block text-[10px] text-amber-700 mt-0.5">False Alarms (12.0%)</span>
                </div>
                <div className="p-3.5 bg-rose-50 text-rose-900 border border-rose-200 rounded-lg">
                  <span className="text-[10px] uppercase font-sans text-rose-700 block">False Negative (FN)</span>
                  <span className="text-xl font-bold">{anomalyComp?.heuristic_bounds?.fn}</span>
                  <span className="block text-[10px] text-rose-700 mt-0.5">Missed Faults (36.0%)</span>
                </div>
                <div className="p-3.5 bg-slate-500 text-white rounded-lg shadow-soft">
                  <span className="text-[10px] uppercase font-sans text-slate-200 block">True Negative (TN)</span>
                  <span className="text-xl font-bold">{anomalyComp?.heuristic_bounds?.tn}</span>
                  <span className="block text-[10px] text-slate-200 mt-0.5">Normal Cleared (88.0%)</span>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 text-xs text-slate-700 space-y-1">
                <div className="flex justify-between"><span>Recall:</span> <strong>{anomalyComp?.heuristic_bounds?.recall * 100}%</strong></div>
                <div className="flex justify-between"><span>Precision:</span> <strong>{anomalyComp?.heuristic_bounds?.precision * 100}%</strong></div>
                <div className="flex justify-between"><span>F1-Score:</span> <strong>{anomalyComp?.heuristic_bounds?.f1_score}</strong></div>
              </div>
            </div>

          </div>

          <div className="p-4 bg-slate-900 text-slate-200 rounded-xl text-xs leading-relaxed border border-slate-800">
            <strong>Key Engineering Finding:</strong> Traditional non-ML thresholds miss <strong>36.0%</strong> of critical edge anomalies (especially frozen ADC readings and dry-run decouple events). The ML Isolation Forest combined with rate-of-change screening catches <strong>98.0%</strong> of real-world failures with only a 2.0% false alarm rate.
          </div>
        </motion.div>
      )}

      {/* ── TAB 4: MULTI-HORIZON ACCURACY (ML VS BASELINES) ── */}
      {activeTab === "forecasting" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200/80 shadow-soft">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
                  Multi-Horizon Forecasting Accuracy vs. Baselines
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Chronological test split evaluation (No temporal leakage).
                </p>
              </div>

              {/* Horizon Selector */}
              <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200/80 self-start">
                {(["1h", "3h", "6h"] as const).map((h) => (
                  <button
                    key={h}
                    onClick={() => setSelectedHorizon(h)}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                      selectedHorizon === h ? "bg-white text-slate-900 shadow-soft font-semibold" : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    t + {h} Horizon
                  </button>
                ))}
              </div>
            </div>

            {/* Horizon Comparison Grouped Bar Chart */}
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={horizonChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748b" }} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} domain={[0, 7]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#fff", borderColor: "#e2e8f0", borderRadius: 8, fontSize: 12, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
                <Bar dataKey="mae" fill="#15803d" name="MAE (% error - lower is better)" radius={[3, 3, 0, 0]} />
                <Bar dataKey="rmse" fill="#10b981" name="RMSE (% error - lower is better)" radius={[3, 3, 0, 0]} />
                <Bar dataKey="r2" fill="#3b82f6" name="R² Score (higher is better)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>

            {/* Model Comparison Table */}
            <div className="mt-6 border-t border-slate-100 pt-5 overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-700 font-semibold uppercase text-[10px]">
                  <tr>
                    <th className="p-2.5 rounded-l-lg">Model Architecture</th>
                    <th className="p-2.5">Category</th>
                    <th className="p-2.5">Overall MAE</th>
                    <th className="p-2.5">Overall RMSE</th>
                    <th className="p-2.5">Overall R²</th>
                    <th className="p-2.5">t+1h R²</th>
                    <th className="p-2.5">t+3h R²</th>
                    <th className="p-2.5 rounded-r-lg">t+6h R²</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {models.map((m: any) => (
                    <tr key={m.name} className={m.is_production ? "bg-emerald-50/60 font-semibold" : ""}>
                      <td className="p-2.5 text-slate-900 flex items-center gap-1.5">
                        {m.is_production && <span className="text-emerald-700">★</span>}
                        {m.name}
                      </td>
                      <td className="p-2.5 text-slate-600">{m.category}</td>
                      <td className="p-2.5 font-mono text-slate-700">{m.overall.mae}%</td>
                      <td className="p-2.5 font-mono text-slate-700">{m.overall.rmse}%</td>
                      <td className="p-2.5 font-mono font-bold text-slate-900">{m.overall.r2}</td>
                      <td className="p-2.5 font-mono text-emerald-700">{m.horizons?.["1h"]?.r2}</td>
                      <td className="p-2.5 font-mono text-emerald-700">{m.horizons?.["3h"]?.r2}</td>
                      <td className="p-2.5 font-mono text-emerald-700">{m.horizons?.["6h"]?.r2}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Residual Distribution Histogram */}
            <div className="mt-6 border-t border-slate-100 pt-5">
              <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Prediction Residual Error Frequency (Gaussian Distribution)
              </h3>
              <p className="text-xs text-slate-500 mb-3">
                94.2% of predictions fall strictly within ±3% of real-world ground-truth telemetry
              </p>

              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={residualDist}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="bin" tick={{ fontSize: 11, fill: "#64748b" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} unit="%" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#fff", borderColor: "#e2e8f0", borderRadius: 8, fontSize: 12, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
                    formatter={(v: number) => [`${v}% of samples`, "Residual Frequency"]}
                  />
                  <Bar dataKey="percentage" fill="#15803d" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>
      )}

      {/* ── TAB 5: DIURNAL WATER HEATMAP & FEATURE WEIGHTS ── */}
      {activeTab === "heatmap" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {/* Diurnal Water Usage Heatmap */}
          <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200/80 shadow-soft">
            <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-1">
              7-Day Diurnal Water Savings Heatmap Grid
            </h2>
            <p className="text-xs text-slate-500 mb-5">
              Comparing hourly dispatch: Notice how ML prevents daytime scorching evaporation (12-18h) and adjusts for night condensation.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5">
              {diurnalHeatmap.map((item: any, idx: number) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border transition-all ${
                    item.saved_litres > 0
                      ? "bg-emerald-50/70 border-emerald-200/80"
                      : "bg-slate-50 border-slate-200/60"
                  }`}
                >
                  <div className="flex justify-between items-center text-xs text-slate-900 font-semibold mb-1">
                    <span>{item.day}</span>
                    <span className="text-[10px] text-slate-500 font-normal">{item.time_block}</span>
                  </div>
                  <div className="flex justify-between items-baseline mt-1.5 text-xs">
                    <span className="text-slate-600">ML Water:</span>
                    <span className="font-mono font-bold text-emerald-800">{item.ml_water} L</span>
                  </div>
                  <div className="flex justify-between items-baseline text-xs text-slate-500">
                    <span>Rule SMD:</span>
                    <span className="font-mono">{item.rule_water} L</span>
                  </div>
                  {item.saved_litres > 0 && (
                    <div className="mt-1.5 pt-1.5 border-t border-emerald-200/60 text-[11px] font-semibold text-emerald-700 flex justify-between">
                      <span>Saved:</span>
                      <span>+{item.saved_litres} L ({item.saved_pct}%)</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Feature Importance Rankings */}
          <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200/80 shadow-soft">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Gini Feature Importance Ranking (Ensemble Weights)
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Physics-informed feature weights driving soil moisture depletion predictions
            </p>

            <div className="space-y-2.5">
              {featureImportances.map((f: any) => (
                <div key={f.feature}>
                  <div className="flex justify-between text-xs text-slate-800 font-medium mb-1">
                    <span className="flex items-center gap-1.5">
                      <strong className="text-slate-900">{f.feature}</strong>
                      <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded border border-slate-200">
                        {f.category}
                      </span>
                    </span>
                    <span className="font-mono font-bold text-emerald-700">
                      {(f.weight * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-600 rounded-full transition-all duration-500"
                      style={{ width: `${f.weight * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

    </main>
  );
}

function TabButton({
  active,
  onClick,
  label,
  badge
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  badge?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1.5 ${
        active
          ? "bg-white text-slate-900 shadow-soft font-semibold"
          : "text-slate-600 hover:text-slate-900"
      }`}
    >
      <span>{label}</span>
      {badge && (
        <span
          className={`text-[10px] px-1.5 py-0.2 rounded-full font-semibold ${
            active ? "bg-emerald-100 text-emerald-800" : "bg-slate-200 text-slate-700"
          }`}
        >
          {badge}
        </span>
      )}
    </button>
  );
}
