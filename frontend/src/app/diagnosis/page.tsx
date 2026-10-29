"use client";

import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { ApiService } from "@/lib/api";
import {
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Bug,
  Stethoscope,
  Sparkles,
  ShieldAlert,
  HelpCircle,
  Eye,
  Droplets,
  Layers,
  ArrowRight,
  RotateCcw,
  Info,
  Sliders,
  Check,
  Scan,
  X
} from "lucide-react";

interface DiseaseCandidate {
  condition: string;
  scientific_name?: string;
  confidence_score: number;
  category: string;
}

interface VerificationStep {
  step_number: number;
  action: string;
  visual_clue: string;
}

interface DiseaseDiagnosis {
  status: string;
  plant_species_identified?: string;
  primary_condition: string;
  confidence: number;
  alternative_predictions: DiseaseCandidate[];
  is_conclusive: boolean;
  visible_symptoms: string[];
  possible_causes: string[];
  verification_steps: VerificationStep[];
  organic_remediation: string[];
  chemical_alternative?: string;
  hydrogel_irrigation_advisory: string;
  scientific_disclaimer: string;
  image_metadata?: Record<string, any>;
}

interface PestCandidate {
  pest_name: string;
  scientific_name?: string;
  confidence_score: number;
  detection_type: string;
  severity_level: string;
}

interface PestDiagnosis {
  status: string;
  primary_pest: string;
  confidence: number;
  detection_type: string;
  alternative_pests: PestCandidate[];
  is_conclusive: boolean;
  visible_evidence: string[];
  typical_damage_symptoms: string[];
  affected_plant_parts: string[];
  inspection_steps: string[];
  organic_management: string[];
  preventive_measures: string[];
  follow_up_monitoring: string;
  scientific_disclaimer: string;
  pest_count?: number;
  bounding_boxes?: any[];
  annotated_image_base64?: string;
  model_architecture?: string;
}

export default function PlantDiagnosisPage() {
  const [mode, setMode] = useState<"disease" | "pest">("disease");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  // Optional contextual inputs
  const [plantHint, setPlantHint] = useState("Potted Tomato");
  const [growthStage, setGrowthStage] = useState("Flowering / Fruiting");
  const [symptomHint, setSymptomHint] = useState("");
  const [durationDays, setDurationDays] = useState(3);
  const [wateringInfo, setWateringInfo] = useState("Standard Micro-Drip");

  // Results
  const [diseaseResult, setDiseaseResult] = useState<DiseaseDiagnosis | null>(null);
  const [pestResult, setPestResult] = useState<PestDiagnosis | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (file: File) => {
    setErrorMsg(null);
    if (!file.type.startsWith("image/")) {
      setErrorMsg("Please upload a valid image file (JPG, JPEG, or PNG).");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg("Image size exceeds the 10MB limit.");
      return;
    }
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setDiseaseResult(null);
    setPestResult(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // Disease Mutation
  const diseaseMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error("No image selected");
      const fd = new FormData();
      fd.append("file", selectedFile);
      if (plantHint) fd.append("plant_hint", plantHint);
      if (symptomHint) fd.append("symptom_hint", symptomHint);
      fd.append("duration_days", durationDays.toString());
      return (await ApiService.diagnoseDisease(fd)) as DiseaseDiagnosis;
    },
    onSuccess: (data) => {
      setDiseaseResult(data);
      setErrorMsg(null);
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.detail || "Failed to analyze image. Please try another photograph.");
    }
  });

  // Pest Mutation
  const pestMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error("No image selected");
      const fd = new FormData();
      fd.append("file", selectedFile);
      if (plantHint) fd.append("plant_hint", plantHint);
      if (symptomHint) fd.append("symptom_hint", symptomHint);
      return (await ApiService.diagnosePest(fd)) as PestDiagnosis;
    },
    onSuccess: (data) => {
      setPestResult(data);
      setErrorMsg(null);
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.detail || "Failed to screen for pests. Please try another photograph.");
    }
  });

  const handleRunAnalysis = () => {
    if (!selectedFile) {
      setErrorMsg("Please upload or select a plant photograph first.");
      return;
    }
    if (mode === "disease") {
      diseaseMutation.mutate();
    } else {
      pestMutation.mutate();
    }
  };

  const isLoading = diseaseMutation.isPending || pestMutation.isPending;

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      {/* ── HEADER ── */}
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-200">
                MODULES 1 & 2 · COMPUTER VISION
              </span>
              <span className="bg-teal-100 text-teal-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-teal-200">
                SMART TERRACE DIAGNOSTICS
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Plant Health & Pest Diagnosis
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Upload photographs of your container plants to screen for foliar diseases (Early/Late Blight, Powdery Mildew, 
              Bacterial Spot) and identify garden pests (Aphids, Whiteflies, Spider Mites, Mealybugs, Leaf Miners).
            </p>
          </div>

          {/* Mode Switcher */}
          <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200 self-start sm:self-center">
            <button
              onClick={() => { setMode("disease"); setPestResult(null); }}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                mode === "disease"
                  ? "bg-white text-emerald-800 shadow-xs border border-slate-200/80"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Stethoscope className="w-3.5 h-3.5 text-emerald-600" />
              Leaf Disease Screening
            </button>
            <button
              onClick={() => { setMode("pest"); setDiseaseResult(null); }}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                mode === "pest"
                  ? "bg-white text-emerald-800 shadow-xs border border-slate-200/80"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Bug className="w-3.5 h-3.5 text-amber-600" />
              Pest & Insect Detection
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* ── LEFT COLUMN: IMAGE UPLOAD & CONTEXTUAL INPUTS ── */}
        <div className="lg:col-span-5 space-y-4">
          {/* Drag & Drop Card */}
          <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900 flex items-center justify-between">
              <span>Plant Photograph Upload</span>
              <span className="text-[11px] font-normal text-slate-500">JPG, JPEG, PNG · Max 10MB</span>
            </h2>

            <div
              onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                dragActive
                  ? "border-emerald-500 bg-emerald-50/50"
                  : previewUrl
                  ? "border-emerald-300 bg-slate-50/50"
                  : "border-slate-300 hover:border-slate-400 bg-slate-50/60"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/jpg,image/png"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) handleFileChange(e.target.files[0]);
                }}
              />

              {previewUrl ? (
                <div className="space-y-3">
                  <div className="relative max-h-56 w-full mx-auto overflow-hidden rounded-lg border border-slate-200 bg-black/5 flex items-center justify-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={previewUrl}
                      alt="Uploaded foliage preview"
                      className="max-h-56 object-contain"
                    />
                  </div>
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-xs text-slate-600 font-medium truncate max-w-[200px]">
                      {selectedFile?.name}
                    </span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                        setPreviewUrl(null);
                        setDiseaseResult(null);
                        setPestResult(null);
                      }}
                      className="text-xs text-rose-600 hover:text-rose-700 font-semibold underline"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2 py-4">
                  <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center mx-auto border border-emerald-100">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <p className="text-xs font-semibold text-slate-800">
                    Click to browse or drag & drop leaf photograph
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Take an in-focus close-up of symptomatic leaf surface in natural light
                  </p>
                </div>
              )}
            </div>

            {errorMsg && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Optional Plant Context Inputs */}
            <div className="pt-2 border-t border-slate-100 space-y-3">
              <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-slate-500" />
                Plant Context (Optional - Enhances Model Prior)
              </span>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                    Plant Species
                  </label>
                  <select
                    value={plantHint}
                    onChange={(e) => setPlantHint(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-slate-800 text-xs"
                  >
                    <option value="Potted Tomato">Potted Tomato (Thakkali)</option>
                    <option value="Green Chilli">Green Chilli (Milagai)</option>
                    <option value="Brinjal">Brinjal / Eggplant</option>
                    <option value="Spearmint">Spearmint (Pudina)</option>
                    <option value="Sweet Basil">Sweet Basil</option>
                    <option value="African Marigold">African Marigold</option>
                    <option value="Dwarf Hibiscus">Dwarf Hibiscus</option>
                    <option value="Okra">Okra (Vendaikkai)</option>
                    <option value="Indian Spinach">Indian Spinach (Palak)</option>
                    <option value="General Flora">Other Container Flora</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                    Growth Stage
                  </label>
                  <select
                    value={growthStage}
                    onChange={(e) => setGrowthStage(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-slate-800 text-xs"
                  >
                    <option value="Seedling">Seedling (Young shoots)</option>
                    <option value="Vegetative">Vegetative Expansion</option>
                    <option value="Flowering / Fruiting">Flowering / Fruiting</option>
                    <option value="Mature">Mature Container Plant</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                  Observed Symptoms (Keyword Clues)
                </label>
                <input
                  type="text"
                  placeholder="e.g. brown circular rings, white powder, sticky ants, leaf curling"
                  value={symptomHint}
                  onChange={(e) => setSymptomHint(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-slate-800 text-xs placeholder:text-slate-400"
                />
              </div>
            </div>

            {/* Run Analysis Button */}
            <button
              onClick={handleRunAnalysis}
              disabled={isLoading || !selectedFile}
              className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                isLoading || !selectedFile
                  ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                  : "bg-emerald-700 hover:bg-emerald-800 text-white shadow-sm"
              }`}
            >
              <Sparkles className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
              {isLoading ? "Running Computer Vision Classification…" : `Analyze Image for ${mode === "disease" ? "Diseases" : "Pests"}`}
            </button>
          </div>
        </div>

        {/* ── RIGHT COLUMN: DIAGNOSTIC REPORT & ACTIONABLE REMEDIATION ── */}
        <div className="lg:col-span-7 space-y-4">
          {isLoading && (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center space-y-3">
              <Sparkles className="w-8 h-8 text-emerald-600 animate-spin mx-auto" />
              <p className="text-sm font-semibold text-slate-800">
                Extracting foliar chlorophyll, necrotic lesion, and texture indices…
              </p>
              <p className="text-xs text-slate-500">
                Matching against PlantVillage benchmark and IP102 pest taxonomy.
              </p>
            </div>
          )}

          {!isLoading && !diseaseResult && !pestResult && (
            <div className="bg-white rounded-xl border border-slate-200/90 p-8 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mx-auto">
                <Eye className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Awaiting Photograph Upload</h3>
              <p className="text-xs text-slate-600 max-w-md mx-auto leading-relaxed">
                Upload a clear close-up photograph of the affected plant leaf or pest cluster on the left. 
                The system will perform feature extraction and display transparent classification metrics, 
                verification steps, and organic terrace remedies.
              </p>
            </div>
          )}

          {/* ── MODULE 1: DISEASE RESULT VIEW ── */}
          {diseaseResult && (
            <div className="space-y-4">
              {/* Primary Condition Card */}
              <div className={`rounded-xl border p-5 shadow-xs ${
                diseaseResult.status === "healthy"
                  ? "bg-emerald-50/70 border-emerald-200"
                  : diseaseResult.status === "inconclusive"
                  ? "bg-amber-50/70 border-amber-200"
                  : "bg-white border-slate-200/90"
              }`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                      Primary Condition Identified
                    </span>
                    <h2 className="text-xl font-bold text-slate-900 mt-0.5">
                      {diseaseResult.primary_condition}
                    </h2>
                    <p className="text-xs text-slate-500">
                      Target Plant: {diseaseResult.plant_species_identified}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center">
                    <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                      diseaseResult.status === "healthy"
                        ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                        : diseaseResult.status === "inconclusive"
                        ? "bg-amber-100 text-amber-800 border-amber-300"
                        : "bg-rose-100 text-rose-800 border-rose-300"
                    }`}>
                      {diseaseResult.confidence}% Confidence · {diseaseResult.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Confidence Bar */}
                <div className="space-y-1 mb-4">
                  <div className="flex justify-between text-xs text-slate-600 font-medium">
                    <span>Classification Fidelity</span>
                    <span>{diseaseResult.confidence}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        diseaseResult.confidence >= 75 ? "bg-emerald-600" : "bg-amber-500"
                      }`}
                      style={{ width: `${Math.min(100, diseaseResult.confidence)}%` }}
                    />
                  </div>
                </div>

                {/* Alternative Predictions Distribution */}
                {diseaseResult.alternative_predictions.length > 0 && (
                  <div className="pt-3 border-t border-slate-100">
                    <span className="text-[11px] font-semibold text-slate-500 block mb-2">
                      Alternative Model Predictions (Top Distribution):
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                      {diseaseResult.alternative_predictions.map((alt, i) => (
                        <div key={i} className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                          <p className="font-bold text-slate-800">{alt.condition}</p>
                          <p className="text-[11px] text-slate-500">
                            {alt.confidence_score}% · {alt.category}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Inconclusive Warning if low confidence */}
              {!diseaseResult.is_conclusive && (
                <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl text-xs space-y-1.5">
                  <div className="flex items-center gap-2 font-bold text-amber-900">
                    <AlertTriangle className="w-4 h-4 text-amber-700" />
                    Classification Inconclusive (Confidence threshold not met)
                  </div>
                  <p className="text-amber-800 leading-relaxed">
                    The leaf features do not match trained disease classes with sufficient certainty. This frequently 
                    occurs when lighting is uneven, the camera is out of focus, or the symptom is in an early ambiguous state. 
                    Please review the physical verification steps below.
                  </p>
                </div>
              )}

              {/* Symptoms & Causes Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-2">
                  <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    Characteristic Foliar Symptoms
                  </h4>
                  <ul className="list-disc pl-4 space-y-1 text-xs text-slate-600">
                    {diseaseResult.visible_symptoms.map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>

                <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-2">
                  <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-blue-600" />
                    Probable Micro-Climate Causes
                  </h4>
                  <ul className="list-disc pl-4 space-y-1 text-xs text-slate-600">
                    {diseaseResult.possible_causes.map((c, idx) => (
                      <li key={idx}>{c}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* 3-Step Verification Guide */}
              <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-3">
                <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-purple-600" />
                  Recommended Physical Inspection Steps
                </h4>
                <div className="space-y-2 text-xs">
                  {diseaseResult.verification_steps.map((v) => (
                    <div key={v.step_number} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 flex items-start gap-2.5">
                      <span className="w-5 h-5 rounded-full bg-purple-100 text-purple-800 font-bold flex items-center justify-center shrink-0 text-[11px]">
                        {v.step_number}
                      </span>
                      <div>
                        <strong className="text-slate-900">{v.action}:</strong>{" "}
                        <span className="text-slate-600">{v.visual_clue}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Organic Remediation Protocol */}
              <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-4 space-y-2.5">
                <h4 className="text-xs font-bold text-emerald-950 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                  Organic & Safe Terrace Remediation Plan
                </h4>
                <ul className="list-disc pl-4 space-y-1 text-xs text-emerald-900">
                  {diseaseResult.organic_remediation.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
                {diseaseResult.chemical_alternative && (
                  <p className="text-[11px] text-slate-600 pt-1 border-t border-emerald-200/60">
                    <strong>Conventional Alternative:</strong> {diseaseResult.chemical_alternative}
                  </p>
                )}
              </div>

              {/* Hydrogel Irrigation Advisory */}
              <div className="bg-teal-50/80 border border-teal-200 rounded-xl p-3 text-xs text-teal-900 flex items-start gap-2.5">
                <Droplets className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Hydrogel & Moisture Advisory: </span>
                  <span>{diseaseResult.hydrogel_irrigation_advisory}</span>
                </div>
              </div>

              {/* Disclaimer */}
              <p className="text-[11px] text-slate-400 italic text-center">
                {diseaseResult.scientific_disclaimer}
              </p>
            </div>
          )}

          {/* ── MODULE 2: PEST RESULT VIEW ── */}
          {pestResult && (
            <div className="space-y-4">
              {/* Primary Pest Card */}
              <div className={`rounded-xl border p-5 shadow-xs ${
                pestResult.status === "no_pest_found"
                  ? "bg-emerald-50/70 border-emerald-200"
                  : pestResult.status === "inconclusive"
                  ? "bg-amber-50/70 border-amber-200"
                  : "bg-white border-slate-200/90"
              }`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                      Pest Identification Result
                    </span>
                    <h2 className="text-xl font-bold text-slate-900 mt-0.5">
                      {pestResult.primary_pest}
                    </h2>
                    <span className="inline-block mt-1 text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded">
                      Detection Type: {pestResult.detection_type}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center">
                    <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                      pestResult.status === "no_pest_found"
                        ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                        : "bg-amber-100 text-amber-800 border-amber-300"
                    }`}>
                      {pestResult.confidence > 0
                        ? `${pestResult.confidence}% Confidence`
                        : "Confidence Unavailable"}
                    </span>
                  </div>
                </div>

                {/* YOLOv8-Nano Object Detection Overlay */}
                {pestResult.annotated_image_base64 && (
                  <div className="mb-4 p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold flex items-center gap-1.5 text-emerald-400">
                        <Scan className="w-3.5 h-3.5 text-emerald-400" />
                        YOLOv8-Nano Spatial Pest Localization
                      </span>
                      <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-0.5 rounded text-[11px] font-bold">
                        {pestResult.pest_count || pestResult.bounding_boxes?.length || 0} Targets Localized
                      </span>
                    </div>
                    <div className="relative max-h-80 w-full overflow-hidden rounded-lg bg-black flex items-center justify-center border border-slate-800">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={pestResult.annotated_image_base64}
                        alt="YOLOv8 Pest Detection Overlay"
                        className="max-h-80 object-contain rounded"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[10px] text-slate-400 pt-1 gap-1">
                      <span>Bounding boxes pinpoint individual pest bodies & lesions</span>
                      <span className="text-emerald-300/90 font-mono">{pestResult.model_architecture || "YOLOv8-Nano (IP102 Benchmark - 102 Classes)"}</span>
                    </div>
                  </div>
                )}

                {/* Evidence & Symptoms */}
                <div className="space-y-3 pt-2 border-t border-slate-100 text-xs">
                  <div>
                    <span className="font-bold text-slate-900 block mb-1">Visual Evidence:</span>
                    <ul className="list-disc pl-4 space-y-0.5 text-slate-600">
                      {pestResult.visible_evidence.map((ev, i) => (
                        <li key={i}>{ev}</li>
                      ))}
                    </ul>
                  </div>

                  {pestResult.typical_damage_symptoms.length > 0 && (
                    <div>
                      <span className="font-bold text-slate-900 block mb-1">Associated Damage:</span>
                      <ul className="list-disc pl-4 space-y-0.5 text-slate-600">
                        {pestResult.typical_damage_symptoms.map((ds, i) => (
                          <li key={i}>{ds}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Physical Inspection Checklist */}
              <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-2">
                <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
                  Recommended Physical Inspection Steps
                </h4>
                <ul className="list-disc pl-4 space-y-1 text-xs text-slate-600">
                  {pestResult.inspection_steps.map((st, i) => (
                    <li key={i}>{st}</li>
                  ))}
                </ul>
              </div>

              {/* Organic Pest Management */}
              <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-4 space-y-2">
                <h4 className="text-xs font-bold text-emerald-950 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                  Non-Toxic Organic Terrace Pest Controls
                </h4>
                <ul className="list-disc pl-4 space-y-1 text-xs text-emerald-900">
                  {pestResult.organic_management.map((m, i) => (
                    <li key={i}>{m}</li>
                  ))}
                </ul>
                <div className="pt-2 border-t border-emerald-200/60 text-[11px] text-emerald-800">
                  <strong>Follow-up: </strong>{pestResult.follow_up_monitoring}
                </div>
              </div>

              <p className="text-[11px] text-slate-400 italic text-center">
                {pestResult.scientific_disclaimer}
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
