"""
IRRIGATEWISE — Personalized Terrace Garden Plant Care Assistant
Synthesizes container species biology, real-time sensor telemetry,
growth stage, weather conditions, and hydrogel retention dynamics.
"""

from typing import List, Dict, Optional, Any
from schemas import PlantCareAdvisoryOutput

PLANT_PROFILES = {
    "Tomato": {
        "min_moisture": 55.0,
        "max_moisture": 68.0,
        "container_ml_full": 500.0,
        "heat_stress_c": 35.0,
        "humidity_stress_pct": 85.0,
        "nutrient_notes": "High potassium and calcium demand during fruit development to prevent blossom-end rot."
    },
    "Chili": {
        "min_moisture": 48.0,
        "max_moisture": 62.0,
        "container_ml_full": 400.0,
        "heat_stress_c": 37.0,
        "humidity_stress_pct": 80.0,
        "nutrient_notes": "Moderate feeding. Overfeeding nitrogen causes flower drop and lush vegetative foliage."
    },
    "Mint (Pudina)": {
        "min_moisture": 60.0,
        "max_moisture": 75.0,
        "container_ml_full": 450.0,
        "heat_stress_c": 36.0,
        "humidity_stress_pct": 90.0,
        "nutrient_notes": "Heavy consumer of organic nitrogen. Excellent synergy with hydrogel moisture buffers."
    },
    "Spinach (Palak)": {
        "min_moisture": 55.0,
        "max_moisture": 70.0,
        "container_ml_full": 350.0,
        "heat_stress_c": 32.0,
        "humidity_stress_pct": 85.0,
        "nutrient_notes": "Needs continuous nitrogen top-dressing (vermicompost tea) for tender leaf production."
    },
    "Tulsi (Holy Basil)": {
        "min_moisture": 42.0,
        "max_moisture": 58.0,
        "container_ml_full": 300.0,
        "heat_stress_c": 40.0,
        "humidity_stress_pct": 80.0,
        "nutrient_notes": "Avoid rich potting fertilizers; lean nutrition preserves strong essential oil concentrations."
    },
    "Brinjal (Eggplant)": {
        "min_moisture": 52.0,
        "max_moisture": 65.0,
        "container_ml_full": 500.0,
        "heat_stress_c": 38.0,
        "humidity_stress_pct": 85.0,
        "nutrient_notes": "Requires steady phosphorus and potassium during budding and flowering."
    },
    "Snake Plant": {
        "min_moisture": 30.0,
        "max_moisture": 45.0,
        "container_ml_full": 200.0,
        "heat_stress_c": 42.0,
        "humidity_stress_pct": 95.0,
        "nutrient_notes": "Extremely low nutrition requirement. Avoid waterlogged potting mix."
    }
}


class PlantCareAssistant:
    @classmethod
    def generate_advisory(
        cls,
        plant_name: str,
        growth_stage: str = "Vegetative",
        current_moisture: float = 52.0,
        temperature: float = 31.0,
        humidity: float = 65.0,
        forecast_rain_mm: float = 0.0,
        hydrogel_present: bool = True,
        yellowing_observed: bool = False
    ) -> PlantCareAdvisoryOutput:
        """
        Synthesizes agronomic sensor signals and plant growth stage into a structured daily advisory.
        """
        profile = PLANT_PROFILES.get(plant_name, PLANT_PROFILES["Tomato"])
        min_sm = profile["min_moisture"]
        max_sm = profile["max_moisture"]
        base_ml = profile["container_ml_full"]

        # Stage multiplier
        stage_factor = {
            "Seedling": 0.5,
            "Vegetative": 0.85,
            "Flowering": 1.15,
            "Fruiting": 1.25,
            "Mature": 0.75
        }.get(growth_stage, 1.0)

        # 1. Moisture & Urgency Analysis
        if forecast_rain_mm >= 8.0:
            urgency = "Not Needed"
            vol_ml = 0.0
            hydrogel_desc = (
                "Upcoming rainfall will replenish container moisture. Hydrogel granules will absorb excess "
                "precipitation, storing it safely inside polymer beads to prevent anaerobic root drowning."
            )
        elif current_moisture < min_sm:
            urgency = "Immediate Replenishment"
            # Calculate deficit replenishment
            deficit_pct = max(0.0, (min_sm + 5.0) - current_moisture)
            vol_ml = round(base_ml * stage_factor * (deficit_pct / 20.0), 0)
            vol_ml = max(150.0, min(650.0, vol_ml))
            if hydrogel_present:
                hydrogel_desc = (
                    "Moisture has dipped below the species threshold. Hydrogel beads have released their primary stored water "
                    "over the past 36-48h and are now collapsed. Applying irrigation will re-swell the hydrogel matrix within 20 minutes."
                )
            else:
                hydrogel_desc = (
                    "Potting mix has dried past critical threshold. Without hydrogel buffer, container substrate is prone to "
                    "hydrophobic channeling where water quickly runs down the container edges without wetting the root ball."
                )
        elif current_moisture > max_sm + 8.0:
            urgency = "Not Needed"
            vol_ml = 0.0
            hydrogel_desc = (
                "Substrate is saturated above optimal aeration limits. Suspend watering immediately. Ensure bottom drainage perforations "
                "are unobstructed so gravitational drainage can proceed."
            )
        else:
            urgency = "Moderate Need"
            if current_moisture <= (min_sm + 5.0):
                vol_ml = round(base_ml * 0.45 * stage_factor, 0)
            else:
                vol_ml = 0.0
                urgency = "Not Needed"
            hydrogel_desc = (
                "Moisture is well buffered within the species optimal comfort zone. Hydrogel polymer is actively releasing "
                "hydration at the root boundary at a steady matric potential."
            )

        # 2. Temperature & Humidity Stress Alert
        stress_alert = None
        if temperature >= profile["heat_stress_c"]:
            stress_alert = (
                f"HEAT STRESS WARNING ({temperature:.1f}°C): Transpiration rates in container grow bags spike rapidly above "
                f"{profile['heat_stress_c']}°C. Provide partial 30% green shading between 11:30 AM and 3:30 PM to prevent leaf scorch."
            )
        elif humidity >= profile["humidity_stress_pct"]:
            stress_alert = (
                f"HIGH HUMIDITY WARNING ({humidity:.0f}%): Prolonged saturated air with restricted terrace breeze creates prime conditions "
                f"for powdery mildew and fungal spore germination. Increase pot spacing to 45cm for improved cross-ventilation."
            )

        # 3. Yellowing Diagnostic Tree
        yellowing_tree = [
            "LOWER LEAVES DRY & CRISPY: Chronic underwatering or salt buildup from tap water. Flush pot with fresh water.",
            "LOWER LEAVES SOFT & LIMP: Overwatering or compacted potting mix causing root hypoxia. Allow top 2 inches to dry.",
            "INTERVEINAL CHLOROSIS (VEINS REMAIN GREEN): Micronutrient lockout (Iron/Magnesium), commonly caused by alkaline pH (>7.2). Apply Epsom salt (1 tsp/L) or chelated iron foliar spray.",
            "STIPPLED YELLOW MOTTLING: Pest damage from spider mites or thrips. Inspect leaf undersides with a 10x lens."
        ]

        # 4. Immediate Actions
        actions = []
        if urgency == "Immediate Replenishment":
            actions.append(f"Apply {int(vol_ml)} mL of room-temperature water directly around the root zone (avoid wetting foliage).")
        elif urgency == "Moderate Need" and vol_ml > 0:
            actions.append(f"Optional maintenance top-up: Apply {int(vol_ml)} mL water during late evening.")
        else:
            actions.append("No irrigation required today. Soil moisture is within the healthy species buffer.")

        if growth_stage in ["Flowering", "Fruiting"]:
            actions.append("Support flower cluster weight with soft bamboo stakes or garden twine.")
            actions.append("Ensure consistent watering: moisture fluctuations during fruiting cause fruit splitting and blossom drop.")
        elif growth_stage == "Vegetative":
            actions.append("Pinch off apical growth tips if a bushier canopy with more lateral flowering branches is desired.")

        if yellowing_observed:
            actions.append("Inspect lower foliage against the Yellowing Diagnostic Tree to verify whether root aeration or nitrogen is limiting.")

        # 5. Upcoming 3-Day Watch
        watch_list = [
            f"Day 1: Monitor surface drying. Hydrogel keeps the root zone 10-15% more moist than the visible surface crust.",
            f"Day 2: Check underside of young leaves for early aphid or whitefly clusters.",
            f"Day 3: Expected weather: Temp {temperature:.0f}°C, Humidity {humidity:.0f}%. Adjust evening inspection accordingly."
        ]

        return PlantCareAdvisoryOutput(
            plant_name=plant_name,
            growth_stage=growth_stage,
            watering_urgency=urgency,
            watering_volume_ml=vol_ml,
            hydrogel_status=hydrogel_desc,
            yellowing_diagnostic_tree=yellowing_tree,
            temperature_humidity_stress_alert=stress_alert,
            nutrient_adjustment=profile["nutrient_notes"],
            immediate_actions=actions,
            upcoming_3_day_watch=watch_list
        )
