"""ESP32 IoT Sensor Node Simulator for IRRIGATEWISE.

=============================================================================
SIMULATION NOTICE: This is a software simulator emulating an ESP32 hardware
microcontroller equipped with a capacitive soil moisture sensor (v1.2),
DHT22 ambient temperature/humidity sensor, and an RS485 wind anemometer.
IT IS NOT PHYSICAL HARDWARE.
=============================================================================

Can be executed standalone to stream telemetry packets to the backend API
or trigger test anomalies to verify system resilience.
"""

import time
import math
import random
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional

DEFAULT_API_URL = "http://localhost:8000/api/v1/sensors/readings"

class ESP32Simulator:
    def __init__(self, device_id: str = "ESP32_FIELD_01", target_url: str = DEFAULT_API_URL):
        self.device_id = device_id
        self.target_url = target_url
        self.soil_moisture = 58.0
        self.hydrogel_present = 1
        self.hydrogel_dosage = 50.0
        self.pump_status = "OFF"

    def generate_packet(
        self,
        inject_anomaly: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates a realistic sensor packet with optional fault injection."""
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        # Diurnal temperature cycle
        solar = math.sin(math.pi * (hour - 5) / 14) if 5 <= hour <= 19 else 0.0
        temperature = round(27.0 + 7.0 * solar + random.uniform(-0.5, 0.5), 1)
        humidity = round(max(35.0, min(95.0, 78.0 - 22.0 * solar + random.uniform(-1.5, 1.5))), 1)
        wind_speed = round(max(4.0, 12.0 + 5.0 * solar + random.uniform(-1.0, 1.0)), 1)
        
        # Slow natural moisture decay
        decay = 0.20 if self.hydrogel_present else 0.35
        self.soil_moisture = max(18.0, round(self.soil_moisture - decay, 2))
        
        # Anomaly Injections for testing
        if inject_anomaly == "spike":
            self.soil_moisture = 98.5
        elif inject_anomaly == "impossible_value":
            self.soil_moisture = 145.0
        elif inject_anomaly == "freeze":
            pass  # keep identical
            
        return {
            "device_id": self.device_id,
            "soil_moisture": self.soil_moisture,
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": 0.0,
            "wind_speed": wind_speed,
            "soil_type": "loam",
            "crop_type": "Samba Rice",
            "hydrogel_present": self.hydrogel_present,
            "hydrogel_dosage": self.hydrogel_dosage,
            "pump_status": self.pump_status
        }

    def send_single_reading(self, inject_anomaly: Optional[str] = None) -> Dict[str, Any]:
        """Sends a single simulated telemetry packet to the backend."""
        packet = self.generate_packet(inject_anomaly)
        try:
            res = requests.post(self.target_url, json=packet, timeout=3)
            resp_data = res.json() if res.status_code == 200 else res.text
            
            # Check backend pump status to simulate real-world moisture recharge
            try:
                pump_res = requests.get("http://localhost:8000/api/v1/irrigation/pump-status", timeout=2)
                if pump_res.status_code == 200:
                    pump_info = pump_res.json()
                    # If pump was executed in the last minute, replenish soil moisture
                    if pump_info.get("last_run_time"):
                        last_t = datetime.fromisoformat(pump_info["last_run_time"].replace("Z", "+00:00"))
                        if (datetime.now(timezone.utc) - last_t).total_seconds() < 90:
                            if self.soil_moisture < 62.0:
                                self.soil_moisture = min(72.0, self.soil_moisture + 18.0)
                                print(f"  └─► [SOIL RECHARGE] Pump pulse detected! Root zone moisture replenished to {self.soil_moisture}%")
            except Exception:
                pass

            return {
                "success": res.status_code == 200,
                "status_code": res.status_code,
                "packet": packet,
                "response": resp_data
            }
        except Exception as e:
            return {"success": False, "error": str(e), "packet": packet}

    def run_continuous_stream(self, interval_seconds: int = 5, total_cycles: int = 10):
        """Runs periodic streaming of sensor readings demonstrating autonomous closed-loop response."""
        print("=" * 70)
        print(f"[ESP32 SIMULATOR] Autonomous Stream Target: {self.target_url}")
        print(f"Cycle Interval: {interval_seconds}s | Planned Cycles: {total_cycles}")
        print("=" * 70)
        
        for cycle in range(1, total_cycles + 1):
            result = self.send_single_reading()
            if result.get("success"):
                pkt = result["packet"]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Cycle {cycle}/{total_cycles}: Moisture={pkt['soil_moisture']}% | Temp={pkt['temperature']}°C | Hum={pkt['humidity']}% -> Ingested (Auto ML Executed)")
            else:
                print(f"Cycle {cycle}: Transmission failed ({result.get('error')})")
            time.sleep(interval_seconds)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ESP32 IoT Node Simulator with Autonomous Closed-Loop Demo")
    parser.add_argument("--once", action="store_true", help="Send single packet and exit")
    parser.add_argument("--anomaly", type=str, choices=["spike", "impossible_value", "freeze"], help="Inject test anomaly")
    parser.add_argument("--cycles", type=int, default=5, help="Number of cycles to send")
    parser.add_argument("--interval", type=int, default=3, help="Interval in seconds")
    parser.add_argument("--dry", action="store_true", help="Start with dry soil (<40%) to demonstrate autonomous ML pump trigger")
    args = parser.parse_args()
    
    sim = ESP32Simulator()
    if args.dry:
        sim.soil_moisture = 37.5
        print("[DEMO MODE] Forced dry root-zone soil moisture: 37.5% (triggers ML anticipatory deficit)")
        
    if args.once:
        print(sim.send_single_reading(inject_anomaly=args.anomaly))
    else:
        sim.run_continuous_stream(interval_seconds=args.interval, total_cycles=args.cycles)

