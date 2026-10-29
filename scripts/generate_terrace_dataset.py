"""
Physics-Informed Terrace Garden Dataset Generator CLI for IRRIGATEWISE
=============================================================================
DATASET CLASSIFICATION: 45-Day Terrace Garden Simulation Dataset
PERIOD: 15 August 2026 00:00 UTC to 28 September 2026 23:00 UTC
PHYSICS ENGINE: Hydrogel Sorption-Desorption & Evapotranspiration Dynamics
RANDOM SEED: 42 (Fully Reproducible)
TARGET SETUP: 10 x 15L Grow Bags with Cocopeat-Vermicompost Mix
CANONICAL DESTINATION: datasets/moisture_iot/sensor_timeseries_dataset.csv
=============================================================================
This CLI delegates directly to the unified physics simulation engine in
`backend.ml.generate_dataset`, eliminating code duplication.
"""

import os
import sys
import argparse
from datetime import datetime, timezone

# Add backend directory to path so ml modules can be loaded from anywhere
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from ml.generate_dataset import (
    generate_complete_dataset,
    generate_sensor_timeseries,
    calculate_et0,
    SEED
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate physics-informed terrace garden soil moisture timeseries dataset."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(BASE_DIR, "datasets", "moisture_iot", "sensor_timeseries_dataset.csv"),
        help="Path where the generated CSV will be saved (default: datasets/moisture_iot/sensor_timeseries_dataset.csv)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=45,
        help="Number of continuous trial days to simulate (default: 45)"
    )
    parser.add_argument(
        "--dosage",
        type=float,
        default=25.0,
        help="Hydrogel dosage in grams per 15L container pot (default: 25.0g)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 75)
    print("IRRIGATEWISE PHYSICS-INFORMED DATASET GENERATOR")
    print(f"Target Destination: {args.output}")
    print(f"Simulation Horizon: {args.days} Days (15 Aug 2026 - 28 Sep 2026)")
    print(f"Hydrogel Dosage:    {args.dosage}g per container pot")
    print("=" * 75)
    
    saved_path = generate_complete_dataset(output_path=args.output)
    print(f"\n[SUCCESS] Canonical dataset is ready at:\n  -> {saved_path}")

if __name__ == "__main__":
    main()
