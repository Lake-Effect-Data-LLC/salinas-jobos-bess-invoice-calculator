import json
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
from sqlalchemy import text

from app.db import get_dataset_config_id
from app.db.writers import (
    _delete_contract_value,
    _delete_monthly_input,
    _delete_monthly_performance_guarantee,
    _delete_performance_test,
    _delete_yearly_input,
    _insert_monthly_input,
    _insert_monthly_performance_guarantee,
    _insert_performance_test,
    _insert_yearly_input,
    _update_monthly_input,
    _update_monthly_performance_guarantee,
    _update_performance_test,
    _update_yearly_input,
)


MONTHLY_INPUT_COLUMNS = [
    "timestamp_month",
    "agreement_year",
    "other_adj",
    "bphrs",
    "pohrs",
    "unavhrs",
    "unavprodhrs",
    "gse",
    "pfm",
    "ip",
    "source_reference",
    "notes",
]

MONTHLY_INPUT_NUMERIC_COLUMNS = [
    "other_adj",
    "bphrs",
    "pohrs",
    "unavhrs",
    "unavprodhrs",
    "gse",
    "pfm",
    "ip",
]

YEARLY_INPUT_COLUMNS = [
    "agreement_year",
    "dde",
    "tr",
    "gc",
    "source_reference",
    "notes",
]

YEARLY_INPUT_NUMERIC_COLUMNS = [
    "dde",
    "tr",
]

PERFORMANCE_TEST_COLUMNS = [
    "test_id",
    "agreement_year",
    "test_type",
    "test_date",
    "requested_by",
    "tde",
    "measured_ramp_rate",
    "certified_by",
    "prepa_approved",
    "approval_date",
    "cure_or_retest_date",
    "replaces_test_id",
    "ramp_failure_caused_outage",
    "outage_start",
    "outage_end",
    "outage_equivalent_unavhrs",
    "source_reference",
    "notes",
]

MONTHLY_PERFORMANCE_GUARANTEE_COLUMNS = [
    "timestamp_month",
    "agreement_year",
    "ce",
    "de",
    "ae_beg",
    "ae_end",
    "source_reference",
    "notes",
]

MONTHLY_PERFORMANCE_GUARANTEE_NUMERIC_COLUMNS = [
    "ce",
    "de",
    "ae_beg",
    "ae_end",
]

CONTRACT_VALUE_COLUMNS = [
    "agreement_year",
    "cppf",
    "cpppif",
    "ddd",
    "ta",
    "rer",
    "ge",
    "design_dmax",
    "design_duration_energy",
    "annual_duration_energy_degradation_rate",
    "design_charge_energy",
    "grid_system_waiting_period_hours",
    "force_majeure_waiting_period_hours",
    "scheduled_maintenance_allowance_hours",
    "source_reference",
    "notes",
]

CONTRACT_VALUE_NUMERIC_COLUMNS = [
    "cppf",
    "cpppif",
    "ddd",
    "ta",
    "rer",
    "ge",
    "design_dmax",
    "design_duration_energy",
    "annual_duration_energy_degradation_rate",
    "design_charge_energy",
    "grid_system_waiting_period_hours",
    "force_majeure_waiting_period_hours",
    "scheduled_maintenance_allowance_hours",
]


def save_monthly_inputs_edits(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
    allow_existing_row_changes=False,
    audit_event_id=None,
):
    return _save_table_edits(
        engine,
        project_id,
        dataset_name,
        original_df,
        edited_df,
        edit_reason,
        source,
        normalize_fn=_normalize_monthly_inputs_df,
        validate_fn=_validate_no_duplicate_months,
        table_name="monthly_inputs",
        insert_fn=_insert_monthly_input,
        update_fn=_update_monthly_input,
        delete_fn=_delete_monthly_input,
        unknown_id_label="monthly input",
        allow_existing_row_changes=allow_existing_row_changes,
        audit_event_id=audit_event_id,
    )


def save_yearly_inputs_edits(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
    allow_existing_row_changes=False,
    audit_event_id=None,
):
    return _save_table_edits(
        engine,
        project_id,
        dataset_name,
        original_df,
        edited_df,
        edit_reason,
        source,
        normalize_fn=_normalize_yearly_inputs_df,
        validate_fn=_validate_no_duplicate_agreement_years,
        table_name="yearly_inputs",
        insert_fn=_insert_yearly_input,
        update_fn=_update_yearly_input,
        delete_fn=_delete_yearly_input,
        unknown_id_label="yearly input",
        allow_existing_row_changes=allow_existing_row_changes,
        audit_event_id=audit_event_id,
    )


def save_performance_tests_edits(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
    allow_existing_row_changes=False,
    audit_event_id=None,
):
    return _save_table_edits(
        engine,
        project_id,
        dataset_name,
        original_df,
        edited_df,
        edit_reason,
        source,
        normalize_fn=_normalize_performance_tests_df,
        validate_fn=_validate_no_duplicate_test_ids,
        table_name="performance_tests",
        insert_fn=_insert_performance_test,
        update_fn=_update_performance_test,
        delete_fn=_delete_performance_test,
        unknown_id_label="performance test",
        allow_existing_row_changes=allow_existing_row_changes,
        audit_event_id=audit_event_id,
    )


def save_monthly_performance_guarantee_edits(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
    allow_existing_row_changes=False,
    audit_event_id=None,
):
    return _save_table_edits(
        engine,
        project_id,
        dataset_name,
        original_df,
        edited_df,
        edit_reason,
        source,
        normalize_fn=_normalize_monthly_performance_guarantee_df,
        validate_fn=_validate_no_duplicate_months,
        table_name="monthly_performance_guarantee",
        insert_fn=_insert_monthly_performance_guarantee,
        update_fn=_update_monthly_performance_guarantee,
        delete_fn=_delete_monthly_performance_guarantee,
        unknown_id_label="monthly performance guarantee",
        allow_existing_row_changes=allow_existing_row_changes,
        audit_event_id=audit_event_id,
    )


def save_contract_value_deletes(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
    allow_existing_row_changes=False,
    audit_event_id=None,
):
    return _save_table_edits(
        engine,
        project_id,
        dataset_name,
        original_df,
        edited_df,
        edit_reason,
        source,
        normalize_fn=_normalize_contract_values_df,
        validate_fn=_validate_no_duplicate_agreement_years,
        table_name="contract_values",
        insert_fn=None,
        update_fn=None,
        delete_fn=_delete_contract_value,
        unknown_id_label="contract value",
        allow_existing_row_changes=allow_existing_row_changes,
        allow_inserts=False,
        allow_updates=False,
        audit_event_id=audit_event_id,
    )


def _save_table_edits(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
    normalize_fn,
    validate_fn,
    table_name,
    insert_fn,
    update_fn,
    delete_fn,
    unknown_id_label,
    require_edit_metadata=False,
    allow_existing_row_changes=False,
    allow_inserts=True,
    allow_updates=True,
    audit_event_id=None,
):
    edit_reason = _optional_audit_text(edit_reason)
    source = _optional_audit_text(source)
    if require_edit_metadata:
        if edit_reason is None:
            raise ValueError("Edit reason is required before saving.")
        if source is None:
            raise ValueError("Source is required before saving.")

    original_records = normalize_fn(original_df, require_id=True)
    edited_df = _restore_existing_ids(original_df, edited_df)
    edited_records = normalize_fn(edited_df, require_id=False)
    validate_fn(edited_records)

    original_by_id = {
        str(record["id"]): record
        for record in original_records
        if record.get("id")
    }
    inserted = []
    updated = []
    edited_ids = set()

    for record in edited_records:
        row_id = record.get("id")
        if not row_id:
            inserted.append(record)
            continue

        edited_ids.add(str(row_id))
        previous_record = original_by_id.get(str(row_id))
        if previous_record is None:
            raise ValueError(f"Unknown {unknown_id_label} row id '{row_id}'.")

        comparable_previous = _without_id(previous_record)
        comparable_current = _without_id(record)
        if comparable_previous != comparable_current:
            updated.append((previous_record, record))

    deleted = [
        record
        for row_id, record in original_by_id.items()
        if row_id not in edited_ids
    ]

    if inserted and not allow_inserts:
        raise ValueError(f"New {unknown_id_label} rows are not enabled.")
    if updated and not allow_updates:
        raise ValueError(f"Editing existing {unknown_id_label} rows is not enabled.")

    existing_row_changes = updated or deleted
    if existing_row_changes and not allow_existing_row_changes:
        raise ValueError("Turn on Override Mode before editing or deleting existing rows.")
    if existing_row_changes and edit_reason is None:
        raise ValueError("An edit reason is required when Override Mode changes existing rows.")

    if not inserted and not updated and not deleted:
        return {"inserted": 0, "updated": 0, "deleted": 0}

    audit_event_id = audit_event_id or generate_audit_event_id()

    with engine.begin() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        for record in inserted:
            row_id = insert_fn(connection, dataset_config_id, record)
            new_record = {"id": str(row_id), **_without_id(record)}
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name=table_name,
                row_id=row_id,
                action="insert",
                previous_data=None,
                new_data=new_record,
                edit_reason=edit_reason,
                source=source,
                audit_event_id=audit_event_id,
            )

        for previous_record, record in updated:
            update_fn(connection, record)
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name=table_name,
                row_id=record["id"],
                action="update",
                previous_data=previous_record,
                new_data=record,
                edit_reason=edit_reason,
                source=source,
                audit_event_id=audit_event_id,
            )

        for previous_record in deleted:
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name=table_name,
                row_id=previous_record["id"],
                action="delete",
                previous_data=previous_record,
                new_data=None,
                edit_reason=edit_reason,
                source=source,
                audit_event_id=audit_event_id,
            )
            delete_fn(connection, previous_record["id"])

    return {
        "inserted": len(inserted),
        "updated": len(updated),
        "deleted": len(deleted),
        "audit_event_id": audit_event_id,
    }


def generate_audit_event_id(timestamp=None):
    timestamp = timestamp or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)
    return f"audit_event_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}"


def _insert_audit_record(
    connection,
    dataset_config_id,
    table_name,
    row_id,
    action,
    previous_data,
    new_data,
    edit_reason,
    source,
    audit_event_id,
):
    connection.execute(
        text(
            """
            INSERT INTO row_edit_history (
                dataset_config_id,
                table_name,
                row_id,
                action,
                audit_event_id,
                previous_data,
                new_data,
                edit_reason,
                source
            )
            VALUES (
                :dataset_config_id,
                :table_name,
                :row_id,
                :action,
                :audit_event_id,
                CAST(:previous_data AS jsonb),
                CAST(:new_data AS jsonb),
                :edit_reason,
                :source
            )
            """
        ),
        {
            "dataset_config_id": dataset_config_id,
            "table_name": table_name,
            "row_id": row_id,
            "action": action,
            "audit_event_id": audit_event_id,
            "previous_data": _to_json(previous_data),
            "new_data": _to_json(new_data),
            "edit_reason": edit_reason,
            "source": source,
        },
    )

def _normalize_monthly_inputs_df(df, require_id):
    records = []
    for row_index, row in df.reset_index(drop=True).iterrows():
        if _is_empty_row(row, MONTHLY_INPUT_COLUMNS):
            continue
        if not require_id and _is_incomplete_new_row(
            row,
            "id",
            ["timestamp_month", "agreement_year"],
        ):
            continue

        record = {"id": _extract_id(row, row_index, require_id)}

        record["timestamp_month"] = _month_start(row.get("timestamp_month"), row_index)
        record["agreement_year"] = _required_int(row, "agreement_year", row_index)
        for column in MONTHLY_INPUT_NUMERIC_COLUMNS:
            record[column] = _required_float(row, column, row_index)
        record["source_reference"] = _optional_text(row.get("source_reference"))
        record["notes"] = _optional_text(row.get("notes"))
        records.append(record)

    return records


def _normalize_yearly_inputs_df(df, require_id):
    records = []
    for row_index, row in df.reset_index(drop=True).iterrows():
        if _is_empty_row(row, YEARLY_INPUT_COLUMNS):
            continue
        if not require_id and _is_incomplete_new_row(row, "id", ["agreement_year"]):
            continue

        record = {"id": _extract_id(row, row_index, require_id)}

        record["agreement_year"] = _required_int(row, "agreement_year", row_index)
        for column in YEARLY_INPUT_NUMERIC_COLUMNS:
            record[column] = _required_float(row, column, row_index)
        record["gc"] = _optional_float(row.get("gc"))
        record["source_reference"] = _optional_text(row.get("source_reference"))
        record["notes"] = _optional_text(row.get("notes"))
        records.append(record)

    return records


def _normalize_performance_tests_df(df, require_id):
    records = []
    for row_index, row in df.reset_index(drop=True).iterrows():
        if _is_empty_row(row, PERFORMANCE_TEST_COLUMNS):
            continue
        if not require_id and _is_incomplete_new_row(
            row,
            "id",
            ["test_id", "agreement_year"],
        ):
            continue

        record = {"id": _extract_id(row, row_index, require_id)}

        record["test_id"] = _required_text(row, "test_id", row_index)
        record["agreement_year"] = _required_int(row, "agreement_year", row_index)
        record["test_type"] = _required_text(row, "test_type", row_index)
        record["test_date"] = _required_date_iso(row.get("test_date"), "test_date", row_index)
        record["requested_by"] = _optional_text(row.get("requested_by"))
        record["tde"] = _required_float(row, "tde", row_index)
        record["measured_ramp_rate"] = _optional_float(row.get("measured_ramp_rate"))
        record["certified_by"] = _optional_text(row.get("certified_by"))
        record["prepa_approved"] = _optional_bool(row.get("prepa_approved"))
        record["approval_date"] = _optional_date_iso(row.get("approval_date"))
        record["cure_or_retest_date"] = _optional_date_iso(row.get("cure_or_retest_date"))
        record["replaces_test_id"] = _optional_text(row.get("replaces_test_id"))
        record["ramp_failure_caused_outage"] = _optional_bool(
            row.get("ramp_failure_caused_outage")
        )
        record["outage_start"] = _optional_datetime_iso(row.get("outage_start"))
        record["outage_end"] = _optional_datetime_iso(row.get("outage_end"))
        record["outage_equivalent_unavhrs"] = _optional_float(
            row.get("outage_equivalent_unavhrs"),
            default=0.0,
        )
        record["source_reference"] = _optional_text(row.get("source_reference"))
        record["notes"] = _optional_text(row.get("notes"))
        records.append(record)

    return records


def _normalize_monthly_performance_guarantee_df(df, require_id):
    records = []
    for row_index, row in df.reset_index(drop=True).iterrows():
        if _is_empty_row(row, MONTHLY_PERFORMANCE_GUARANTEE_COLUMNS):
            continue
        if not require_id and _is_incomplete_new_row(
            row,
            "id",
            ["timestamp_month", "agreement_year"],
        ):
            continue

        record = {"id": _extract_id(row, row_index, require_id)}

        record["timestamp_month"] = _month_start(row.get("timestamp_month"), row_index)
        record["agreement_year"] = _required_int(row, "agreement_year", row_index)
        for column in MONTHLY_PERFORMANCE_GUARANTEE_NUMERIC_COLUMNS:
            record[column] = _required_float(row, column, row_index)
        record["source_reference"] = _optional_text(row.get("source_reference"))
        record["notes"] = _optional_text(row.get("notes"))
        records.append(record)

    return records


def _normalize_contract_values_df(df, require_id):
    records = []
    for row_index, row in df.reset_index(drop=True).iterrows():
        if _is_empty_row(row, CONTRACT_VALUE_COLUMNS):
            continue
        if not require_id and _is_incomplete_new_row(row, "id", ["agreement_year"]):
            continue

        record = {"id": _extract_id(row, row_index, require_id)}

        record["agreement_year"] = _required_int(row, "agreement_year", row_index)
        for column in CONTRACT_VALUE_NUMERIC_COLUMNS:
            record[column] = _required_float(row, column, row_index)
        record["source_reference"] = _optional_text(row.get("source_reference"))
        record["notes"] = _optional_text(row.get("notes"))
        records.append(record)

    return records


def _validate_no_duplicate_months(records):
    _validate_no_duplicate_keys(records, "timestamp_month", "monthly input")


def _validate_no_duplicate_agreement_years(records):
    _validate_no_duplicate_keys(records, "agreement_year", "yearly input")


def _validate_no_duplicate_test_ids(records):
    _validate_no_duplicate_keys(records, "test_id", "performance test")


def _validate_no_duplicate_keys(records, key_field, label):
    seen = set()
    for record in records:
        key = record[key_field]
        if key in seen:
            raise ValueError(f"Duplicate {label} row for {key_field} {key!r}.")
        seen.add(key)


def _is_empty_row(row, columns):
    return all(_is_blank(row.get(column)) for column in columns)


def _extract_id(row, row_index, require_id):
    row_id = row.get("id")
    if not _is_blank(row_id):
        return str(row_id)
    if require_id:
        raise ValueError(f"Existing row {row_index + 1} is missing an id.")
    return None


def _month_start(value, row_index):
    value = _cell_value(value)
    if _is_blank(value):
        raise ValueError(f"Row {row_index + 1}: timestamp_month is required.")
    try:
        parsed = pd.to_datetime(value).date().replace(day=1)
    except Exception as exc:
        raise ValueError(
            f"Row {row_index + 1}: timestamp_month must be a valid date or YYYY-MM."
        ) from exc
    return parsed.isoformat()


def _required_int(row, column, row_index):
    value = _cell_value(row.get(column))
    if _is_blank(value):
        raise ValueError(f"Row {row_index + 1}: {column} is required.")
    try:
        numeric_value = _coerce_number(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Row {row_index + 1}: {column} must be an integer "
            f"(got {value!r}, type={type(value).__name__})."
        ) from exc
    if not numeric_value.is_integer():
        raise ValueError(
            f"Row {row_index + 1}: {column} must be an integer "
            f"(got {value!r}, type={type(value).__name__})."
        )
    return int(numeric_value)


def _required_text(row, column, row_index):
    value = _cell_value(row.get(column))
    if _is_blank(value):
        raise ValueError(f"Row {row_index + 1}: {column} is required.")
    return str(value).strip()


def _required_float(row, column, row_index):
    value = _cell_value(row.get(column))
    if _is_blank(value):
        raise ValueError(f"Row {row_index + 1}: {column} is required.")
    try:
        return _coerce_number(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Row {row_index + 1}: {column} must be numeric "
            f"(got {value!r}, type={type(value).__name__})."
        ) from exc


def _optional_float(value, default=None):
    value = _cell_value(value)
    if _is_blank(value):
        return default
    try:
        return _coerce_number(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Optional numeric fields must be numeric when provided (got {value!r})."
        ) from exc


def _optional_bool(value, default=False):
    value = _cell_value(value)
    if _is_blank(value):
        return default
    if isinstance(value, bool):
        return value
    text_value = str(value).strip().lower()
    if text_value in {"true", "t", "yes", "y", "1"}:
        return True
    if text_value in {"false", "f", "no", "n", "0"}:
        return False
    raise ValueError("Boolean fields must be TRUE/FALSE, YES/NO, or 1/0.")


def _required_date_iso(value, column, row_index):
    parsed = _optional_date_iso(value)
    if parsed is None:
        raise ValueError(f"Row {row_index + 1}: {column} is required.")
    return parsed


def _optional_date_iso(value):
    value = _cell_value(value)
    if _is_blank(value):
        return None
    try:
        return pd.to_datetime(value).date().isoformat()
    except Exception as exc:
        raise ValueError("Date fields must be valid dates.") from exc


def _optional_datetime_iso(value):
    value = _cell_value(value)
    if _is_blank(value):
        return None
    try:
        return pd.to_datetime(value).to_pydatetime().isoformat()
    except Exception as exc:
        raise ValueError("Datetime fields must be valid datetimes.") from exc


def _optional_text(value):
    value = _cell_value(value)
    if _is_blank(value):
        return ""
    return str(value)


def _optional_audit_text(value):
    value = _cell_value(value)
    if _is_blank(value):
        return None
    return str(value).strip()


def _without_id(record):
    return {
        key: value
        for key, value in record.items()
        if key != "id"
    }


def _to_json(value):
    if value is None:
        return None
    return json.dumps(value, sort_keys=True)


def _restore_existing_ids(original_df, edited_df):
    restored_df = edited_df.reset_index(drop=True).copy()
    original_df = original_df.reset_index(drop=True)
    original_ids = list(original_df["id"]) if "id" in original_df else []

    if "id" not in restored_df:
        if len(restored_df) != len(original_df):
            raise ValueError(
                "Could not safely identify changed rows. Refresh the page and try again."
            )
        restored_df.insert(0, "id", None)

    for row_index, original_id in enumerate(original_ids):
        if row_index >= len(restored_df):
            break
        if _is_blank(restored_df.at[row_index, "id"]):
            restored_df.at[row_index, "id"] = original_id

    return restored_df


def _is_blank(value):
    value = _cell_value(value)
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() == ""


def _coerce_number(value):
    value = _cell_value(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        value = value.strip().replace(",", "")
    return float(value)


def _cell_value(value):
    if isinstance(value, pd.Series):
        non_blank_values = [
            item
            for item in value.tolist()
            if not _is_blank_scalar(item)
        ]
        if len(non_blank_values) == 1:
            return non_blank_values[0]
    if isinstance(value, (list, tuple)):
        non_blank_values = [
            item
            for item in value
            if not _is_blank_scalar(item)
        ]
        if len(non_blank_values) == 1:
            return non_blank_values[0]
    return value


def _is_blank_scalar(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() == ""


def _is_incomplete_new_row(row, id_column, required_columns):
    if not _is_blank(row.get(id_column)):
        return False
    return any(_is_blank(row.get(column)) for column in required_columns)
