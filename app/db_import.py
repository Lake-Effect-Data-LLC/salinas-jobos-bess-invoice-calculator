from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.db import ensure_project_and_dataset


INPUT_FILES = {
    "contract_values": "bess_contract_values_template.csv",
    "yearly_inputs": "bess_yearly_inputs_template.csv",
    "monthly_inputs": "bess_monthly_inputs_template.csv",
    "monthly_performance_guarantee": "Monthly_Performance_Guarantee.csv",
    "performance_tests": "Performance_Tests.csv",
}


def import_project_csvs(
    engine,
    project_id,
    project_name,
    data_dir,
    dataset_name="actual",
    replace=True,
):
    data_path = Path(data_dir)

    with engine.begin() as connection:
        dataset_config_id = ensure_project_and_dataset(
            connection,
            project_id=project_id,
            project_name=project_name,
            dataset_name=dataset_name,
        )
        if replace:
            _delete_existing_dataset_rows(connection, dataset_config_id)

        counts = {
            "contract_values": _import_contract_values(
                connection,
                dataset_config_id,
                data_path / INPUT_FILES["contract_values"],
            ),
            "yearly_inputs": _import_yearly_inputs(
                connection,
                dataset_config_id,
                data_path / INPUT_FILES["yearly_inputs"],
            ),
            "monthly_inputs": _import_monthly_inputs(
                connection,
                dataset_config_id,
                data_path / INPUT_FILES["monthly_inputs"],
            ),
            "monthly_performance_guarantee": _import_monthly_performance_guarantee(
                connection,
                dataset_config_id,
                data_path / INPUT_FILES["monthly_performance_guarantee"],
            ),
            "performance_tests": _import_performance_tests(
                connection,
                dataset_config_id,
                data_path / INPUT_FILES["performance_tests"],
            ),
        }

    return counts


def _delete_existing_dataset_rows(connection, dataset_config_id):
    for table_name in (
        "validation_result",
        "row_edit_history",
        "performance_tests",
        "monthly_performance_guarantee",
        "monthly_inputs",
        "yearly_inputs",
        "contract_values",
    ):
        connection.execute(
            text(f"DELETE FROM {table_name} WHERE dataset_config_id = :dataset_config_id"),
            {"dataset_config_id": dataset_config_id},
        )


def _import_contract_values(connection, dataset_config_id, csv_path):
    df = pd.read_csv(csv_path)
    rows = []
    for row in df.to_dict("records"):
        rows.append(
            {
                "dataset_config_id": dataset_config_id,
                "agreement_year": int(row["agreement_year"]),
                "cppf": _required_number(row, "cppf"),
                "cpppif": _required_number(row, "cpppif"),
                "ddd": _required_number(row, "DDD"),
                "ta": _required_number(row, "TA"),
                "rer": _required_number(row, "RER"),
                "ge": _required_number(row, "GE"),
                "design_dmax": _required_number(row, "design_dmax"),
                "design_duration_energy": _required_number(row, "design_duration_energy"),
                "annual_duration_energy_degradation_rate": _required_number(
                    row,
                    "annual_duration_energy_degradation_rate",
                ),
                "design_charge_energy": _required_number(row, "design_charge_energy"),
                "grid_system_waiting_period_hours": _required_number(
                    row,
                    "grid_system_waiting_period_hours",
                ),
                "force_majeure_waiting_period_hours": _required_number(
                    row,
                    "force_majeure_waiting_period_hours",
                ),
                "scheduled_maintenance_allowance_hours": _required_number(
                    row,
                    "scheduled_maintenance_allowance_hours",
                ),
                "source_reference": _optional_text(row, "source_reference"),
                "notes": _optional_text(row, "notes"),
            }
        )

    if rows:
        connection.execute(
            text(
                """
                INSERT INTO contract_values (
                    dataset_config_id,
                    agreement_year,
                    cppf,
                    cpppif,
                    ddd,
                    ta,
                    rer,
                    ge,
                    design_dmax,
                    design_duration_energy,
                    annual_duration_energy_degradation_rate,
                    design_charge_energy,
                    grid_system_waiting_period_hours,
                    force_majeure_waiting_period_hours,
                    scheduled_maintenance_allowance_hours,
                    source_reference,
                    notes
                )
                VALUES (
                    :dataset_config_id,
                    :agreement_year,
                    :cppf,
                    :cpppif,
                    :ddd,
                    :ta,
                    :rer,
                    :ge,
                    :design_dmax,
                    :design_duration_energy,
                    :annual_duration_energy_degradation_rate,
                    :design_charge_energy,
                    :grid_system_waiting_period_hours,
                    :force_majeure_waiting_period_hours,
                    :scheduled_maintenance_allowance_hours,
                    :source_reference,
                    :notes
                )
                """
            ),
            rows,
        )

    return len(rows)


def _import_yearly_inputs(connection, dataset_config_id, csv_path):
    df = pd.read_csv(csv_path)
    rows = []
    for row in df.to_dict("records"):
        rows.append(
            {
                "dataset_config_id": dataset_config_id,
                "agreement_year": int(row["agreement_year"]),
                "dde": _required_number(row, "DDE"),
                "tr": _optional_number(row, "TR"),
                "gc": _optional_number(row, "GC"),
                "source_reference": _optional_text(row, "source_reference"),
                "notes": _optional_text(row, "notes"),
            }
        )

    if rows:
        connection.execute(
            text(
                """
                INSERT INTO yearly_inputs (
                    dataset_config_id,
                    agreement_year,
                    dde,
                    tr,
                    gc,
                    source_reference,
                    notes
                )
                VALUES (
                    :dataset_config_id,
                    :agreement_year,
                    :dde,
                    :tr,
                    :gc,
                    :source_reference,
                    :notes
                )
                """
            ),
            rows,
        )

    return len(rows)


def _import_monthly_inputs(connection, dataset_config_id, csv_path):
    df = pd.read_csv(csv_path)
    rows = []
    for row in df.to_dict("records"):
        rows.append(
            {
                "dataset_config_id": dataset_config_id,
                "timestamp_month": _month_start(row["timestamp_month"]),
                "agreement_year": int(row["agreement_year"]),
                "other_adj": _required_number(row, "Other_ADJ"),
                "bphrs": _required_number(row, "BPHRS"),
                "pohrs": _required_number(row, "POHRS"),
                "unavhrs": _required_number(row, "UNAVHRS"),
                "unavprodhrs": _required_number(row, "UNAVPRODHRS"),
                "gse": _required_number(row, "GSE"),
                "pfm": _required_number(row, "PFM"),
                "ip": _required_number(row, "IP"),
                "source_reference": _optional_text(row, "source_reference"),
                "notes": _optional_text(row, "notes"),
            }
        )

    if rows:
        connection.execute(
            text(
                """
                INSERT INTO monthly_inputs (
                    dataset_config_id,
                    timestamp_month,
                    agreement_year,
                    other_adj,
                    bphrs,
                    pohrs,
                    unavhrs,
                    unavprodhrs,
                    gse,
                    pfm,
                    ip,
                    source_reference,
                    notes
                )
                VALUES (
                    :dataset_config_id,
                    :timestamp_month,
                    :agreement_year,
                    :other_adj,
                    :bphrs,
                    :pohrs,
                    :unavhrs,
                    :unavprodhrs,
                    :gse,
                    :pfm,
                    :ip,
                    :source_reference,
                    :notes
                )
                """
            ),
            rows,
        )

    return len(rows)


def _import_monthly_performance_guarantee(connection, dataset_config_id, csv_path):
    df = pd.read_csv(csv_path)
    rows = []
    for row in df.to_dict("records"):
        rows.append(
            {
                "dataset_config_id": dataset_config_id,
                "timestamp_month": _month_start(row["timestamp_month"]),
                "agreement_year": int(row["agreement_year"]),
                "ce": _required_number(row, "CE"),
                "de": _required_number(row, "DE"),
                "ae_beg": _required_number(row, "AE_beg"),
                "ae_end": _required_number(row, "AE_end"),
                "source_reference": _optional_text(row, "source_reference"),
                "notes": _optional_text(row, "notes"),
            }
        )

    if rows:
        connection.execute(
            text(
                """
                INSERT INTO monthly_performance_guarantee (
                    dataset_config_id,
                    timestamp_month,
                    agreement_year,
                    ce,
                    de,
                    ae_beg,
                    ae_end,
                    source_reference,
                    notes
                )
                VALUES (
                    :dataset_config_id,
                    :timestamp_month,
                    :agreement_year,
                    :ce,
                    :de,
                    :ae_beg,
                    :ae_end,
                    :source_reference,
                    :notes
                )
                """
            ),
            rows,
        )

    return len(rows)


def _import_performance_tests(connection, dataset_config_id, csv_path):
    df = pd.read_csv(csv_path)
    rows = []
    for row in df.to_dict("records"):
        rows.append(
            {
                "dataset_config_id": dataset_config_id,
                "test_id": _required_text(row, "test_id"),
                "agreement_year": int(row["agreement_year"]),
                "test_type": _required_text(row, "test_type"),
                "test_date": _required_date(row, "test_date"),
                "requested_by": _optional_text(row, "requested_by"),
                "tde": _required_number(row, "TDE"),
                "measured_ramp_rate": _optional_number(row, "measured_ramp_rate"),
                "certified_by": _optional_text(row, "certified_by"),
                "prepa_approved": _optional_bool(row, "prepa_approved"),
                "approval_date": _optional_date(row, "approval_date"),
                "cure_or_retest_date": _optional_date(row, "cure_or_retest_date"),
                "replaces_test_id": _optional_text(row, "replaces_test_id"),
                "ramp_failure_caused_outage": _optional_bool(
                    row,
                    "ramp_failure_caused_outage",
                ),
                "outage_start": _optional_datetime(row, "outage_start"),
                "outage_end": _optional_datetime(row, "outage_end"),
                "outage_equivalent_unavhrs": _optional_number(
                    row,
                    "outage_equivalent_unavhrs",
                    0.0,
                ),
                "source_reference": _optional_text(row, "source_reference"),
                "notes": _optional_text(row, "notes"),
            }
        )

    if rows:
        connection.execute(
            text(
                """
                INSERT INTO performance_tests (
                    dataset_config_id,
                    test_id,
                    agreement_year,
                    test_type,
                    test_date,
                    requested_by,
                    tde,
                    measured_ramp_rate,
                    certified_by,
                    prepa_approved,
                    approval_date,
                    cure_or_retest_date,
                    replaces_test_id,
                    ramp_failure_caused_outage,
                    outage_start,
                    outage_end,
                    outage_equivalent_unavhrs,
                    source_reference,
                    notes
                )
                VALUES (
                    :dataset_config_id,
                    :test_id,
                    :agreement_year,
                    :test_type,
                    :test_date,
                    :requested_by,
                    :tde,
                    :measured_ramp_rate,
                    :certified_by,
                    :prepa_approved,
                    :approval_date,
                    :cure_or_retest_date,
                    :replaces_test_id,
                    :ramp_failure_caused_outage,
                    :outage_start,
                    :outage_end,
                    :outage_equivalent_unavhrs,
                    :source_reference,
                    :notes
                )
                """
            ),
            rows,
        )

    return len(rows)


def _required_text(row, field_name):
    value = row.get(field_name)
    if _is_blank(value):
        raise ValueError(f"Required field '{field_name}' is blank.")
    return str(value)


def _optional_text(row, field_name):
    value = row.get(field_name)
    if _is_blank(value):
        return ""
    return str(value)


def _required_number(row, field_name):
    value = row.get(field_name)
    if _is_blank(value):
        raise ValueError(f"Required field '{field_name}' is blank.")
    return float(value)


def _optional_number(row, field_name, default=None):
    value = row.get(field_name)
    if _is_blank(value):
        return default
    return float(value)


def _optional_bool(row, field_name, default=False):
    value = row.get(field_name)
    if _is_blank(value):
        return default
    if isinstance(value, bool):
        return value

    text_value = str(value).strip().lower()
    if text_value in {"true", "t", "yes", "y", "1"}:
        return True
    if text_value in {"false", "f", "no", "n", "0"}:
        return False

    raise ValueError(f"Boolean field '{field_name}' has invalid value '{value}'.")


def _required_date(row, field_name):
    value = _optional_date(row, field_name)
    if value is None:
        raise ValueError(f"Required field '{field_name}' is blank.")
    return value


def _optional_date(row, field_name):
    value = row.get(field_name)
    if _is_blank(value):
        return None
    return pd.to_datetime(value).date()


def _optional_datetime(row, field_name):
    value = row.get(field_name)
    if _is_blank(value):
        return None
    return pd.to_datetime(value).to_pydatetime()


def _month_start(value):
    if _is_blank(value):
        raise ValueError("timestamp_month is required.")
    return pd.to_datetime(str(value)).date().replace(day=1)


def _is_blank(value):
    return value is None or pd.isna(value) or str(value).strip() == ""
