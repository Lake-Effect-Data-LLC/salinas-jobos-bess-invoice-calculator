import csv
from pathlib import Path


OUTPUT_DIR = Path("output")

BESS_MONTHLY_RESULT_COLUMNS = [
    "timestamp_month",
    "agreement_year",
    "CPP",
    "MCC",
    "FA",
    "FAA",
    "PRA",
    "MFP",
    "ADJ",
    "MP",
]


def get_output_path(filename):
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR / filename


def write_bess_monthly_results(monthly_results, filename="bess_monthly_results.csv"):
    csv_path = get_output_path(filename)

    with csv_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=BESS_MONTHLY_RESULT_COLUMNS)
        writer.writeheader()

        for result in monthly_results:
            writer.writerow(
                {
                    "timestamp_month": result.timestamp_month,
                    "agreement_year": result.agreement_year,
                    "CPP": _format_decimal(result.cpp),
                    "MCC": _format_decimal(result.mcc),
                    "FA": _format_decimal(result.fa),
                    "FAA": _format_decimal(result.faa),
                    "PRA": _format_decimal(result.pra),
                    "MFP": _format_decimal(result.mfp),
                    "ADJ": _format_decimal(result.adj),
                    "MP": _format_decimal(result.mp),
                }
            )

    return csv_path


def _format_decimal(value):
    return f"{value:.6f}"
