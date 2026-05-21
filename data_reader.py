import pandas as pd
from typing import List
from datetime import datetime
from collections import defaultdict, deque
from typing import Deque, List, Tuple
from classes import FacilityData, BillingPeriodData, TimeIntervalData, DailyData, InverterState

def load_facility_and_billing_config(csv_file_path: str):

    df = pd.read_csv(csv_file_path, header=None)
    facility_data = {}
    inverter_capacities = {}
    
    current_section = None
    
    for idx, row in df.iterrows():
        first_col = str(row[0]).strip()
        
        # Identify sections
        if first_col == 'Facility Information':
            current_section = 'facility'
            continue
        elif first_col == 'Billing Period Information':
            current_section = 'billing'
            continue
        elif first_col == 'Inverter Nominal Capacities (kw)':
            current_section = 'inverters'
            continue
        
        # Skip empty rows
        if pd.isna(row[0]) or first_col == '':
            continue
        
        # Parse based on current section
        if current_section == 'facility':
            if not pd.isna(row[1]):
                facility_data[first_col] = row[1]
        
        elif current_section == 'billing':
            if not pd.isna(row[1]):
                facility_data[first_col] = row[1]
        
        elif current_section == 'inverters':
            if not pd.isna(row[1]) and first_col.startswith('inv_'):
                inverter_capacities[first_col] = float(row[1])
    
    # Create FacilityData object
    facility_config = FacilityData(
        maximum_dispatch_limit_mw=float(facility_data['Maximum Dispatch Limit (MW)']),
        num_inverters=int(facility_data['Number of Inverters']),
        inverter_capacities=inverter_capacities,
        commercial_operation_date=pd.to_datetime(facility_data['Commerical Operation Date']),
        plane_of_array_area_m2=float(facility_data['Plane of Array Area (m2)']),
        base_tariff=float(facility_data['Base Tariff ($)']),
        P50_energy_yield=float(facility_data['P50 Energy Yield (kWh)']),
        yearly_neo_and_dneo=float(facility_data['Yearly Total Output (kWh)'])
    )
    
    # Create BillingPeriodData object
    billing_config = BillingPeriodData(
        period_id=str(int(facility_data['Period ID'])),
        other_credits=float(facility_data['Other Credits'])
    )
    
    return facility_config, billing_config

def get_interval_data(plant_csv_path: str, inverter_csv_path: str) -> List[TimeIntervalData]:

    # Load CSVs
    plant_df = pd.read_csv(plant_csv_path)
    inverter_df = pd.read_csv(inverter_csv_path)

    # Parse timestamps
    plant_df["Timestamp"] = pd.to_datetime(
        plant_df["Timestamp"],
        format="mixed",
    )

    inverter_df["Timestamp"] = pd.to_datetime(
        inverter_df["Timestamp"],
        format="mixed",
    )

    # Group inverter data by timestamp for fast lookup
    inverter_groups = inverter_df.groupby("Timestamp")

    intervals: List[TimeIntervalData] = []

    for _, plant_row in plant_df.iterrows():
        timestamp = plant_row["Timestamp"]

        # All inverter rows for this 10-min interval
        inv_slice = inverter_groups.get_group(timestamp)

        inverter_is_event_interval = dict(
            zip(inv_slice["Inverter_ID"], inv_slice["Is_Event_Interval"])
        )

        inverter_is_failure_interval = dict(
            zip(inv_slice["Inverter_ID"], inv_slice["Is_Failure_Interval"])
        )

        # PREPA risk if any inverter has a PREPA-caused event
        is_prepa_risk_event = any(inverter_is_event_interval.values())

        interval = TimeIntervalData(
            timestamp=timestamp,
            neo_kwh=float(plant_row["NEO_kWh"]),
            irradiance_plane_of_array=float(plant_row["Irradiance_kWh_per_m2"]),
            inverter_is_event_interval=inverter_is_event_interval,
            inverter_is_failure_interval=inverter_is_failure_interval,
            is_prepa_risk_event=is_prepa_risk_event,
        )

        intervals.append(interval)

    return intervals

def get_daily_data(intervals: List[TimeIntervalData]) -> List[DailyData]:
    # Accumulator per day
    daily_accumulator = defaultdict(lambda: {
        "neo": 0.0,
        "irradiance_sum": 0.0,
        "interval_count": 0,
        "prepa_risk": False
    })

    for interval in intervals:
        day = interval.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)     
        daily_accumulator[day]["neo"] += interval.neo_kwh
        daily_accumulator[day]["irradiance_sum"] += interval.irradiance_plane_of_array
        daily_accumulator[day]["interval_count"] += 1
        daily_accumulator[day]["prepa_risk"] |= interval.is_prepa_risk_event

    # Convert to DailyData
    daily_data_list = [
        DailyData(
            day = day,
            daily_neo_kwh = data["neo"],
            daily_irradiance_plane_of_array = (
                data["irradiance_sum"] / data["interval_count"]
                if data["interval_count"] > 0 else 0.0
            ),
            is_prepa_risk_event = data["prepa_risk"]
        )
        for day, data in sorted(daily_accumulator.items())
    ]

    return daily_data_list

def get_inverter_availabilities(csv_file_path: str) -> List[InverterState]:
    df = pd.read_csv(csv_file_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    inverter_deque: Deque[Tuple[pd.Timestamp, List[InverterState]]] = deque()

    df = df.sort_values(["timestamp", "id"])

    for ts, group in df.groupby("timestamp"):
        inverter_states = [
            InverterState(
                id=row.id,
                t=row.t,
                u_e=row.u_e,
                u_i=row.u_i,
            )
            for row in group.itertuples(index=False)
        ]

        inverter_deque.append((ts, inverter_states))

    return inverter_deque

def get_prev_days(csv_file_path: str):

    data = deque()

    with open(csv_file_path, "r") as f:
        next(f, None)  # skip header

        for line in f:
            line = line.strip()
            if not line:
                continue
            day, daily_neo, daily_irradiance = line.split(",")
            data.append((
                day,
                float(daily_neo),
                float(daily_irradiance)
            ))

    return data

def get_inverter_availabilities_rolling(csv_file_path: str) -> Deque[Tuple[pd.Timestamp, List[InverterState]]]:
    df = pd.read_csv(csv_file_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    inverter_deque: Deque[Tuple[pd.Timestamp, List[InverterState]]] = deque()

    df = df.sort_values(["timestamp", "id"])

    for ts, group in df.groupby("timestamp"):
        inverter_states = [
            InverterState(
                id=row.id,
                t=row.t,
                u_e=row.u_e,
                u_i=row.u_i,
            )
            for row in group.itertuples(index=False)
        ]

        inverter_deque.append((ts, inverter_states))

    return inverter_deque

def get_prev_outputs(csv_file_path: str) -> Deque[Tuple[pd.Timestamp, float]]:
    df = pd.read_csv(csv_file_path, header=None)

    df.columns = ["Timestamp", "Value"]

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        format="mixed",
    )

    data: Deque[Tuple[pd.Timestamp, float]] = deque(
        (row.Timestamp, float(row.Value))
        for row in df.itertuples(index=False)
    )

    return data
