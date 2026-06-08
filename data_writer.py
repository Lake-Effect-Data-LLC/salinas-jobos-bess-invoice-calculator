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
    "Other_ADJ",
    "ALD",
    "CLD",
    "Actual_Efficiency",
    "ELD",
    "ADJ_Total",
    "MP",
]


def get_output_path(filename, output_dir=OUTPUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    return output_dir / filename


def write_bess_monthly_results(
    monthly_results,
    filename="bess_monthly_results.csv",
    output_dir=OUTPUT_DIR,
):
    csv_path = get_output_path(filename, output_dir)

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
                    "Other_ADJ": _format_decimal(result.other_adj),
                    "ALD": _format_decimal(result.ald),
                    "CLD": _format_decimal(result.cld),
                    "Actual_Efficiency": _format_optional_decimal(
                        result.actual_efficiency
                    ),
                    "ELD": _format_decimal(result.eld),
                    "ADJ_Total": _format_decimal(result.adj_total),
                    "MP": _format_decimal(result.mp),
                }
            )

    return csv_path


def _format_decimal(value):
    return f"{value:.6f}"


def _format_optional_decimal(value):
    if value is None:
        return ""

    return _format_decimal(value)
