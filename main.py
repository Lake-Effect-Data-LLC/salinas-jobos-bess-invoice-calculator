from data_reader import get_interval_data, get_daily_data, get_inverter_availabilities, load_facility_and_billing_config, get_prev_days, get_prev_outputs
from calculations import calculate_ENEO_i, calculate_CR, calculate_FA_rolling, calculate_BR, calculate_SC
from data_writer import write_prev_days, write_inverter_states, write_facility_info, write_outputs
from report import generate_report, save_report
from error_checks import input_validation
from pathlib import Path
from pprint import pprint
import time
DATA_DIR = Path("data")

def main():
    start = time.time()

    #Define Filepaths
    facility_and_billing_info_csv = DATA_DIR / "facility_info.csv"
    plant_csv = DATA_DIR / "plant_data.csv"
    inverter_csv = DATA_DIR / "inverter_data.csv"
    prev_inverter_states = DATA_DIR / "prev_inverter_states.csv"
    no_event_days = DATA_DIR / "no_event_days.csv"
    prev_total_output = DATA_DIR / "prev_total_output.csv"

    # Input File Validation
    input_validation(facility_and_billing_info_csv, plant_csv, inverter_csv, prev_inverter_states, no_event_days, prev_total_output)

    # Get the facility and billing period data
    facility_info, billing_info = load_facility_and_billing_config(facility_and_billing_info_csv)

    # Read interval data for this billing period from files
    interval_data = get_interval_data(
        plant_csv_path=plant_csv,
        inverter_csv_path=inverter_csv,
    )

    # Aggregate intervals into daily data
    daily_data = get_daily_data(interval_data)
    curr_day = daily_data[0].day

    # Get data from previous billing periods
    prev_UAs_rolling = get_inverter_availabilities(prev_inverter_states)
    prev_days = get_prev_days(no_event_days)
    prev_outputs = get_prev_outputs(prev_total_output)

    # Calculate the FA with a rolling 30 day window (takes 2-3 minutes)
    FA = calculate_FA_rolling(facility_info, interval_data, prev_UAs_rolling)

    # Calculate ENEO
    ENEO_i = calculate_ENEO_i(facility_info, interval_data, daily_data, prev_days, FA) # Per Interval
    ENEO_n = sum(ENEO_i) # For entire billing period

    # Calculate Base Rate
    BR = calculate_BR(facility_info, curr_day)

    # Calculate the Monthly Payment
    NEO_n = sum(interval.neo_kwh for interval in interval_data)
    DNEO_n = ENEO_n - NEO_n
    CR_n = calculate_CR(facility_info, NEO_n, DNEO_n, curr_day, BR)
    OC_n = billing_info.other_credits
    MP = ((NEO_n + DNEO_n) * CR_n) - OC_n

    # Check for Shortfall Credits (Performance Guarantee)
    total_output = NEO_n + DNEO_n
    prev_outputs.append((curr_day, total_output))
    shortfall_credits = calculate_SC(prev_outputs, facility_info, BR)

    # Write output
    write_prev_days(prev_days)
    write_facility_info(facility_info, facility_and_billing_info_csv)
    write_inverter_states(prev_UAs_rolling)
    write_outputs(prev_outputs)

    #  Generate Report
    calculations = {
        'NEO_n': NEO_n,
        'ENEO_n': ENEO_n,
        'FA': FA,
        'DNEO_n': DNEO_n,
        'CR_n' : CR_n,
        'MP': MP,
        'BR': BR,
        'shortfall_credits' : shortfall_credits
    }

    start_date = daily_data[0].day
    end_date = daily_data[-1].day
    
    # Generate and save report
    report_text = generate_report(facility_info, billing_info, calculations, start_date, end_date)

    save_report(report_text, "report.txt")
    end = time.time() 
    print(f"Program took {end - start:.2f} seconds to execute")

if __name__ == "__main__":
    main()
