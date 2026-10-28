""" Database Seeding Script for IRRIGATEWISE. Populates initial baseline user, soil data, irrigation, and on records,
and initial sensor telemetry records for Erumaiyur Village field."""


from datetime import datetime, timedelta, timezone
from database import SessionLocal, engine
import models

def seed_database():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed baseline soil records if empty
        if db.query(models.SoilData).count() == 0:
            sample_soil = [
                (92.0, 48.0, 220.0, 6.8, 0.85, 78.2, "High", 0),
                (88.0, 44.0, 210.0, 6.9, 0.80, 74.5, "High", 7),
                (72.0, 38.0, 185.0, 7.1, 0.62, 62.3, "Medium", 14),
                (76.0, 40.0, 192.0, 7.0, 0.65, 65.1, "Medium", 21),
                (64.0, 32.0, 170.0, 7.3, 0.55, 55.4, "Medium", 28),
                (94.0, 50.0, 225.0, 6.7, 0.88, 80.1, "High", 35),
                (52.0, 26.0, 145.0, 7.6, 0.40, 42.3, "Low", 42),
                (85.0, 42.0, 205.0, 6.8, 0.82, 70.8, "High", 49),
            ]
            for n, p, k, ph, oc, score, cls, days_ago in sample_soil:
                rec = models.SoilData(
                    user_id=1,
                    nitrogen=n,
                    phosphorus=p,
                    potassium=k,
                    ph=ph,
                    organic_carbon=oc,
                    fertility_score=score,
                    classification=cls,
                    created_at=datetime.now(timezone.utc) - timedelta(days=days_ago)
                )
                db.add(rec)
            db.commit()
            print(f"Seeded {len(sample_soil)} soil records.")

        # 2. Seed baseline irrigation records if empty
        if db.query(models.IrrigationData).count() == 0:
            sample_irr = [
                (58.0, 70.0, 12.0, 10.2, 31.8, 0),
                (55.0, 70.0, 15.0, 12.75, 28.4, 1),
                (60.0, 70.0, 10.0, 8.5, 31.8, 2),
                (52.0, 70.0, 18.0, 15.3, 23.2, 3),
                (63.0, 70.0, 7.0, 5.95, 35.5, 4),
                (57.0, 70.0, 13.0, 11.05, 30.1, 5),
                (59.0, 70.0, 11.0, 9.35, 32.0, 6),
            ]
            for curr, opt, smd, req, saved, days_ago in sample_irr:
                rec = models.IrrigationData(
                    user_id=1,
                    sm_current=curr,
                    sm_optimal=opt,
                    smd=smd,
                    irrigation_required=req,
                    water_saved=saved,
                    created_at=datetime.now(timezone.utc) - timedelta(days=days_ago)
                )
                db.add(rec)
            db.commit()
            print(f"Seeded {len(sample_irr)} irrigation records.")

        # 3. Seed initial sensor readings if empty
        if db.query(models.SensorReading).count() == 0:
            now = datetime.now(timezone.utc)
            sample_readings = []
            for i in range(24):
                time_point = now - timedelta(hours=23 - i)
                # Diurnal temperature oscillation (26°C night to 35°C day)
                hour = time_point.hour
                temp = round(28.0 + 6.0 * (1 - abs(hour - 14) / 12), 1)
                humidity = round(80.0 - 20.0 * (1 - abs(hour - 14) / 12), 1)
                # Soil moisture gradually declining from 62% to 54%
                moisture = round(62.0 - (i * 0.35), 1)
                sample_readings.append(
                    models.SensorReading(
                        device_id="ESP32_FIELD_01",
                        timestamp=time_point,
                        soil_moisture=moisture,
                        temperature=temp,
                        humidity=humidity,
                        rainfall=0.0,
                        wind_speed=round(12.0 + (i % 5), 1),
                        soil_type="loam",
                        crop_type="Samba Rice",
                        hydrogel_present=1,
                        hydrogel_dosage=50.0,
                        pump_status="OFF",
                        created_at=time_point
                    )
                )
            db.add_all(sample_readings)
            db.commit()
            print(f"Seeded {len(sample_readings)} initial sensor readings.")

        print("Database seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
