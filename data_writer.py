import os
import csv
from pathlib import Path

OUTPUT_DIR = Path("output")

def get_output_path(filename: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True) 
    return OUTPUT_DIR / filename


def write_outputs(prev_outputs):
    csv_path = get_output_path('new_prev_outputs.csv')

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        for timestamp, value in prev_outputs:
            writer.writerow([
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                f"{value:.2f}"
            ])