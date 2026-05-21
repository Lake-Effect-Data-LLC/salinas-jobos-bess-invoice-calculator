from datetime import datetime, time
from classes import InverterState
from itertools import islice

# HELPER FUNCTIONS
def is_valid_irradiance_interval(interval) -> bool:
    IRRADIANCE_THRESHOLD_KWH_PER_M2 = 0.1  # Equivalent to 100 W/m²
    return interval.irradiance_plane_of_array > IRRADIANCE_THRESHOLD_KWH_PER_M2

def is_last_interval_of_day(timestamp: datetime) -> bool:
    return timestamp.time() ==  time(23, 50, 0)  # Last 10-minute interval (23:50-00:00)

# Calculate the rolling 30 day Facility Availabliity per interval
def calculate_FA_rolling(facility_info, interval_data, prev_UAs_rolling):

    def calculate_WAs(interval_data):
        WAs = []
        NC = facility_info.maximum_dispatch_limit_mw * 1000
        UC = facility_info.inverter_capacities

        for interval in interval_data:
            total = 0
            for inv_id, UA_i in interval:
                UC_i = UC[inv_id]
                total += (UA_i * UC_i)
            WAs.append(total / NC)
        return WAs

    def calculate_UAs():
        inverter_data = []
        for interval in interval_data:
            temp = []

            # create list of inverter states for time interval
            inverter_states = []
            for inverter_id in interval.inverter_is_event_interval:
                is_event = int(interval.inverter_is_event_interval[inverter_id])
                is_failure = int(interval.inverter_is_failure_interval[inverter_id])
                t = int(is_valid_irradiance_interval(interval))
                state = InverterState(
                    id=inverter_id,
                    t=t,
                    u_e=is_event,
                    u_i=is_failure,
                )
                inverter_states.append(state)

            # create entry and add it to the queue
            entry = (interval.timestamp, inverter_states)
            prev_UAs_rolling.append(entry)
                
            # run sum for each inv
            inverter_sums = [
                InverterState(id=f"inv_{i:03d}")
                for i in range(25)
            ]
            last_30_days = list(prev_UAs_rolling)[-4320:]
            for data in last_30_days:
                for i, inverter in enumerate(data[1]):
                    curr = inverter_sums[i]
                    curr.t += inverter.t
                    curr.u_e += inverter.u_e
                    curr.u_i += inverter.u_i

            # calculate inverter availability for each inverter
            for inv in inverter_sums:
                U_a = 0
                if inv.t - inv.u_e > 0:
                     U_a = (inv.t - inv.u_e - inv.u_i) / (inv.t - inv.u_e)
                temp.append((inv.id, U_a))
            inverter_data.append(temp)
        return inverter_data

    inverter_data = calculate_UAs()
    WA_i = calculate_WAs(inverter_data)
    FA = sum(WA_i) / len(WA_i)
    return FA

# Calculate ENEO per interval
def calculate_ENEO_i(facility_info, interval_data, daily_data, prev_days, FA):
    all_ENEO_i = []
    for interval in interval_data:
        GK_i = interval.irradiance_plane_of_array * facility_info.plane_of_array_area_m2 # KWh/m2

        total = 0

        # iterate through the last 7 days in prev days
        last_7_days = list(prev_days)[-7:]

        for day, NEO_j, GK_j in last_7_days:
            total += (NEO_j / (GK_j * facility_info.plane_of_array_area_m2))

        ENEO_i = (total / 7) * GK_i * FA
        all_ENEO_i.append(ENEO_i/100)

        # if last interval of day and day is not an event day, add to list of no event days
        dt = interval.timestamp
        if is_last_interval_of_day(interval.timestamp):
            matching_daily = None
            for day in daily_data:
                if interval.timestamp.date() == day.day.date():
                    matching_daily = day
                    break
            if matching_daily.is_prepa_risk_event == False:
                dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                prev_days.append((dt_str, round(matching_daily.daily_neo_kwh, 4), round(matching_daily.daily_irradiance_plane_of_array, 4)))

    return all_ENEO_i

# Calculate Base Rate
def calculate_BR(facility_info, curr_day):
    ESCALATION_RATE = 0.02
    BASE_TARIFF = facility_info.base_tariff

    cod = facility_info.commercial_operation_date
    first_agreement_year_end = cod.replace(year=cod.year + 1)

    # Check how much to increase base tariff rate
    if curr_day < first_agreement_year_end:
        return BASE_TARIFF
    else:
        escalation_count = 0
        year = cod.year + 1
        while True:
            july_1 = datetime(year, 7, 1)
            if july_1 <= curr_day:
                escalation_count += 1
                year += 1
            else:
                break

    escalated_rate = BASE_TARIFF * ((1 + ESCALATION_RATE) ** escalation_count)
    return escalated_rate

# Calculate Contract Rate
def calculate_CR(facility_info, NEO, DNEO, curr_day, BR):

    # Update yearly output
    if curr_day.month == 1:
        facility_info.yearly_neo_and_dneo = (NEO + DNEO)
    else:
        facility_info.yearly_neo_and_dneo += (NEO + DNEO)

    # if yearly output is in excess of the P50
    yearly_output = facility_info.yearly_neo_and_dneo
    if yearly_output > (facility_info.P50_energy_yield * 1.1):
        CR = BR * 0.8
    else:
        CR = BR

    return CR

# Calculate Shortfall Credits
def calculate_SC(prev_outputs, facility_info, BR):

    # if its been less than 2 years (rolling period length)
    if len(prev_outputs) < 24:
        return 0

    P50 = facility_info.P50_energy_yield
    estimated_output_of_rolling_period = (P50 * 2) * 0.9 
    total_output_of_rolling_period = sum(
        val for _, val in islice(prev_outputs, max(len(prev_outputs)-24, 0), len(prev_outputs))
    )

    RER = 0.17 # Replacement Energy Rate ($/kWh)
    EQS = estimated_output_of_rolling_period - total_output_of_rolling_period # Energy Quantity Shortfall

    if EQS <= 0:
        return 0

    # Calculate Shortfall Credit ($)
    SC = (RER - BR) * EQS
    return SC