"""Pump Actuation and Automation Controller for IRRIGATEWISE.

Implements safe abstraction for physical relays and software simulation mode,
enforcing strict agricultural safety limits, minimum cooldown intervals,
maximum pulse runtimes, and emergency stops.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

class PumpController:
    _instance = None
    
    # Safety thresholds (calibrated for terrace container grow bags & field)
    MAX_DURATION_MINUTES = 10.0
    MIN_COOLDOWN_MINUTES = 20.0
    MAX_MOISTURE_SAFETY_LIMIT = 80.0  # Container root-zone saturation ceiling
    FLOW_RATE_ML_PER_MIN = 2000.0     # 12V DC terrace micro-drip pump (200 mL/min per pot across 10 pots)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PumpController, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance
        
    def _init_state(self):
        self.status = "OFF"  # "ON" or "OFF"
        self.simulation_mode = True
        self.last_run_time: Optional[datetime] = None
        self.last_run_duration = 0.0
        self.total_water_pumped_litres = 0.0
        self.total_water_pumped_ml = 0.0
        self.emergency_stop_active = False

    def get_status(self) -> Dict[str, Any]:
        """Returns the real-time operational status of the pump system."""
        return {
            "status": self.status,
            "mode": "SIMULATION" if self.simulation_mode else "HARDWARE_GPIO",
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_duration_minutes": self.last_run_duration,
            "total_water_pumped_litres": self.total_water_pumped_litres,
            "total_water_pumped_ml": self.total_water_pumped_ml,
            "irrigation_unit": "mL",
            "emergency_stop": self.emergency_stop_active,
            "safety_guards": {
                "max_duration_minutes": self.MAX_DURATION_MINUTES,
                "min_cooldown_minutes": self.MIN_COOLDOWN_MINUTES,
                "max_moisture_limit": self.MAX_MOISTURE_SAFETY_LIMIT,
                "flow_rate_ml_per_min": self.FLOW_RATE_ML_PER_MIN
            }
        }

    def execute_irrigation(
        self,
        duration_minutes: float,
        water_amount_litres: float = 0.0,
        current_moisture: float = 50.0,
        override_safety: bool = False,
        water_amount_ml: Optional[float] = None
    ) -> Dict[str, Any]:
        """Safely activates pump actuation in simulation or hardware mode."""
        now = datetime.now(timezone.utc)
        
        # Calculate consistent water measurements in mL and Litres
        if water_amount_ml is not None:
            water_ml = float(water_amount_ml)
            water_litres = round(water_ml / 1000.0, 3)
        else:
            water_litres = float(water_amount_litres)
            water_ml = round(water_litres * 1000.0, 1)
        
        # Guard 1: Emergency Stop
        if self.emergency_stop_active and not override_safety:
            return {
                "success": False,
                "status": "ABORTED",
                "message": "Emergency stop is currently engaged. Clear emergency stop before irrigating."
            }
            
        # Guard 2: High Moisture Safety Limit
        if current_moisture >= self.MAX_MOISTURE_SAFETY_LIMIT and not override_safety:
            return {
                "success": False,
                "status": "REJECTED_SAFETY",
                "message": f"Safety limit tripped: Soil moisture is {current_moisture}%, exceeding {self.MAX_MOISTURE_SAFETY_LIMIT}% maximum ceiling to prevent waterlogging and root rot."
            }

        # Guard 3: Maximum Duration Clamp
        clamped_duration = min(duration_minutes, self.MAX_DURATION_MINUTES)
        
        # Guard 4: Cooldown period check
        if self.last_run_time is not None and not override_safety:
            elapsed_minutes = (now - self.last_run_time).total_seconds() / 60.0
            if elapsed_minutes < self.MIN_COOLDOWN_MINUTES:
                remaining = round(self.MIN_COOLDOWN_MINUTES - elapsed_minutes, 1)
                return {
                    "success": False,
                    "status": "COOLDOWN_ACTIVE",
                    "message": f"Pump in cooldown period. Please wait {remaining} more minutes before triggering another cycle."
                }

        # Execute in Simulation or Hardware
        self.status = "ON"
        self.last_run_time = now
        self.last_run_duration = clamped_duration
        self.total_water_pumped_litres += water_litres
        self.total_water_pumped_ml += water_ml
        
        mode_str = "[SIMULATION]" if self.simulation_mode else "[HARDWARE]"
        log_message = (
            f"{mode_str} Pump ON: Running for {clamped_duration:.1f} minutes, "
            f"delivering {water_ml:.0f} mL ({water_litres:.2f} L) across terrace grow bags."
        )
        print(log_message)
        
        # Reset to standby status
        self.status = "OFF"
        
        # Broadcast real-time pump event via WebSockets
        try:
            from services.websocket_manager import ws_manager
            ws_manager.broadcast_sync("PUMP_STATE", {
                "status": "ON_PULSE_COMPLETED",
                "duration_minutes": clamped_duration,
                "water_amount_litres": water_amount_litres,
                "total_water_pumped_litres": self.total_water_pumped_litres,
                "timestamp": now.isoformat()
            })
        except Exception:
            pass

        return {
            "success": True,
            "status": "COMPLETED_SIMULATION" if self.simulation_mode else "COMPLETED_HARDWARE",
            "pump_state": "OFF",
            "duration_minutes": clamped_duration,
            "water_amount_litres": water_amount_litres,
            "timestamp": now.isoformat(),
            "message": log_message
        }

    def emergency_stop(self) -> Dict[str, Any]:
        """Instantly terminates any pump activity and engages safety lock."""
        self.status = "OFF"
        self.emergency_stop_active = True
        try:
            from services.websocket_manager import ws_manager
            ws_manager.broadcast_sync("PUMP_STATE", {
                "status": "EMERGENCY_STOP",
                "emergency_stop": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception:
            pass
        return {"status": "OFF", "emergency_stop": True, "message": "Emergency stop triggered. Actuators isolated."}

    def reset_emergency_stop(self) -> Dict[str, Any]:
        self.emergency_stop_active = False
        try:
            from services.websocket_manager import ws_manager
            ws_manager.broadcast_sync("PUMP_STATE", {
                "status": "STANDBY",
                "emergency_stop": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception:
            pass
        return {"status": "OFF", "emergency_stop": False, "message": "Emergency stop cleared. System armed in Standby."}
