"""Centralized Experimental Configuration for IRRIGATEWISE.

Configured specifically for:
30-Day Terrace-Garden Study (Potted Plants / Grow Bags)
Location: Tambaram Terrace Research Station, Tamil Nadu
"""

from typing import Dict, Any

# ─────────────────────────────────────────────────────────────────────────────
# 1. STUDY DURATION & EXPERIMENTAL TIMELINE
# ─────────────────────────────────────────────────────────────────────────────
STUDY_DURATION_DAYS = 30
STUDY_START_DATE = "2026-08-15"
STUDY_END_DATE = "2026-09-13"
STUDY_START_TIMESTAMP = "2026-08-15T00:00:00+05:30"
STUDY_END_TIMESTAMP = "2026-09-13T23:59:59+05:30"
SAMPLING_INTERVAL_HOURS = 1.0  # Hourly telemetric intervals
STUDY_TYPE = "30-Day Controlled Terrace Garden Study"

# ─────────────────────────────────────────────────────────────────────────────
# 2. TERRACE GARDEN ENVIRONMENT & CONTAINER ASSUMPTIONS
# ─────────────────────────────────────────────────────────────────────────────
ENVIRONMENT: Dict[str, Any] = {
    "type": "Terrace Garden (Potted Plants / Grow Bags)",
    "location": "Tambaram Terrace Research Station, Tamil Nadu",
    "coordinates": {"latitude": 12.9249, "longitude": 80.1000},
    "pot_count": 10,                        # 10 grow bags in experimental cluster
    "container_type": "15-Litre HDPE Grow Bags",
    "container_volume_litres": 15.0,        # Volume per pot
    "plant_species": "Solanum lycopersicum (Potted Tomato / Vegetables)",
    "potting_medium": "Cocopeat + Vermicompost + Red Soil (50:30:20 v/v)",
    "hydrogel_dosage_per_pot_g": 5.0,       # ~0.25% w/w of container dry potting mix
    "hydrogel_dosage_sqm_equiv": 50.0,      # Equivalent g/m² field calibration
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. IRRIGATION MEASUREMENT UNITS & EMITTER FLOW DYNAMICS
# ─────────────────────────────────────────────────────────────────────────────
# Measurements are strictly tracked in Millilitres (mL) per pot and cluster total
IRRIGATION_UNIT = "mL"
PRIMARY_VOLUME_UNIT = "millilitres"

# 12V DC Terrace Drip Submersible / Diaphragm Pump with 10 Micro-Drip Emitters
# Rated pump output: 2.0 L/min (2,000 mL/min) across 10 emitters = 200 mL/min per pot
PUMP_FLOW_RATE_TOTAL_ML_PER_MIN = 2000.0
PUMP_FLOW_RATE_PER_POT_ML_PER_MIN = 200.0

# Traditional / Fixed-timer baseline for terrace grow bags
# 500 mL per 15L pot daily fixed watering (5,000 mL total cluster baseline)
TRADITIONAL_IRRIGATION_ML_PER_POT = 500.0
TRADITIONAL_IRRIGATION_TOTAL_ML = 5000.0

# ─────────────────────────────────────────────────────────────────────────────
# 4. POTTING MEDIUM HYDRATION COEFFICIENTS & MOISTURE THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────
# Medium-specific retention multiplier (alpha)
POTTING_MEDIUM_COEFFICIENTS: Dict[str, float] = {
    "cocopeat_mix": 0.75,       # High water retention, lower irrigation rate
    "vermicompost_soil": 0.85,  # Balanced organic potting medium
    "red_soil": 1.00,           # Standard mineral potting soil
    "sandy_mix": 0.65,          # High drainage container mix
    # Backwards-compatible aliases for legacy soil types:
    "loam": 0.85,
    "clay": 1.10,
    "sandy": 0.65,
    "silt": 1.00,
}

# Configurable moisture targets for terrace container growing (% VWC)
MOISTURE_THRESHOLDS = {
    "optimal_target": 60.0,             # Target hydration level (% VWC)
    "critical_wilting_hydrogel": 38.0,  # Stress threshold with hydrogel polymer
    "critical_wilting_control": 42.0,   # Stress threshold without hydrogel (dries faster in containers)
    "saturation_ceiling_abort": 80.0,   # Upper limit to prevent container waterlogging
    "deficit_trigger_margin": 12.0,     # SMD threshold to trigger proactive pulse
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. PUMP SAFETY GUARDRAILS (SCALED FOR TERRACE CONTAINERS)
# ─────────────────────────────────────────────────────────────────────────────
PUMP_SAFETY_LIMITS = {
    "max_pulse_duration_minutes": 5.0,  # Clamped to 5 mins max (1,000 mL/pot ceiling)
    "min_cooldown_minutes": 20.0,       # Minimum pause between pulses
    "emergency_moisture_ceiling": 80.0, # Immediate shutdown threshold
}

# ─────────────────────────────────────────────────────────────────────────────
# 6. DATA INTEGRITY & AUDIT METADATA
# ─────────────────────────────────────────────────────────────────────────────
DATA_INTEGRITY_METADATA = {
    "data_nature": "Development / Simulation Benchmarking Dataset (Physics-Informed)",
    "dataset_preservation_policy": "STRICT_IMMUTABLE",
    "notes": "Historical benchmark records remain preserved without synthetic alteration. Terrace garden parameters govern active real-time evaluation, irrigation calculations, and reporting."
}
