import csv
import sys
from pathlib import Path


BESS_REQUIRED_COLUMNS = {
    "bess_contract_values_template.csv": {
        "agreement_year",
        "cppf",
        "cpppif",
        "DDD",
    },
    "bess_yearly_inputs_template.csv": {
        "agreement_year",
        "DDE",
        "TR",
    },
    "bess_monthly_inputs_template.csv": {
        "timestamp_month",
        "agreement_year",
        "ADJ",
        "BPHRS",
        "POHRS",
        "UNAVHRS",
        "UNAVPRODHRS",
        "GSE",
        "PFM",
        "IP",
    },
    "Performance_Tests.csv": {
        "test_id",
        "agreement_year",
        "test_type",
        "test_date",
        "requested_by",
        "TDE",
        "measured_ramp_rate",
        "prepa_approved",
    },
    "Monthly_Performance_Guarantee.csv": {
        "timestamp_month",
        "agreement_year",
        "CE",
        "DE",
        "AE_beg",
        "AE_end",
    },
}


def input_validation(*csv_paths):
    try:
        validate_input_files(csv_paths)
    except ValueError as exc:
        sys.exit(str(exc))


def validate_input_files(csv_paths):
    if not csv_paths:
        raise ValueError("No input files were provided for validation.")

    paths = [Path(csv_path) for csv_path in csv_paths]
    _validate_files_exist(paths)
    _validate_known_bess_headers(paths)


def _validate_files_exist(paths):
    missing_paths = [path for path in paths if not path.exists()]

    if missing_paths:
        formatted_paths = "\n".join(f"- {path}" for path in missing_paths)
        raise ValueError(f"Required input file(s) not found:\n{formatted_paths}")


def _validate_known_bess_headers(paths):
    for path in paths:
        required_columns = BESS_REQUIRED_COLUMNS.get(path.name)
        if required_columns is None:
            continue

        actual_columns = _read_csv_header(path)
        missing_columns = sorted(required_columns - actual_columns)

        if missing_columns:
            formatted_columns = ", ".join(missing_columns)
            raise ValueError(
                f"{path} is missing required column(s): {formatted_columns}"
            )


def _read_csv_header(path):
    with path.open(newline="") as csvfile:
        reader = csv.reader(csvfile)
        try:
            return {column.strip() for column in next(reader)}
        except StopIteration as exc:
            raise ValueError(f"{path} is empty.") from exc
