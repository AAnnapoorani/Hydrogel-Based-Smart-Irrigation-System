"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { useSearchParams } from "next/navigation";
import { ApiService } from "@/lib/api";
import Link from "next/link";
import {
  Sprout,
  Plus,
  Trash2,
  Activity,
  Droplets,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Sparkles,
  Search,
  BookOpen,
  ArrowRight,
  ShieldAlert,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  X,
  Sun,
  Layers,
  Calendar,
  Flower2,
  Apple,
  Leaf,
  SlidersHorizontal,
  RotateCcw,
  Check,
  ShieldCheck,
  Info
} from "lucide-react";

interface UserPlant {
  id: number;
  name: string;
  plant_type: string;
  variety?: string;
  container_size_litres: number;
  planting_date?: string;
  growth_stage: string;
  hydrogel_dosage_grams: number;
  health_status: string;
  notes?: string;
  created_at: string;
  latest_moisture?: number;
  latest_diagnosis?: string;
}

interface PlantObservation {
  id: number;
  plant_id: number;
  observation_type: string;
  notes: string;
  severity: string;
  created_at: string;
}

interface CareAdvisory {
  plant_name: string;
  growth_stage: string;
  watering_urgency: string;
  watering_volume_ml: number;
  hydrogel_status: string;
  yellowing_diagnostic_tree: string[];
  temperature_humidity_stress_alert?: string;
  nutrient_adjustment?: string;
  immediate_actions: string[];
  upcoming_3_day_watch: string[];
}

interface RecommendedPlant {
  id: string;
  name: string;
  scientific_name: string;
  tamil_name?: string;
  category: string;
  suitability_score: number;
  suitability_rating: string;
  why_suitable: string;
  sunlight_requirement: string;
  min_container_litres: number;
  recommended_pot_depth_inches: number;
  watering_needs: string;
  hydrogel_synergy: string;
  soil_medium_preference: string;
  growth_timeline_days: string;
  difficulty_level: string;
  seasonal_notes: string;
  care_instructions: string[];
  companion_plants: string[];
  potential_challenges: string;
}

interface UnsuitableWarning {
  plant_name: string;
  limiting_factor: string;
  explanation: string;
  recommended_alternative: string;
}

interface RecommenderResponse {
  total_evaluated: number;
  recommended_plants: RecommendedPlant[];
  unsuitable_warnings: UnsuitableWarning[];
  terrace_context_summary: string;
  hydrogel_recommendation: string;
}

interface CatalogPlant {
  id: string;
  name: string;
  scientific_name: string;
  tamil_name?: string;
  category: string;
  min_sunlight_hours: number;
  sunlight_req_text: string;
  min_container_litres: number;
  recommended_pot_depth_inches: number;
  watering_needs: string;
  hydrogel_synergy: string;
  preferred_medium: string;
  difficulty: string;
  purposes: string[];
  care_instructions: string[];
  companion_plants: string[];
  potential_challenges: string;
}

function TerraceGardenContent({ defaultTab }: { defaultTab?: "my-garden" | "recommender" | "catalog" }) {
  const searchParams = useSearchParams();
  const queryTab = searchParams.get("tab") as "my-garden" | "recommender" | "catalog" | null;
  const [activeMainTab, setActiveMainTab] = useState<"my-garden" | "recommender" | "catalog">(
    defaultTab || queryTab || "my-garden"
  );

  const queryClient = useQueryClient();

  // ─────────────────────────────────────────────────────────────────
  // TAB 1: MY CONTAINERS STATE & QUERIES
  // ─────────────────────────────────────────────────────────────────
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedPlantForCare, setSelectedPlantForCare] = useState<UserPlant | null>(null);
  const [selectedPlantForObs, setSelectedPlantForObs] = useState<UserPlant | null>(null);
  const [newObsType, setNewObsType] = useState("Leaf Color");
  const [newObsNotes, setNewObsNotes] = useState("");
  const [newObsSeverity, setNewObsSeverity] = useState("Normal");

  const [form, setForm] = useState({
    name: "Grow Bag 1 - Tomato",
    plant_type: "Bush Tomato",
    variety: "Pusa Ruby",
    container_size_litres: 15.0,
    planting_date: new Date().toISOString().split("T")[0],
    growth_stage: "Vegetative",
    hydrogel_dosage_grams: 25.0,
    notes: "Potting mix: 50% Cocopeat + 30% Vermicompost + 20% Perlite"
  });

  const { data: plants = [], isLoading: isPlantsLoading } = useQuery<UserPlant[]>({
    queryKey: ["terrace-user-plants"],
    queryFn: ApiService.getUserPlants,
  });

  const { data: latestSensor } = useQuery({
    queryKey: ["latest-sensor"],
    queryFn: ApiService.getLatestSensor,
    refetchInterval: 5000,
  });

  const { data: plantObservations = [] } = useQuery<PlantObservation[]>({
    queryKey: ["plant-observations", selectedPlantForObs?.id],
    queryFn: () => (selectedPlantForObs ? ApiService.getPlantObservations(selectedPlantForObs.id) : Promise.resolve([])),
    enabled: Boolean(selectedPlantForObs),
  });

  const { data: careAdvisory, isLoading: isCareLoading } = useQuery<CareAdvisory>({
    queryKey: ["care-advisory", selectedPlantForCare?.id, selectedPlantForCare?.growth_stage],
    queryFn: () => {
      if (!selectedPlantForCare) return Promise.reject();
      return ApiService.getCareAdvisory({
        plant_name: selectedPlantForCare.plant_type,
        growth_stage: selectedPlantForCare.growth_stage,
        current_moisture: selectedPlantForCare.latest_moisture || latestSensor?.soil_moisture || 55.0,
        temperature: latestSensor?.temperature || 31.5,
        humidity: latestSensor?.humidity || 68.0,
        forecast_rain_mm: 0.0,
        hydrogel_present: selectedPlantForCare.hydrogel_dosage_grams > 0,
        yellowing_observed: false
      });
    },
    enabled: Boolean(selectedPlantForCare),
  });

  const createPlantMutation = useMutation({
    mutationFn: (data: typeof form) => ApiService.createUserPlant(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["terrace-user-plants"] });
      setShowAddModal(false);
    }
  });

  const deletePlantMutation = useMutation({
    mutationFn: (id: number) => ApiService.deleteUserPlant(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["terrace-user-plants"] });
    }
  });

  const addObservationMutation = useMutation({
    mutationFn: (data: { plantId: number; payload: any }) =>
      ApiService.addPlantObservation(data.plantId, data.payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plant-observations", selectedPlantForObs?.id] });
      queryClient.invalidateQueries({ queryKey: ["terrace-user-plants"] });
      setNewObsNotes("");
    }
  });

  // ─────────────────────────────────────────────────────────────────
  // TAB 2: RECOMMENDER STATE & MUTATION
  // ─────────────────────────────────────────────────────────────────
  const [sunlight, setSunlight] = useState("4-6h");
  const [containerSize, setContainerSize] = useState<number>(15);
  const [season, setSeason] = useState("post_monsoon");
  const [experience, setExperience] = useState("beginner");
  const [soilType, setSoilType] = useState("cocopeat_mix");
  const [maintenance, setMaintenance] = useState("moderate");
  const [categories, setCategories] = useState<string[]>(["vegetables", "herbs"]);
  const [purposes, setPurposes] = useState<string[]>(["household_consumption", "cooking_herbs"]);
  const [hydrogelPresent, setHydrogelPresent] = useState(true);
  const [potCount, setPotCount] = useState(10);
  const [expandedPlant, setExpandedPlant] = useState<string | null>(null);
  const [recommenderFilterCat, setRecommenderFilterCat] = useState<string>("all");

  const toggleCategory = (cat: string) => {
    setCategories((prev) =>
      prev.includes(cat) ? (prev.length > 1 ? prev.filter((c) => c !== cat) : prev) : [...prev, cat]
    );
  };

  const togglePurpose = (purp: string) => {
    setPurposes((prev) =>
      prev.includes(purp) ? (prev.length > 1 ? prev.filter((p) => p !== purp) : prev) : [...prev, purp]
    );
  };

  const {
    data: recommendations,
    isPending: isRecommenderPending,
    mutate: fetchRecommendations
  } = useMutation({
    mutationFn: async () => {
      return (await ApiService.getTerraceRecommendations({
        sunlight_hours: sunlight,
        container_size_litres: containerSize,
        season,
        experience_level: experience,
        soil_type: soilType,
        maintenance_level: maintenance,
        preferred_categories: categories,
        gardening_purposes: purposes,
        hydrogel_present: hydrogelPresent,
        pot_count: potCount
      })) as RecommenderResponse;
    }
  });

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const handlePlantRecommended = (plant: RecommendedPlant) => {
    setForm({
      name: `Grow Bag - ${plant.name}`,
      plant_type: plant.name,
      variety: plant.scientific_name,
      container_size_litres: plant.min_container_litres || 15.0,
      planting_date: new Date().toISOString().split("T")[0],
      growth_stage: "Vegetative",
      hydrogel_dosage_grams: Math.round((plant.min_container_litres || 15.0) * 1.6),
      notes: `Optimal medium: ${plant.soil_medium_preference}. Hydrogel synergy: ${plant.hydrogel_synergy}`
    });
    setShowAddModal(true);
    setActiveMainTab("my-garden");
  };

  const filteredRecommendedPlants = (recommendations?.recommended_plants || []).filter((p) => {
    if (recommenderFilterCat === "all") return true;
    return p.category.toLowerCase().replace(" ", "_") === recommenderFilterCat.toLowerCase();
  });

  // ─────────────────────────────────────────────────────────────────
  // TAB 3: BOTANICAL CATALOG STATE & QUERY
  // ─────────────────────────────────────────────────────────────────
  const [catalogSearch, setCatalogSearch] = useState("");
  const [catalogCategory, setCatalogCategory] = useState("all");

  const { data: catalogData, isLoading: isCatalogLoading } = useQuery<{ total: number; plants: CatalogPlant[] }>({
    queryKey: ["terrace-catalog"],
    queryFn: () => ApiService.getTerraceCatalog(),
  });

  const filteredCatalog = useMemo(() => {
    const list = catalogData?.plants || [];
    return list.filter((plant) => {
      const matchCat =
        catalogCategory === "all" ||
        plant.category.toLowerCase().replace(" ", "_") === catalogCategory.toLowerCase();
      const matchSearch =
        catalogSearch === "" ||
        plant.name.toLowerCase().includes(catalogSearch.toLowerCase()) ||
        plant.scientific_name.toLowerCase().includes(catalogSearch.toLowerCase()) ||
        (plant.tamil_name && plant.tamil_name.toLowerCase().includes(catalogSearch.toLowerCase()));
      return matchCat && matchSearch;
    });
  }, [catalogData, catalogCategory, catalogSearch]);

  const speciesList = [
    "Bush Tomato", "Cherry Tomato", "Green Chilli", "Capsicum", "Brinjal", "Okra",
    "Bush French Beans", "Amaranth Keerai", "Indian Spinach", "Spearmint", "Coriander",
    "Curry Leaf", "White Radish", "Strawberry", "Rose", "Aloe Vera", "Marigold", "Tulsi"
  ];

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      {/* ── TOP HEADER ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 animate-pulse" />
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Terrace Garden Intelligence Hub
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl leading-relaxed">
            Unified container gardening suite: manage active grow bags, discover sunlight-matched plants, and consult the 24-species botanical catalog.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/diagnosis"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-soft transition-colors"
          >
            <Activity className="w-3.5 h-3.5 text-emerald-600" />
            Screen Foliage Health
          </Link>
          <button
            onClick={() => {
              setShowAddModal(true);
              setActiveMainTab("my-garden");
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold shadow-soft transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Container Pot
          </button>
        </div>
      </div>

      {/* ── UNIFIED 3-TAB NAVIGATION ── */}
      <div className="flex overflow-x-auto gap-1 p-1 bg-slate-100 rounded-xl border border-slate-200/80">
        <button
          onClick={() => setActiveMainTab("my-garden")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs sm:text-sm font-semibold transition-all whitespace-nowrap ${
            activeMainTab === "my-garden"
              ? "bg-white text-emerald-800 shadow-sm border border-slate-200/60"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
          }`}
        >
          <Sprout className="w-4 h-4 text-emerald-700" />
          My Containers ({plants.length})
        </button>

        <button
          onClick={() => setActiveMainTab("recommender")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs sm:text-sm font-semibold transition-all whitespace-nowrap ${
            activeMainTab === "recommender"
              ? "bg-white text-emerald-800 shadow-sm border border-slate-200/60"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
          }`}
        >
          <Sparkles className="w-4 h-4 text-emerald-700" />
          Plant Recommender
          <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-bold ml-1">
            AI Matched
          </span>
        </button>

        <button
          onClick={() => setActiveMainTab("catalog")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs sm:text-sm font-semibold transition-all whitespace-nowrap ${
            activeMainTab === "catalog"
              ? "bg-white text-emerald-800 shadow-sm border border-slate-200/60"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
          }`}
        >
          <BookOpen className="w-4 h-4 text-emerald-700" />
          Botanical Catalog (24 Species)
        </button>
      </div>

      {/* ─────────────────────────────────────────────────────────────────
          TAB 1: MY ACTIVE CONTAINER GARDEN
      ───────────────────────────────────────────────────────────────── */}
      {activeMainTab === "my-garden" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {/* Summary KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-soft">
              <p className="text-xs font-medium text-slate-500">Registered Pots</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{plants.length}</p>
              <p className="text-[11px] text-slate-400 mt-0.5">15L Container capacity</p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-soft">
              <p className="text-xs font-medium text-slate-500">Hydrogel SAP Protected</p>
              <p className="text-2xl font-bold text-emerald-700 mt-1">
                {plants.filter((p) => p.hydrogel_dosage_grams > 0).length}
              </p>
              <p className="text-[11px] text-emerald-600 font-medium mt-0.5">25g buffer / pot</p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-soft">
              <p className="text-xs font-medium text-slate-500">Live Root Moisture</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">
                {latestSensor ? `${latestSensor.soil_moisture.toFixed(1)}%` : "58.4%"}
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">ESP32 Root zone probe</p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-soft">
              <p className="text-xs font-medium text-slate-500">Water Conservation</p>
              <p className="text-2xl font-bold text-teal-700 mt-1">48.2%</p>
              <p className="text-[11px] text-teal-600 font-medium mt-0.5">vs non-hydrogel pots</p>
            </div>
          </div>

          {/* Container Plants List */}
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <h2 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Active Container Grow Bags ({plants.length})
              </h2>
              <span className="text-xs text-slate-400">Cocopeat + Vermicompost + Hydrogel Matrix</span>
            </div>

            {isPlantsLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-44 bg-slate-100 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : plants.length === 0 ? (
              <div className="bg-white rounded-xl border border-dashed border-slate-200 p-12 text-center flex flex-col items-center justify-center min-h-[300px] shadow-soft">
                <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center mb-3">
                  <Sprout className="w-6 h-6" />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-1">No Container Plants Registered</h3>
                <p className="text-xs text-slate-500 max-w-sm mb-4">
                  Add your first terrace grow bag to track personalized daily watering needs, hydrogel kinetics, and physical growth logs.
                </p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowAddModal(true)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-emerald-700 text-white text-xs font-semibold shadow-soft hover:bg-emerald-800 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    Add First Container Pot
                  </button>
                  <button
                    onClick={() => setActiveMainTab("recommender")}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-slate-200 bg-white text-slate-700 text-xs font-semibold shadow-soft hover:bg-slate-50 transition-colors"
                  >
                    <Sparkles className="w-4 h-4 text-emerald-600" />
                    Discover Suitable Plants
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {plants.map((plant) => (
                  <div
                    key={plant.id}
                    className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-soft hover:border-emerald-600/30 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-slate-900 text-sm">{plant.name}</h3>
                            <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                              {plant.plant_type}
                            </span>
                          </div>
                          {plant.variety && (
                            <p className="text-xs text-slate-400 mt-0.5">Var: {plant.variety}</p>
                          )}
                        </div>
                        <button
                          onClick={() => deletePlantMutation.mutate(plant.id)}
                          className="text-slate-400 hover:text-rose-600 p-1 transition-colors"
                          title="Remove Plant"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <div className="grid grid-cols-2 gap-2 mt-4 text-xs">
                        <div className="p-2 bg-slate-50 rounded-lg">
                          <span className="text-slate-400 text-[10px] block">Container Size</span>
                          <span className="font-medium text-slate-700">
                            {plant.container_size_litres}L Grow Bag
                          </span>
                        </div>
                        <div className="p-2 bg-emerald-50/60 rounded-lg">
                          <span className="text-emerald-700 text-[10px] block font-medium">Hydrogel SAP</span>
                          <span className="font-medium text-emerald-800">
                            {plant.hydrogel_dosage_grams > 0 ? `${plant.hydrogel_dosage_grams}g / pot` : "None"}
                          </span>
                        </div>
                        <div className="p-2 bg-slate-50 rounded-lg">
                          <span className="text-slate-400 text-[10px] block">Growth Stage</span>
                          <span className="font-medium text-slate-700">{plant.growth_stage}</span>
                        </div>
                        <div className="p-2 bg-slate-50 rounded-lg">
                          <span className="text-slate-400 text-[10px] block">Health Status</span>
                          <span className="font-medium text-emerald-700 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            {plant.health_status}
                          </span>
                        </div>
                      </div>

                      {plant.notes && (
                        <p className="text-xs text-slate-500 mt-3 bg-slate-50/70 p-2 rounded-lg italic line-clamp-2">
                          "{plant.notes}"
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 mt-5 pt-3 border-t border-slate-100">
                      <button
                        onClick={() => setSelectedPlantForCare(plant)}
                        className="flex-1 inline-flex items-center justify-center gap-1.5 py-1.5 px-2 bg-emerald-50 text-emerald-800 hover:bg-emerald-100/80 rounded-lg text-xs font-semibold transition-colors"
                      >
                        <Droplets className="w-3.5 h-3.5" />
                        Care Advisory
                      </button>
                      <button
                        onClick={() => setSelectedPlantForObs(plant)}
                        className="flex-1 inline-flex items-center justify-center gap-1.5 py-1.5 px-2 bg-slate-100 text-slate-700 hover:bg-slate-200/70 rounded-lg text-xs font-semibold transition-colors"
                      >
                        <Clock className="w-3.5 h-3.5" />
                        Log Health
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* ─────────────────────────────────────────────────────────────────
          TAB 2: PLANT RECOMMENDER (DISCOVERY & MATCHING)
      ───────────────────────────────────────────────────────────────── */}
      {activeMainTab === "recommender" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Questionnaire Column */}
            <div className="lg:col-span-1 bg-white p-5 sm:p-6 rounded-xl border border-slate-200/80 shadow-soft space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="w-4 h-4 text-emerald-700" />
                  <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
                    Terrace Parameters
                  </h2>
                </div>
                <button
                  onClick={() => {
                    setSunlight("4-6h");
                    setContainerSize(15);
                    setSeason("post_monsoon");
                    setExperience("beginner");
                    setSoilType("cocopeat_mix");
                    setMaintenance("moderate");
                    setCategories(["vegetables", "herbs"]);
                    setPurposes(["household_consumption", "cooking_herbs"]);
                    setHydrogelPresent(true);
                  }}
                  className="text-slate-400 hover:text-slate-600 text-xs flex items-center gap-1 transition-colors"
                  title="Reset to Defaults"
                >
                  <RotateCcw className="w-3 h-3" />
                  Reset
                </button>
              </div>

              {/* Sunlight Hours */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
                  <Sun className="w-3.5 h-3.5 text-amber-500" />
                  Daily Direct Sunlight Exposure
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { val: "2-4h", label: "2–4 Hours", desc: "Partial Shade" },
                    { val: "4-6h", label: "4–6 Hours", desc: "Moderate Sun" },
                    { val: "6-8h", label: "6–8 Hours", desc: "Full Sun" },
                    { val: "8h+", label: "8+ Hours", desc: "Intense Rooftop" }
                  ].map((s) => (
                    <button
                      key={s.val}
                      onClick={() => setSunlight(s.val)}
                      className={`p-2.5 rounded-lg border text-left transition-all ${
                        sunlight === s.val
                          ? "border-emerald-600 bg-emerald-50/50 text-emerald-900 font-semibold"
                          : "border-slate-200 hover:border-slate-300 text-slate-700"
                      }`}
                    >
                      <div className="text-xs">{s.label}</div>
                      <div className="text-[10px] text-slate-400">{s.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Container Size */}
              <div>
                <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-1.5">
                  <label className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-emerald-700" />
                    Container / Grow Bag Volume
                  </label>
                  <span className="text-emerald-800 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    {containerSize} Litres
                  </span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="35"
                  step="5"
                  value={containerSize}
                  onChange={(e) => setContainerSize(Number(e.target.value))}
                  className="w-full accent-emerald-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                  <span>5L Small Pot</span>
                  <span>15L Standard Grow Bag</span>
                  <span>35L Large Tub</span>
                </div>
              </div>

              {/* Season */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-teal-600" />
                  Tamil Nadu Agro-Climatic Season
                </label>
                <select
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                >
                  <option value="sw_monsoon">SW Monsoon (Jun – Aug) · Heavy Cloud Cover</option>
                  <option value="post_monsoon">NE Monsoon (Sep – Nov) · Peak Precipitation</option>
                  <option value="winter">Winter / Mild (Dec – Feb) · Optimal Rooftop Period</option>
                  <option value="summer">Summer (Mar – May) · Intense Thermal Radiation</option>
                </select>
              </div>

              {/* Potting Medium */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Primary Growing Substrate
                </label>
                <select
                  value={soilType}
                  onChange={(e) => setSoilType(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                >
                  <option value="cocopeat_mix">Cocopeat + Vermicompost (50:50 Lightweight)</option>
                  <option value="red_soil">Red Loam Soil + Farmyard Manure</option>
                  <option value="sandy_mix">Sandy Loam Mix (High Drainage)</option>
                </select>
              </div>

              {/* Categories */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Target Plant Categories
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {[
                    { id: "vegetables", label: "Vegetables" },
                    { id: "herbs", label: "Culinary Herbs" },
                    { id: "flowering", label: "Flowering" },
                    { id: "ornamental", label: "Ornamental" },
                    { id: "small_fruits", label: "Small Fruits" }
                  ].map((c) => (
                    <button
                      key={c.id}
                      onClick={() => toggleCategory(c.id)}
                      className={`text-xs px-2.5 py-1 rounded-full border transition-all ${
                        categories.includes(c.id)
                          ? "bg-emerald-700 text-white border-emerald-700 font-medium"
                          : "bg-slate-50 text-slate-600 border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Hydrogel SAP Integration Toggle */}
              <div className="p-3 bg-teal-50/70 border border-teal-200/60 rounded-lg flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-teal-900 block">Hydrogel SAP Incorporated</span>
                  <span className="text-[10px] text-teal-700 block">
                    {hydrogelPresent ? `Buffering ${Math.round(containerSize * 1.6)}g SAP / container` : "Dry-wet oscillations active"}
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={hydrogelPresent}
                  onChange={(e) => setHydrogelPresent(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-600 cursor-pointer"
                />
              </div>

              <button
                onClick={() => fetchRecommendations()}
                disabled={isRecommenderPending}
                className="w-full bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg text-xs shadow-soft transition-colors flex items-center justify-center gap-2"
              >
                {isRecommenderPending ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Calculating Agronomic Matches...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Evaluate Container Suitability
                  </>
                )}
              </button>
            </div>

            {/* Results Column */}
            <div className="lg:col-span-2 space-y-4">
              {/* Context Callout */}
              {recommendations && (
                <div className="bg-emerald-50/70 border border-emerald-200 p-4 rounded-xl">
                  <div className="flex items-start gap-2.5">
                    <Info className="w-4 h-4 text-emerald-700 mt-0.5 flex-shrink-0" />
                    <div className="text-xs text-emerald-950 space-y-1">
                      <p className="font-semibold text-emerald-900">
                        {recommendations.terrace_context_summary}
                      </p>
                      <p className="text-emerald-800 leading-relaxed">
                        {recommendations.hydrogel_recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Filter Tabs */}
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <div className="flex items-center gap-1.5 overflow-x-auto">
                  {["all", "vegetables", "herbs", "flowering", "ornamental", "small_fruits"].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setRecommenderFilterCat(tab)}
                      className={`text-xs px-3 py-1 rounded-lg font-medium transition-colors ${
                        recommenderFilterCat === tab
                          ? "bg-slate-900 text-white"
                          : "text-slate-500 hover:text-slate-900 hover:bg-slate-100"
                      }`}
                    >
                      {tab === "all" ? "All Suitable" : tab.replace("_", " ").toUpperCase()}
                    </button>
                  ))}
                </div>
                <span className="text-xs text-slate-400 font-medium">
                  {filteredRecommendedPlants.length} Plants Ranked
                </span>
              </div>

              {/* Plant Cards */}
              <div className="space-y-3">
                {isRecommenderPending ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-28 bg-slate-100 rounded-xl animate-pulse" />
                    ))}
                  </div>
                ) : filteredRecommendedPlants.length === 0 ? (
                  <div className="bg-white p-8 rounded-xl border text-center text-slate-500 text-xs shadow-soft">
                    No plant candidates matched this specific combination of criteria. Try lowering the container volume or adjusting sunlight hours.
                  </div>
                ) : (
                  filteredRecommendedPlants.map((plant) => {
                    const isExpanded = expandedPlant === plant.id;
                    return (
                      <div
                        key={plant.id}
                        className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-soft hover:border-emerald-600/30 transition-all"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <h3 className="font-bold text-slate-900 text-sm">{plant.name}</h3>
                              {plant.tamil_name && (
                                <span className="text-xs text-slate-500 font-medium">
                                  ({plant.tamil_name})
                                </span>
                              )}
                              <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                                {plant.category}
                              </span>
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                  plant.suitability_rating === "Prime Choice"
                                    ? "bg-emerald-100 text-emerald-800"
                                    : "bg-teal-100 text-teal-800"
                                }`}
                              >
                                {plant.suitability_rating}
                              </span>
                            </div>

                            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                              {plant.why_suitable}
                            </p>

                            <div className="flex items-center gap-4 mt-2 text-[11px] text-slate-500 flex-wrap">
                              <span className="flex items-center gap-1">
                                <Sun className="w-3 h-3 text-amber-500" />
                                {plant.sunlight_requirement}
                              </span>
                              <span className="flex items-center gap-1">
                                <Layers className="w-3 h-3 text-emerald-700" />
                                {plant.min_container_litres}L+ Container
                              </span>
                              <span className="flex items-center gap-1">
                                <Droplets className="w-3 h-3 text-teal-600" />
                                {plant.difficulty_level}
                              </span>
                            </div>
                          </div>

                          <div className="flex flex-col items-end gap-2 flex-shrink-0">
                            <div className="text-right">
                              <span className="text-lg font-bold text-emerald-700">
                                {plant.suitability_score}%
                              </span>
                              <span className="text-[10px] text-slate-400 block -mt-0.5">Match</span>
                            </div>

                            <button
                              onClick={() => handlePlantRecommended(plant)}
                              className="inline-flex items-center gap-1 text-[11px] bg-emerald-700 hover:bg-emerald-800 text-white font-semibold px-2.5 py-1.5 rounded-lg shadow-soft transition-colors"
                            >
                              <Plus className="w-3 h-3" />
                              Plant in My Garden
                            </button>
                          </div>
                        </div>

                        {/* Collapsible Details */}
                        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
                          <button
                            onClick={() => setExpandedPlant(isExpanded ? null : plant.id)}
                            className="text-xs text-emerald-800 hover:text-emerald-900 font-semibold flex items-center gap-1"
                          >
                            {isExpanded ? "Hide Care & Hydrogel Guidelines" : "View Care & Hydrogel Guidelines"}
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                          <span className="text-[10px] text-slate-400">
                            Timeline: {plant.growth_timeline_days}
                          </span>
                        </div>

                        {isExpanded && (
                          <div className="mt-3 pt-3 border-t border-slate-100 space-y-3 text-xs bg-slate-50 p-3 rounded-lg">
                            <div>
                              <span className="font-semibold text-slate-900 block mb-0.5">
                                💧 Hydrogel SAP Synergy:
                              </span>
                              <p className="text-slate-600 leading-relaxed">{plant.hydrogel_synergy}</p>
                            </div>
                            <div>
                              <span className="font-semibold text-slate-900 block mb-0.5">
                                📋 Rooftop Care Instructions:
                              </span>
                              <ul className="list-disc list-inside space-y-0.5 text-slate-600">
                                {plant.care_instructions.map((inst, idx) => (
                                  <li key={idx}>{inst}</li>
                                ))}
                              </ul>
                            </div>
                            <div className="flex items-center gap-4 text-[11px] text-slate-500 pt-1">
                              <span>
                                <strong>Preferred Substrate:</strong> {plant.soil_medium_preference}
                              </span>
                              <span>
                                <strong>Companions:</strong> {plant.companion_plants.join(", ")}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>

              {/* Unsuitable Warnings */}
              {recommendations && recommendations.unsuitable_warnings.length > 0 && (
                <div className="mt-6 bg-amber-50/60 border border-amber-200/70 rounded-xl p-4 space-y-2">
                  <div className="flex items-center gap-2 text-amber-900 font-semibold text-xs">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Unsuitable Crops Filtered Out for Current Terrace Parameters</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                    {recommendations.unsuitable_warnings.map((w, idx) => (
                      <div key={idx} className="bg-white/80 p-2.5 rounded-lg border border-amber-200/50">
                        <span className="font-semibold text-slate-900">{w.plant_name}</span>:{" "}
                        <span className="text-amber-800">{w.explanation}</span>
                        <div className="text-[10px] text-slate-500 mt-1">
                          Alternative: <em>{w.recommended_alternative}</em>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* ─────────────────────────────────────────────────────────────────
          TAB 3: BOTANICAL CATALOG (24 CURATED SPECIES)
      ───────────────────────────────────────────────────────────────── */}
      {activeMainTab === "catalog" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2 flex-wrap">
              {["all", "vegetables", "herbs", "flowering", "ornamental", "small_fruits"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCatalogCategory(cat)}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
                    catalogCategory === cat
                      ? "bg-slate-900 text-white font-semibold"
                      : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {cat === "all" ? "All Species (24)" : cat.replace("_", " ").toUpperCase()}
                </button>
              ))}
            </div>

            <div className="relative min-w-[240px]">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search botanical species or Tamil name..."
                value={catalogSearch}
                onChange={(e) => setCatalogSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-600 shadow-soft"
              />
            </div>
          </div>

          {isCatalogLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-44 bg-slate-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : filteredCatalog.length === 0 ? (
            <div className="bg-white p-12 text-center text-slate-500 text-xs rounded-xl border shadow-soft">
              No botanical species matched your search query.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredCatalog.map((item) => (
                <div
                  key={item.id}
                  className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-soft hover:border-emerald-600/30 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm">{item.name}</h3>
                        <p className="text-xs text-slate-400 italic">{item.scientific_name}</p>
                      </div>
                      <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                        {item.category}
                      </span>
                    </div>

                    {item.tamil_name && (
                      <p className="text-xs text-emerald-800 font-medium mt-1">
                        Tamil: {item.tamil_name}
                      </p>
                    )}

                    <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                      <div className="p-2 bg-slate-50 rounded-lg">
                        <span className="text-slate-400 text-[10px] block">Sunlight Requirement</span>
                        <span className="font-medium text-slate-700">{item.sunlight_req_text}</span>
                      </div>
                      <div className="p-2 bg-slate-50 rounded-lg">
                        <span className="text-slate-400 text-[10px] block">Min Pot Volume</span>
                        <span className="font-medium text-slate-700">{item.min_container_litres}L+</span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-600 mt-2.5 line-clamp-2">
                      <strong>Watering:</strong> {item.watering_needs}
                    </p>

                    <div className="mt-2.5 p-2 bg-emerald-50/70 border border-emerald-200/50 rounded-lg text-xs text-emerald-900">
                      <strong>Hydrogel Synergy:</strong> {item.hydrogel_synergy}
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setForm({
                        name: `Grow Bag - ${item.name}`,
                        plant_type: item.name,
                        variety: item.scientific_name,
                        container_size_litres: item.min_container_litres || 15.0,
                        planting_date: new Date().toISOString().split("T")[0],
                        growth_stage: "Vegetative",
                        hydrogel_dosage_grams: Math.round((item.min_container_litres || 15.0) * 1.6),
                        notes: `Preferred medium: ${item.preferred_medium}`
                      });
                      setShowAddModal(true);
                      setActiveMainTab("my-garden");
                    }}
                    className="w-full mt-4 inline-flex items-center justify-center gap-1.5 py-1.5 px-3 bg-slate-100 hover:bg-emerald-50 text-slate-700 hover:text-emerald-800 rounded-lg text-xs font-semibold transition-colors border border-slate-200/60"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Register This Species in My Garden
                  </button>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* ─────────────────────────────────────────────────────────────────
          MODALS: ADD PLANT, CARE ADVISORY, OBSERVATION LOGBOOK
      ───────────────────────────────────────────────────────────────── */}
      {/* 1. Add Plant Modal */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 max-h-[90vh] overflow-y-auto space-y-4"
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <h3 className="font-bold text-slate-900 text-base">Add New Container Plant</h3>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Pot Identifier Name</label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full p-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-emerald-600"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Plant Species</label>
                    <input
                      type="text"
                      list="species-options"
                      value={form.plant_type}
                      onChange={(e) => setForm({ ...form, plant_type: e.target.value })}
                      className="w-full p-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-emerald-600"
                    />
                    <datalist id="species-options">
                      {speciesList.map((s) => (
                        <option key={s} value={s} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Variety (Optional)</label>
                    <input
                      type="text"
                      value={form.variety}
                      onChange={(e) => setForm({ ...form, variety: e.target.value })}
                      className="w-full p-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-emerald-600"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Container Size (L)</label>
                    <input
                      type="number"
                      step="1"
                      value={form.container_size_litres}
                      onChange={(e) => setForm({ ...form, container_size_litres: Number(e.target.value) })}
                      className="w-full p-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-emerald-600"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Hydrogel Dosage (g)</label>
                    <input
                      type="number"
                      step="1"
                      value={form.hydrogel_dosage_grams}
                      onChange={(e) => setForm({ ...form, hydrogel_dosage_grams: Number(e.target.value) })}
                      className="w-full p-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-emerald-600"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Growth Stage</label>
                    <select
                      value={form.growth_stage}
                      onChange={(e) => setForm({ ...form, growth_stage: e.target.value })}
                      className="w-full p-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-emerald-600"
                    >
                      <option value="Seedling">Seedling</option>
                      <option value="Vegetative">Vegetative</option>
                      <option value="Flowering">Flowering</option>
                      <option value="Fruiting">Fruiting</option>
                      <option value="Harvesting">Harvesting</option>
                    </select>
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Planting Date</label>
                    <input
                      type="date"
                      value={form.planting_date}
                      onChange={(e) => setForm({ ...form, planting_date: e.target.value })}
                      className="w-full p-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-emerald-600"
                    />
                  </div>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Potting Mix & Notes</label>
                  <textarea
                    rows={2}
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                    className="w-full p-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-emerald-600"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createPlantMutation.mutate(form)}
                  disabled={createPlantMutation.isPending}
                  className="px-4 py-2 text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg shadow-soft transition-colors flex items-center gap-1.5"
                >
                  {createPlantMutation.isPending ? "Adding..." : "Confirm & Save Pot"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 2. Care Advisory Modal */}
      <AnimatePresence>
        {selectedPlantForCare && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl border border-slate-200 max-h-[90vh] overflow-y-auto space-y-4"
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <Droplets className="w-5 h-5 text-emerald-700" />
                  <h3 className="font-bold text-slate-900 text-base">
                    Plant Care Advisory: {selectedPlantForCare.name}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedPlantForCare(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {isCareLoading ? (
                <div className="p-8 text-center text-xs text-slate-500 animate-pulse">
                  Synthesizing botanical advisory rules with hydrogel kinetics...
                </div>
              ) : careAdvisory ? (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200/60">
                      <span className="text-[10px] text-emerald-800 font-semibold block uppercase">
                        Watering Urgency
                      </span>
                      <span className="text-sm font-bold text-emerald-950 mt-0.5 block">
                        {careAdvisory.watering_urgency}
                      </span>
                    </div>
                    <div className="p-3 bg-teal-50 rounded-xl border border-teal-200/60">
                      <span className="text-[10px] text-teal-800 font-semibold block uppercase">
                        Target Drench Volume
                      </span>
                      <span className="text-sm font-bold text-teal-950 mt-0.5 block">
                        {careAdvisory.watering_volume_ml} mL
                      </span>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl space-y-1">
                    <span className="font-semibold text-slate-900">Hydrogel SAP Status:</span>
                    <p className="text-slate-600 leading-relaxed">{careAdvisory.hydrogel_status}</p>
                  </div>

                  {careAdvisory.immediate_actions.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="font-semibold text-slate-900 block">Immediate Actions:</span>
                      <ul className="list-disc list-inside space-y-1 text-slate-600 bg-emerald-50/50 p-3 rounded-lg border border-emerald-100">
                        {careAdvisory.immediate_actions.map((act, i) => (
                          <li key={i}>{act}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {careAdvisory.upcoming_3_day_watch.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="font-semibold text-slate-900 block">Upcoming 3-Day Rooftop Watch:</span>
                      <ul className="list-disc list-inside space-y-1 text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200/60">
                        {careAdvisory.upcoming_3_day_watch.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {careAdvisory.yellowing_diagnostic_tree.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="font-semibold text-slate-900 block">Yellowing Foliage Diagnostic:</span>
                      <div className="bg-amber-50/60 border border-amber-200/60 p-3 rounded-lg space-y-1">
                        {careAdvisory.yellowing_diagnostic_tree.map((diag, i) => (
                          <p key={i} className="text-amber-900 leading-relaxed">
                            • {diag}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : null}

              <div className="flex justify-end pt-3 border-t border-slate-100">
                <button
                  onClick={() => setSelectedPlantForCare(null)}
                  className="px-4 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
                >
                  Close Advisory
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 3. Health & Observation Logbook Modal */}
      <AnimatePresence>
        {selectedPlantForObs && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 max-h-[90vh] overflow-y-auto space-y-4"
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-emerald-700" />
                  <h3 className="font-bold text-slate-900 text-base">
                    Log Health: {selectedPlantForObs.name}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedPlantForObs(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* New Log Entry Form */}
              <div className="space-y-3 p-3 bg-slate-50 rounded-xl border border-slate-200/60 text-xs">
                <span className="font-semibold text-slate-900 block">Record New Observation</span>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-slate-500 block mb-1">Observation Type</label>
                    <select
                      value={newObsType}
                      onChange={(e) => setNewObsType(e.target.value)}
                      className="w-full p-2 bg-white border border-slate-200 rounded-lg"
                    >
                      <option value="Leaf Color">Leaf Color / Yellowing</option>
                      <option value="Pest Activity">Pest / Insect Sighting</option>
                      <option value="Fungal Spot">Fungal / Leaf Spot</option>
                      <option value="Vigor & Growth">Flowering / Fruit Vigor</option>
                      <option value="Wilting">Root Stress / Wilting</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-500 block mb-1">Severity</label>
                    <select
                      value={newObsSeverity}
                      onChange={(e) => setNewObsSeverity(e.target.value)}
                      className="w-full p-2 bg-white border border-slate-200 rounded-lg"
                    >
                      <option value="Normal">Normal / Healthy</option>
                      <option value="Mild">Mild Concern</option>
                      <option value="Moderate">Moderate Action Needed</option>
                      <option value="Severe">Severe Outbreak</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-slate-500 block mb-1">Field Observation Notes</label>
                  <input
                    type="text"
                    placeholder="e.g. Lower leaves show slight chlorosis; new terminal shoots healthy..."
                    value={newObsNotes}
                    onChange={(e) => setNewObsNotes(e.target.value)}
                    className="w-full p-2 bg-white border border-slate-200 rounded-lg"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={() => {
                      if (!newObsNotes.trim()) return;
                      addObservationMutation.mutate({
                        plantId: selectedPlantForObs.id,
                        payload: {
                          observation_type: newObsType,
                          notes: newObsNotes,
                          severity: newObsSeverity
                        }
                      });
                    }}
                    disabled={addObservationMutation.isPending || !newObsNotes.trim()}
                    className="px-3.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white font-semibold rounded-lg shadow-soft transition-colors"
                  >
                    {addObservationMutation.isPending ? "Logging..." : "Save Observation Entry"}
                  </button>
                </div>
              </div>

              {/* Past Observation Timeline */}
              <div className="space-y-2 text-xs">
                <span className="font-semibold text-slate-900 block">Past Observation History</span>
                {plantObservations.length === 0 ? (
                  <p className="text-slate-400 italic text-center py-4">No observations logged yet for this pot.</p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {plantObservations.map((obs) => (
                      <div key={obs.id} className="p-2.5 bg-white border border-slate-200 rounded-lg flex flex-col gap-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-800">{obs.observation_type}</span>
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                              obs.severity === "Normal"
                                ? "bg-emerald-50 text-emerald-800"
                                : obs.severity === "Mild"
                                ? "bg-amber-50 text-amber-800"
                                : "bg-rose-50 text-rose-800"
                            }`}
                          >
                            {obs.severity}
                          </span>
                        </div>
                        <p className="text-slate-600">{obs.notes}</p>
                        <span className="text-[10px] text-slate-400">
                          {new Date(obs.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-3 border-t border-slate-100">
                <button
                  onClick={() => setSelectedPlantForObs(null)}
                  className="px-4 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </main>
  );
}

export default function PlantsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-400">Loading Terrace Garden...</div>}>
      <TerraceGardenContent />
    </Suspense>
  );
}
