import csv
import warnings
from pathlib import Path


BESS_REQUIRED_COLUMNS = {
    "bess_contract_values_template.csv": {
        "agreement_year",
        "cppf",
        "cpppif",
        "DDD",
        "TA",
        "RER",
        "GE",
        "CLD_uses_DDE_multiplier",
        "ELD_uses_CE_times_GE",
        "design_dmax",
        "design_duration_energy",
        "annual_duration_energy_degradation_rate",
        "design_charge_energy",
        "grid_system_waiting_period_hours",
        "force_majeure_waiting_period_hours",
        "scheduled_maintenance_allowance_hours",
    },
    "bess_yearly_inputs_template.csv": {
        "agreement_year",
        "DDE",
        "TR",
    },
    "bess_monthly_inputs_template.csv": {
        "timestamp_month",
        "agreement_year",
        "Other_ADJ",
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
        "ramp_failure_caused_outage",
        "outage_start",
        "outage_end",
        "outage_equivalent_unavhrs",
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
    validate_input_files(csv_paths)


def validate_input_files(csv_paths):
    if not csv_paths:
        raise ValueError("No input files were provided for validation.")

    paths = [Path(csv_path) for csv_path in csv_paths]
    _validate_files_exist(paths)
    _validate_known_bess_headers(paths)
    _validate_performance_test_ramp_outage_fields(paths)
    _warn_if_tr_misses_prior_year_failed_test_carry(paths)


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
    with path.open(newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile)
        try:
            return {column.strip() for column in next(reader)}
        except StopIteration as exc:
            raise ValueError(f"{path} is empty.") from exc


def _validate_performance_test_ramp_outage_fields(paths):
    for path in paths:
        if path.name != "Performance_Tests.csv":
            continue

        with path.open(newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row_number, row in enumerate(reader, start=2):
                if not _csv_bool(row.get("ramp_failure_caused_outage")):
                    continue

                missing_fields = [
                    field_name
                    for field_name in [
                        "outage_start",
                        "outage_end",
                        "outage_equivalent_unavhrs",
                    ]
                    if not str(row.get(field_name, "")).strip()
                ]
                if missing_fields:
                    formatted_fields = ", ".join(missing_fields)
                    raise ValueError(
                        f"{path} row {row_number} has "
                        "ramp_failure_caused_outage=TRUE but is missing "
                        f"{formatted_fields}."
                    )

                try:
                    outage_hours = float(row["outage_equivalent_unavhrs"])
                except ValueError as exc:
                    raise ValueError(
                        f"{path} row {row_number} has non-numeric "
                        "outage_equivalent_unavhrs."
                    ) from exc

                if outage_hours < 0:
                    raise ValueError(
                        f"{path} row {row_number} has negative "
                        "outage_equivalent_unavhrs."
                    )


def _warn_if_tr_misses_prior_year_failed_test_carry(paths):
    contract_path = _find_path(
        paths,
        {"bess_contract_values_template.csv", "bess_contract_values.csv"},
    )
    yearly_path = _find_path(
        paths,
        {"bess_yearly_inputs_template.csv", "bess_yearly_inputs.csv"},
    )
    tests_path = _find_path(paths, {"Performance_Tests.csv"})
    if contract_path is None or yearly_path is None or tests_path is None:
        return

    contract_by_year = _read_rows_by_year(contract_path)
    yearly_by_year = _read_rows_by_year(yearly_path)
    tests_by_year = {}
    with tests_path.open(newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not _csv_bool(row.get("prepa_approved")):
                continue

            agreement_year = int(row["agreement_year"])
            tests_by_year.setdefault(agreement_year, []).append(row)

    for agreement_year, yearly_row in yearly_by_year.items():
        if agreement_year <= 1:
            continue

        prior_year = agreement_year - 1
        prior_tests = tests_by_year.get(prior_year, [])
        if not prior_tests:
            continue

        prior_yearly = yearly_by_year.get(prior_year)
        prior_contract = contract_by_year.get(prior_year)
        if prior_yearly is None or prior_contract is None:
            continue

        last_test = max(prior_tests, key=lambda row: str(row["test_date"]))
        prior_dde = float(prior_yearly["DDE"])
        last_tde = float(last_test["TDE"])
        if last_tde >= 0.99 * prior_dde:
            continue

        ddd = float(prior_contract["DDD"])
        expected_tr = last_tde / ddd
        actual_tr = float(yearly_row["TR"])
        if actual_tr <= expected_tr + 1e-9:
            continue

        warnings.warn(
            f"{yearly_path} agreement_year {agreement_year} has TR={actual_tr:.2f}, "
            f"but the last approved Year {prior_year} Performance Test "
            f"({last_test['test_id']}) had TDE={last_tde:.2f} below "
            f"0.99 x DDE={0.99 * prior_dde:.2f}. Expected TR should be no "
            f"greater than TDE/DDD={expected_tr:.2f} unless a documented "
            "contract adjustment applies.",
            UserWarning,
        )


def _find_path(paths, names):
    for path in paths:
        if path.name in names:
            return path

    return None


def _read_rows_by_year(path):
    with path.open(newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        return {int(row["agreement_year"]): row for row in reader}


def _csv_bool(value):
    return str(value or "").strip().lower() in {"true", "t", "yes", "y", "1"}
