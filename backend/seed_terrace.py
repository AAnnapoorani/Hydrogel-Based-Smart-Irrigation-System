"""
Seeds starter container pots for the Terrace Garden Registry
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
import models

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    count = db.query(models.UserPlant).count()
    print(f"Current terrace plants count: {count}")
    if count == 0:
        p1 = models.UserPlant(
            name="Grow Bag 1 - Tomato (Pusa Ruby)",
            plant_type="Tomato",
            variety="Pusa Ruby",
            container_size_litres=15.0,
            planting_date="2026-09-15",
            growth_stage="Flowering",
            hydrogel_dosage_grams=25.0,
            health_status="Healthy",
            notes="50:30:20 Cocopeat mix with 25g SAP hydrogel buffer. Flower clusters setting well."
        )
        p2 = models.UserPlant(
            name="Grow Bag 2 - Mint (Pudina)",
            plant_type="Mint (Pudina)",
            variety="Spearmint Local",
            container_size_litres=10.0,
            planting_date="2026-10-01",
            growth_stage="Vegetative",
            hydrogel_dosage_grams=20.0,
            health_status="Healthy",
            notes="High transpiration container. Hydrogel preserves steady 62% root moisture."
        )
        p3 = models.UserPlant(
            name="Grow Bag 3 - Green Chili",
            plant_type="Chili",
            variety="Guntur Sannam",
            container_size_litres=15.0,
            planting_date="2026-09-20",
            growth_stage="Vegetative",
            hydrogel_dosage_grams=25.0,
            health_status="Healthy",
            notes="Compact branching. Moderate water requirement."
        )
        db.add_all([p1, p2, p3])
        db.commit()
        print("Seeded 3 starter terrace container plants.")
    else:
        print("Terrace plants table already contains records.")
    db.close()

if __name__ == "__main__":
    seed()
