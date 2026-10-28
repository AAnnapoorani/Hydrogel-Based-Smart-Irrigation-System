"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import { ApiService } from "@/lib/api";
import { Droplets, Cpu, Play, Square, Check, Layers, Sliders, Zap, AlertCircle } from "lucide-react";

const SOIL_ALPHA: Record<string, number> = {
  cocopeat_mix: 0.75,
  vermicompost_soil: 0.85,
  red_soil: 1.0,
  sandy_mix: 0.65,
  loam: 0.85,
  clay: 1.1,
  sandy: 0.65,
  silt: 1.0,
};

// 3-Way water consumption comparison (mL per container daily)
const weeklyComparisonData = [
  { day: "Mon", mlPredictive: 220, ruleBased: 310, traditional: 500 },
  { day: "Tue", mlPredictive: 190, ruleBased: 290, traditional: 500 },
  { day: "Wed", mlPredictive: 250, ruleBased: 350, traditional: 550 },
  { day: "Thu", mlPredictive: 180, ruleBased: 270, traditional: 500 },
  { day: "Fri", mlPredictive: 230, ruleBased: 330, traditional: 520 },
  { day: "Sat", mlPredictive: 200, ruleBased: 300, traditional: 500 },
  { day: "Sun", mlPredictive: 215, ruleBased: 315, traditional: 500 },
];

export default function IrrigationPage() {
  const [smCurrent, setSmCurrent] = useState(38);
  const [smOptimal, setSmOptimal] = useState(60);
  const [texture, setTexture] = useState("cocopeat_mix");
  const [fieldArea, setFieldArea] = useState(10); // 10 container grow bags
  const [hydrogelActive, setHydrogelActive] = useState(true);
  const [decisionMode, setDecisionMode] = useState<"comparison" | "ml" | "rule">("comparison");
  const [pumpActionStatus, setPumpActionStatus] = useState<string | null>(null);
  const [togglingNode, setTogglingNode] = useState(false);
  const queryClient = useQueryClient();

  const alpha = SOIL_ALPHA[texture] ?? 0.85;

  // 1. Fetch live ML-driven predictive decision & comparison
  const { data: decision } = useQuery({
    queryKey: ["irrigation-decision", smCurrent, smOptimal, texture, fieldArea, hydrogelActive],
    queryFn: () => ApiService.evaluateIrrigation({
      current_moisture: smCurrent,
      target_moisture: smOptimal,
      temperature: 33.0,
      humidity: 62.0,
      wind_speed: 12.0,
      rainfall_forecast_6h: 0.0,
      soil_texture: texture,
      crop_type: "Potted Tomato",
      hydrogel_present: hydrogelActive ? 1 : 0,
      field_area: fieldArea,
      pot_count: fieldArea,
      container_volume_litres: 15.0,
      hours_since_irrigation: 18.0
    }),
  });

  // 2. Fetch live pump state
  const { data: pumpState, refetch: refetchPump } = useQuery({
    queryKey: ["pump-status"],
    queryFn: ApiService.getPumpStatus,
    refetchInterval: 6000,
  });

  // 3. Fetch live autonomous system status
  const { data: autoStatus, refetch: refetchAuto } = useQuery({
    queryKey: ["automation-status"],
    queryFn: ApiService.getAutomationStatus,
    refetchInterval: 5000,
  });

  // 4. Fetch live ESP32 node connectivity
  const { data: nodeStatus } = useQuery({
    queryKey: ["node-status"],
    queryFn: ApiService.getNodeStatus,
    refetchInterval: 3500,
  });

  const handleToggleNode = async () => {
    try {
      setTogglingNode(true);
      if (nodeStatus?.is_online) {
        await ApiService.disconnectNode();
      } else {
        await ApiService.simulatePacket();
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["node-status"] }),
        queryClient.invalidateQueries({ queryKey: ["latest-sensor"] }),
        queryClient.invalidateQueries({ queryKey: ["predictive-decision"] }),
      ]);
    } catch (e) {
      console.error("ESP32 toggle failed:", e);
    } finally {
      setTogglingNode(false);
    }
  };

  // Toggle automation mutation
  const toggleAutoMutation = useMutation({
    mutationFn: (newVal: boolean) => ApiService.toggleAutomation({
      autonomous_enabled: newVal,
      auto_actuation_enabled: newVal,
      simulation_mode: true
    }),
    onSuccess: () => {
      refetchAuto();
      refetchPump();
    }
  });

  // Trigger instant autonomous cycle mutation
  const triggerCycleMutation = useMutation({
    mutationFn: ApiService.triggerAutonomousCycle,
    onSuccess: (res: any) => {
      setPumpActionStatus(`Autonomous cycle: ${res.message}`);
      refetchAuto();
      refetchPump();
    },
    onError: (err: any) => {
      setPumpActionStatus(`Autonomous cycle error: ${err?.response?.data?.detail ?? err.message}`);
    }
  });

  // 4. Mutation for executing pump actuation (Safe Simulation)
  const pumpMutation = useMutation({
    mutationFn: () => ApiService.executePump({
      duration_minutes: decision?.estimated_pump_duration_minutes ?? 15.0,
      water_amount_litres: decision?.water_required_litres ?? 3000.0,
      decision_mode: "ml_predictive",
      trigger_reason: decision?.reason ?? "Manual simulated actuation",
      simulation_mode: true
    }),
    onSuccess: (res) => {
      setPumpActionStatus(res.message);
      refetchPump();
      refetchAuto();
    },
    onError: (err: any) => {
      setPumpActionStatus(`Actuation error: ${err?.response?.data?.detail ?? err.message}`);
    }
  });

  const ruleWater = decision?.comparison?.rule_based_water_litres ?? 0;
  const mlWater = decision?.comparison?.ml_predictive_water_litres ?? 0;
  const waterDiff = decision?.comparison?.water_difference_litres ?? 0;
  const savingAdvantage = decision?.comparison?.water_saving_advantage_pct ?? 0;
  const ruleWaterMl = decision?.comparison?.rule_based_water_ml ?? Math.round(ruleWater * 1000);
  const mlWaterMl = decision?.comparison?.ml_predictive_water_ml ?? Math.round(mlWater * 1000);
  const waterPerPotMl = decision?.water_per_pot_ml ?? (fieldArea > 0 ? Math.round(mlWaterMl / fieldArea) : 0);

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Predictive Irrigation & Water Optimization
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              30-Day Terrace-Garden Study · 10 Potted Grow Bags (15L) · Solanaceae · Automated Micro-Drip (mL).
            </p>
          </div>

          {/* Mode Switcher */}
          <div className="bg-slate-100 p-0.5 rounded-lg flex gap-1 self-start">
            <button
              onClick={() => setDecisionMode("comparison")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                decisionMode === "comparison" ? "bg-white text-slate-900 shadow-soft font-semibold" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Side-by-Side Comparison
            </button>
            <button
              onClick={() => setDecisionMode("ml")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                decisionMode === "ml" ? "bg-white text-slate-900 shadow-soft font-semibold" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              ML Predictive Mode
            </button>
            <button
              onClick={() => setDecisionMode("rule")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                decisionMode === "rule" ? "bg-white text-slate-900 shadow-soft font-semibold" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Rule-Based SMD
            </button>
          </div>
        </div>

        {/* ── AUTONOMOUS CLOSED-LOOP AI ENGINE BANNER ── */}
        <div className="bg-slate-900 border border-slate-800 text-white rounded-xl p-5 mb-6 shadow-soft">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${autoStatus?.autonomous_enabled ? "bg-emerald-400 animate-pulse" : "bg-slate-500"}`} />
                <span className="text-xs uppercase tracking-wider font-semibold text-emerald-300">
                  Autonomous ML Closed-Loop
                </span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase ${
                  autoStatus?.autonomous_enabled ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-slate-800 text-slate-400"
                }`}>
                  {autoStatus?.autonomous_mode ?? "ACTIVE"}
                </span>

                <div className="hidden sm:flex items-center gap-1.5 pl-2 text-xs text-slate-400 border-l border-slate-700">
                  <span className={`w-1.5 h-1.5 rounded-full ${nodeStatus?.is_online ? "bg-emerald-400" : "bg-amber-400"}`}></span>
                  <span>{nodeStatus?.is_online ? "ESP32 Live" : "ESP32 Standby"}</span>
                  <button
                    onClick={handleToggleNode}
                    disabled={togglingNode}
                    className="ml-1 text-[11px] font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    {togglingNode ? "…" : nodeStatus?.is_online ? "Disconnect" : "Simulate"}
                  </button>
                </div>
              </div>

              <p className="text-sm font-semibold text-white">
                SENSE → DETECT → PREDICT → DECIDE → ACT → VERIFY
              </p>
              <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                Telemetry arriving from ESP32 is screened for anomalies, fed to the Multi-Horizon Regressor, and triggers precision drip actuation pulses.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 bg-white/5 p-3 rounded-lg border border-white/10 self-start md:self-center shrink-0">
              <div className="text-left pr-3 border-r border-white/10 text-xs">
                <span className="text-slate-400 block text-[10px] uppercase font-medium">Auto Cycles</span>
                <span className="text-base font-bold text-white">{autoStatus?.total_cycles_automated ?? 0} Dispatched</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleAutoMutation.mutate(!autoStatus?.autonomous_enabled)}
                  disabled={toggleAutoMutation.isPending}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors shadow-soft ${
                    autoStatus?.autonomous_enabled
                      ? "bg-slate-700 hover:bg-slate-600 text-white"
                      : "bg-emerald-600 hover:bg-emerald-500 text-white"
                  }`}
                >
                  {autoStatus?.autonomous_enabled ? "Pause Automation" : "Enable Full Automation"}
                </button>

                <button
                  onClick={() => triggerCycleMutation.mutate()}
                  disabled={triggerCycleMutation.isPending}
                  className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-lg text-xs font-medium border border-white/15 transition-colors"
                  title="Run instant autonomous evaluation on latest telemetry"
                >
                  {triggerCycleMutation.isPending ? "Evaluating…" : "⚡ Run Cycle Now"}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          
          {/* ── LEFT: INPUTS & SLIDERS ── */}
          <div className="space-y-5">
            
            {/* Model Architecture Info Card */}
            <div className="rounded-xl p-5 bg-white border border-slate-200/80 shadow-soft">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Dual Decision Engine Principles
                </span>
                <span className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-mono font-medium">
                  α = {alpha.toFixed(2)} ({texture})
                </span>
              </div>
              <p className="font-mono text-xs text-slate-700 leading-relaxed mb-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200/60">
                <strong>Mode 1 (Baseline):</strong> IR = α × (SM_optimal − SM_current)<br/>
                <strong>Mode 2 (ML Predictive):</strong> Forecasts t+1h, t+3h, t+6h with hydrogel buffer & weather integration.
              </p>
              
              <div className="flex items-center gap-3 pt-2 border-t border-slate-100">
                <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-700">
                  <input
                    type="checkbox"
                    checked={hydrogelActive}
                    onChange={(e) => setHydrogelActive(e.target.checked)}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-slate-300"
                  />
                  <span>Hydrogel Polymer Matrix Applied (5 g / 15L pot)</span>
                </label>
              </div>
            </div>

            {/* Interactive Sliders */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-soft space-y-4">
              <SliderRow
                label="Current Soil Moisture"
                value={smCurrent}
                min={15} max={85}
                onChange={setSmCurrent}
                unit="%"
              />
              <SliderRow
                label="Target Optimal Moisture"
                value={smOptimal}
                min={35} max={75}
                onChange={setSmOptimal}
                unit="%"
              />

              {/* Texture Select */}
              <div>
                <label className="flex justify-between text-xs font-medium text-slate-700 mb-1.5">
                  <span>Potting Medium Coefficient</span>
                  <span className="font-bold text-slate-900">α = {alpha.toFixed(2)}</span>
                </label>
                <select
                  value={texture}
                  onChange={(e) => setTexture(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 transition-colors"
                >
                  <option value="cocopeat_mix">Cocopeat + Compost Mix (50:30:20) — α 0.75</option>
                  <option value="vermicompost_soil">Vermicompost + Garden Soil — α 0.85</option>
                  <option value="red_soil">Red Soil Potting Mix — α 1.00</option>
                  <option value="sandy_mix">Sandy Container Mix — α 0.65</option>
                  <option value="loam">Loam Reference Mix — α 0.85</option>
                </select>
              </div>

              <SliderRow
                label="Potted Grow Bags"
                value={fieldArea}
                min={1} max={30} step={1}
                onChange={setFieldArea}
                unit=" pots"
              />
            </div>

            {/* Actuator & Pump Control Panel */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-soft">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-slate-900">Pump Actuation Guardrail Control</h2>
                <span className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium">
                  {pumpState?.mode ?? "SIMULATION MODE"}
                </span>
              </div>

              <p className="text-xs text-slate-500 mb-3.5 leading-relaxed">
                Actuation operates under agricultural safety ceiling (Max: 25 min pulse, 30 min cooldown lockout).
              </p>

              <div className="flex flex-col gap-2.5">
                <button
                  onClick={() => pumpMutation.mutate()}
                  disabled={pumpMutation.isPending || !decision?.irrigation_required}
                  className="w-full py-2.5 bg-emerald-700 hover:bg-emerald-800 active:bg-emerald-900 text-white font-medium rounded-lg text-sm transition-colors disabled:opacity-50 shadow-soft"
                >
                  {pumpMutation.isPending ? "Executing Pulse…" : `Trigger Pump Pulse (${decision?.estimated_pump_duration_minutes ?? 15} min simulated)`}
                </button>

                {pumpActionStatus && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
                    <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>{pumpActionStatus}</span>
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* ── RIGHT: DECISION ENGINE COMPARISON & 3-WAY WATER BENCHMARK ── */}
          <div className="space-y-5">
            
            {/* Comparison Cards: Rule-Based vs ML Predictive */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-soft">
              <h2 className="text-sm font-semibold text-slate-900 mb-1">
                Baseline vs. ML Predictive Comparison
              </h2>
              <p className="text-xs text-slate-500 mb-4">
                Forecasted 3h: <strong>{decision?.predicted_moisture_3h}%</strong> · 6h: <strong>{decision?.predicted_moisture_6h}%</strong>
              </p>

              <div className="grid grid-cols-2 gap-3.5 mb-4">
                {/* Mode 1 Card */}
                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Mode 1: Rule-Based (SMD)</div>
                  <div className="text-xs text-slate-700 font-medium mb-1.5">
                    {decision?.comparison?.rule_based_decision ? "⚠ Triggered (SMD)" : "✓ Not Triggered"}
                  </div>
                  <div className="text-2xl font-bold text-slate-900 leading-tight">{ruleWaterMl.toLocaleString()} mL</div>
                  <div className="text-[11px] text-slate-500 mt-1">{fieldArea > 0 ? `${Math.round(ruleWaterMl / fieldArea)} mL / pot · ` : ""}{ruleWater} L total</div>
                </div>

                {/* Mode 2 Card */}
                <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/60">
                  <div className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider mb-1">Mode 2: ML Predictive</div>
                  <div className="text-xs text-emerald-800 font-medium mb-1.5">
                    {decision?.comparison?.ml_predictive_decision ? "💧 Micro-Drip Pulse" : "✓ Optimal Hydration"}
                  </div>
                  <div className="text-2xl font-bold text-emerald-900 leading-tight">{mlWaterMl.toLocaleString()} mL</div>
                  <div className="text-[11px] text-emerald-700 mt-1">{waterPerPotMl} mL / pot · {mlWater} L total</div>
                </div>
              </div>

              {/* Water Conservation Advantage Banner */}
              <div className="p-3.5 rounded-lg bg-teal-50 border border-teal-200/80 text-teal-950 text-xs flex items-center justify-between">
                <div>
                  <p className="font-semibold text-xs sm:text-sm text-teal-900">ML + Hydrogel Water Advantage</p>
                  <p className="text-[11px] text-teal-700 mt-0.5">
                    Saves {Math.max(0, ruleWaterMl - mlWaterMl).toLocaleString()} mL per cycle vs. rule-based over-watering
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xl font-bold text-teal-800">+{savingAdvantage}%</span>
                  <p className="text-[10px] text-teal-600 font-medium">Conserved</p>
                </div>
              </div>

              <div className="mt-3.5 text-xs text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-200/60 leading-relaxed">
                <strong>Decision Rationale:</strong> {decision?.reason}
              </div>
            </div>

            {/* 3-Way Water Consumption Bar Chart */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-soft">
              <h2 className="text-sm font-semibold text-slate-900 mb-1">
                Water Consumption Comparison (mL / Container Daily)
              </h2>
              <p className="text-xs text-slate-500 mb-4">
                Traditional Fixed Watering (500 mL) vs. Rule-Based SMD vs. ML Predictive + Hydrogel
              </p>

              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={weeklyComparisonData} barCategoryGap="25%">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="day" tick={{ fontSize: 11, fill: "#64748b" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} unit=" mL" domain={[0, 600]} />
                  <Tooltip
                    contentStyle={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 12, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
                    formatter={(v: number, name: string) => [
                      `${v} mL / pot`,
                      name === "mlPredictive" ? "ML Predictive + Hydrogel" : name === "ruleBased" ? "Rule-Based SMD" : "Traditional Baseline (500 mL)"
                    ]}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
                    formatter={(val) => val === "mlPredictive" ? "ML Predictive" : val === "ruleBased" ? "Rule-Based" : "Traditional"}
                  />
                  <Bar dataKey="mlPredictive" fill="#15803d" radius={[2, 2, 0, 0]} name="mlPredictive" />
                  <Bar dataKey="ruleBased"    fill="#10b981" radius={[2, 2, 0, 0]} name="ruleBased" />
                  <Bar dataKey="traditional"  fill="#cbd5e1" radius={[2, 2, 0, 0]} name="traditional" />
                </BarChart>
              </ResponsiveContainer>
              <p className="text-[11px] text-slate-500 mt-2 text-center">
                ML Predictive scheduling combined with Hydrogel retains root moisture with least water expenditure.
              </p>
            </div>

          </div>

        </div>

      </motion.div>
    </main>
  );
}

function SliderRow({
  label, value, min, max, step = 1, onChange, unit,
}: {
  label: string; value: number; min: number; max: number; step?: number;
  onChange: (v: number) => void; unit: string;
}) {
  return (
    <div>
      <label className="flex justify-between text-xs font-medium text-slate-700 mb-1.5">
        <span>{label}</span>
        <span className="font-bold text-slate-900">{value}{unit}</span>
      </label>
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-emerald-700 cursor-pointer"
      />
    </div>
  );
}
