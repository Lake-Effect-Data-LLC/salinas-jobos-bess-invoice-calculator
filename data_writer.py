import os
import csv
from pathlib import Path

OUTPUT_DIR = Path("output")

def get_output_path(filename: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True) 
    return OUTPUT_DIR / filename

def write_prev_days(prev_days):
    csv_path = get_output_path('new_no_event_days.csv')

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        # header
        writer.writerow([
            "Day",
            "Daily_NEO",
            "Daily_Global_Irradiance"
        ])

        # rows
        for day, neo, irradiance in prev_days:
            writer.writerow([
                day,
                neo,
                irradiance
            ])

def write_facility_info(facility_info, csv_file_path):
    yearly_output = round(facility_info.yearly_neo_and_dneo, 2)
    new_csv_path = get_output_path('new_facility_info.csv')

    with open(csv_file_path, newline='') as f:
        lines = list(csv.reader(f))

    # Find the "Yearly Total Output (kWh)" row and update it
    for i, row in enumerate(lines):
        if row and row[0].strip() == "Yearly Total Output (kWh)":
            lines[i][1] = str(yearly_output)
        elif row[0].strip() == "Period ID":
            lines[i][1] = str(int(row[1]) + 1)

    # Write to new CSV
    with open(new_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(lines)

def write_inverter_states(inverter_deque):
    new_csv_path = get_output_path('new_prev_inverter_states.csv')

    rows = [["id", "timestamp", "t", "u_e", "u_i"]]

    for timestamp, inverter_states in inverter_deque:
        ts_str = (
            f"{timestamp.month}/"
            f"{timestamp.day}/"
            f"{timestamp.year} "
            f"{timestamp.hour}:{timestamp.minute:02d}"
        )

        for inv in inverter_states:
            rows.append(
                [
                    inv.id,
                    ts_str,
                    inv.t,
                    inv.u_e,
                    inv.u_i,
                ]
            )

    with open(new_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def write_outputs(prev_outputs):
    csv_path = get_output_path('new_prev_outputs.csv')

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        for timestamp, value in prev_outputs:
            writer.writerow([
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                f"{value:.2f}"
            ])