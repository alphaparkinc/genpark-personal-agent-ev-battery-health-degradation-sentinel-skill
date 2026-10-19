# -*- coding: utf-8 -*-
"""EV Battery Health & Degradation Sentinel Skill for GenPark Personal Agents."""
import json
from typing import Dict, Any

def audit_ev_battery_degradation(original_usable_kwh: float, current_max_range_km: float, original_rated_range_km: float, odometer_km: float, vehicle_age_months: int, fast_dc_charging_ratio_pct: float = 20.0) -> Dict[str, Any]:
    if original_rated_range_km <= 0 or original_usable_kwh <= 0:
        return {"error": "Invalid baseline battery specifications"}

    capacity_retention_pct = round((current_max_range_km / original_rated_range_km) * 100.0, 1)
    degradation_pct = round(100.0 - capacity_retention_pct, 1)

    # Typical OEM battery warranty threshold: 70% capacity retention within 8 years (96 months) or 160,000 km
    warranty_months_limit = 96
    warranty_km_limit = 160000.0
    within_warranty_window = (vehicle_age_months <= warranty_months_limit) and (odometer_km <= warranty_km_limit)
    warranty_claim_eligible = within_warranty_window and (capacity_retention_pct < 70.0)

    # Assess accelerated degradation from excessive DC fast charging
    dc_fast_impact = "HIGH_THERMAL_STRESS" if fast_dc_charging_ratio_pct > 50.0 else ("MODERATE_USAGE" if fast_dc_charging_ratio_pct > 25.0 else "MINIMAL_BENIGN")

    return {
        "original_rated_range_km": original_rated_range_km,
        "current_usable_range_km": current_max_range_km,
        "current_state_of_health_pct": capacity_retention_pct,
        "cumulative_capacity_fade_pct": degradation_pct,
        "vehicle_odometer_km": odometer_km,
        "vehicle_age_months": vehicle_age_months,
        "dc_fast_charge_stress_tier": dc_fast_impact,
        "within_oem_warranty_limits": within_warranty_window,
        "qualifies_for_warranty_pack_replacement": warranty_claim_eligible,
        "status": "FREE_WARRANTY_BATTERY_REPLACEMENT_ELIGIBLE" if warranty_claim_eligible else "NORMAL_DEGRADATION_TRAJECTORY",
        "guardian": "GenPark Automotive Powertrain Telemetry"
    }

def generate_battery_longevity_charging_protocol(battery_chemistry: str, daily_commute_km: float, ambient_temperature_c: float) -> Dict[str, Any]:
    guidelines = []

    if battery_chemistry == "lfp_lithium_iron_phosphate":
        charge_limit_pct = 100
        guidelines.append("Charge to 100% at least once per week for battery management system (BMS) cell balancing.")
    else:
        # NMC / NCA
        charge_limit_pct = 80
        guidelines.append("Cap daily routine charging at 80% SoC; reserve 100% only for long road trips.")
        guidelines.append("Avoid leaving the battery sitting below 10% or above 90% in elevated ambient heat.")

    if ambient_temperature_c < 5.0:
        guidelines.append("Enable scheduled departure preconditioning while plugged in to warm battery pack via grid power.")
    elif ambient_temperature_c > 35.0:
        guidelines.append("Charge in shaded carport or garage during cooler night hours to minimize thermal degradation.")

    return {
        "battery_chemistry": battery_chemistry.upper(),
        "ambient_temp_c": ambient_temperature_c,
        "recommended_daily_soc_charge_limit_pct": charge_limit_pct,
        "advisory_rules": guidelines,
        "estimated_life_extension": "Adherence slows capacity fade by up to 40% over a 5-year operating horizon."
    }
