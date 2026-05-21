# classes.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class FacilityData:
    """One-time configuration data for the facility"""
    maximum_dispatch_limit_mw: float
    num_inverters: int
    inverter_capacities: Dict[str, float]  # inverter_id -> capacity in kW
    commercial_operation_date: datetime
    plane_of_array_area_m2: float
    base_tariff: float
    P50_energy_yield: float
    yearly_neo_and_dneo: float

@dataclass
class BillingPeriodData:
    """Data for a billing period"""
    period_id: str
    other_credits: float = 0.0

@dataclass
class TimeIntervalData:
    """Data for a single 10-minute time interval"""
    timestamp: datetime
    neo_kwh: float
    irradiance_plane_of_array: float
    inverter_is_event_interval: Dict[str, bool]  # PREPA Caused
    inverter_is_failure_interval: Dict[str, bool]  # Not PREPA
    is_prepa_risk_event: bool

@dataclass
class DailyData:
    """Data summary for a single day"""
    day: datetime
    daily_neo_kwh: float
    daily_irradiance_plane_of_array: float
    is_prepa_risk_event: bool  

@dataclass
class InverterState:
    """Tracks running counts for inverter availability calculation"""
    id: str
    t: int = 0
    u_e: int = 0
    u_i: int = 0
