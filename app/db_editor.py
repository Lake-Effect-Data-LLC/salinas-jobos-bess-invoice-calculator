import json
from decimal import Decimal

import pandas as pd
from sqlalchemy import text

from app.db import get_dataset_config_id


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


def save_monthly_inputs_edits(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
):
    if not edit_reason.strip():
        raise ValueError("Edit reason is required before saving.")
    if not source.strip():
        raise ValueError("Source is required before saving.")

    original_records = _normalize_monthly_inputs_df(original_df, require_id=True)
    edited_df = _restore_existing_ids(original_df, edited_df)
    edited_records = _normalize_monthly_inputs_df(edited_df, require_id=False)
    _validate_no_duplicate_months(edited_records)

    original_by_id = {
        str(record["id"]): record
        for record in original_records
        if record.get("id")
    }
    inserted = []
    updated = []

    for record in edited_records:
        row_id = record.get("id")
        if not row_id:
            inserted.append(record)
            continue

        previous_record = original_by_id.get(str(row_id))
        if previous_record is None:
            raise ValueError(f"Unknown monthly input row id '{row_id}'.")

        comparable_previous = _without_id(previous_record)
        comparable_current = _without_id(record)
        if comparable_previous != comparable_current:
            updated.append((previous_record, record))

    if not inserted and not updated:
        return {"inserted": 0, "updated": 0}

    with engine.begin() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        for record in inserted:
            row_id = _insert_monthly_input(connection, dataset_config_id, record)
            new_record = {"id": str(row_id), **_without_id(record)}
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name="monthly_inputs",
                row_id=row_id,
                action="insert",
                previous_data=None,
                new_data=new_record,
                edit_reason=edit_reason,
                source=source,
            )

        for previous_record, record in updated:
            _update_monthly_input(connection, record)
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name="monthly_inputs",
                row_id=record["id"],
                action="update",
                previous_data=previous_record,
                new_data=record,
                edit_reason=edit_reason,
                source=source,
            )

    return {"inserted": len(inserted), "updated": len(updated)}


def save_yearly_inputs_edits(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
):
    if not edit_reason.strip():
        raise ValueError("Edit reason is required before saving.")
    if not source.strip():
        raise ValueError("Source is required before saving.")

    original_records = _normalize_yearly_inputs_df(original_df, require_id=True)
    edited_df = _restore_existing_ids(original_df, edited_df)
    edited_records = _normalize_yearly_inputs_df(edited_df, require_id=False)
    _validate_no_duplicate_agreement_years(edited_records)

    original_by_id = {
        str(record["id"]): record
        for record in original_records
        if record.get("id")
    }
    inserted = []
    updated = []

    for record in edited_records:
        row_id = record.get("id")
        if not row_id:
            inserted.append(record)
            continue

        previous_record = original_by_id.get(str(row_id))
        if previous_record is None:
            raise ValueError(f"Unknown yearly input row id '{row_id}'.")

        comparable_previous = _without_id(previous_record)
        comparable_current = _without_id(record)
        if comparable_previous != comparable_current:
            updated.append((previous_record, record))

    if not inserted and not updated:
        return {"inserted": 0, "updated": 0}

    with engine.begin() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        for record in inserted:
            row_id = _insert_yearly_input(connection, dataset_config_id, record)
            new_record = {"id": str(row_id), **_without_id(record)}
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name="yearly_inputs",
                row_id=row_id,
                action="insert",
                previous_data=None,
                new_data=new_record,
                edit_reason=edit_reason,
                source=source,
            )

        for previous_record, record in updated:
            _update_yearly_input(connection, record)
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name="yearly_inputs",
                row_id=record["id"],
                action="update",
                previous_data=previous_record,
                new_data=record,
                edit_reason=edit_reason,
                source=source,
            )

    return {"inserted": len(inserted), "updated": len(updated)}


def save_performance_tests_edits(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
):
    if not edit_reason.strip():
        raise ValueError("Edit reason is required before saving.")
    if not source.strip():
        raise ValueError("Source is required before saving.")

    original_records = _normalize_performance_tests_df(original_df, require_id=True)
    edited_df = _restore_existing_ids(original_df, edited_df)
    edited_records = _normalize_performance_tests_df(edited_df, require_id=False)
    _validate_no_duplicate_test_ids(edited_records)

    original_by_id = {
        str(record["id"]): record
        for record in original_records
        if record.get("id")
    }
    inserted = []
    updated = []

    for record in edited_records:
        row_id = record.get("id")
        if not row_id:
            inserted.append(record)
            continue

        previous_record = original_by_id.get(str(row_id))
        if previous_record is None:
            raise ValueError(f"Unknown performance test row id '{row_id}'.")

        comparable_previous = _without_id(previous_record)
        comparable_current = _without_id(record)
        if comparable_previous != comparable_current:
            updated.append((previous_record, record))

    if not inserted and not updated:
        return {"inserted": 0, "updated": 0}

    with engine.begin() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        for record in inserted:
            row_id = _insert_performance_test(connection, dataset_config_id, record)
            new_record = {"id": str(row_id), **_without_id(record)}
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name="performance_tests",
                row_id=row_id,
                action="insert",
                previous_data=None,
                new_data=new_record,
                edit_reason=edit_reason,
                source=source,
            )

        for previous_record, record in updated:
            _update_performance_test(connection, record)
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name="performance_tests",
                row_id=record["id"],
                action="update",
                previous_data=previous_record,
                new_data=record,
                edit_reason=edit_reason,
                source=source,
            )

    return {"inserted": len(inserted), "updated": len(updated)}


def save_monthly_performance_guarantee_edits(
    engine,
    project_id,
    dataset_name,
    original_df,
    edited_df,
    edit_reason,
    source,
):
    if not edit_reason.strip():
        raise ValueError("Edit reason is required before saving.")
    if not source.strip():
        raise ValueError("Source is required before saving.")

    original_records = _normalize_monthly_performance_guarantee_df(
        original_df,
        require_id=True,
    )
    edited_df = _restore_existing_ids(original_df, edited_df)
    edited_records = _normalize_monthly_performance_guarantee_df(
        edited_df,
        require_id=False,
    )
    _validate_no_duplicate_months(edited_records)

    original_by_id = {
        str(record["id"]): record
        for record in original_records
        if record.get("id")
    }
    inserted = []
    updated = []

    for record in edited_records:
        row_id = record.get("id")
        if not row_id:
            inserted.append(record)
            continue

        previous_record = original_by_id.get(str(row_id))
        if previous_record is None:
            raise ValueError(f"Unknown monthly performance guarantee row id '{row_id}'.")

        comparable_previous = _without_id(previous_record)
        comparable_current = _without_id(record)
        if comparable_previous != comparable_current:
            updated.append((previous_record, record))

    if not inserted and not updated:
        return {"inserted": 0, "updated": 0}

    with engine.begin() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        for record in inserted:
            row_id = _insert_monthly_performance_guarantee(
                connection,
                dataset_config_id,
                record,
            )
            new_record = {"id": str(row_id), **_without_id(record)}
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name="monthly_performance_guarantee",
                row_id=row_id,
                action="insert",
                previous_data=None,
                new_data=new_record,
                edit_reason=edit_reason,
                source=source,
            )

        for previous_record, record in updated:
            _update_monthly_performance_guarantee(connection, record)
            _insert_audit_record(
                connection,
                dataset_config_id,
                table_name="monthly_performance_guarantee",
                row_id=record["id"],
                action="update",
                previous_data=previous_record,
                new_data=record,
                edit_reason=edit_reason,
                source=source,
            )

    return {"inserted": len(inserted), "updated": len(updated)}


def _insert_monthly_performance_guarantee(connection, dataset_config_id, record):
    return connection.execute(
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
            RETURNING id
            """
        ),
        {"dataset_config_id": dataset_config_id, **_without_id(record)},
    ).scalar_one()


def _update_monthly_performance_guarantee(connection, record):
    connection.execute(
        text(
            """
            UPDATE monthly_performance_guarantee
            SET timestamp_month = :timestamp_month,
                agreement_year = :agreement_year,
                ce = :ce,
                de = :de,
                ae_beg = :ae_beg,
                ae_end = :ae_end,
                source_reference = :source_reference,
                notes = :notes,
                updated_at = now()
            WHERE id = :id
            """
        ),
        record,
    )


def _insert_performance_test(connection, dataset_config_id, record):
    return connection.execute(
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
            RETURNING id
            """
        ),
        {"dataset_config_id": dataset_config_id, **_without_id(record)},
    ).scalar_one()


def _update_performance_test(connection, record):
    connection.execute(
        text(
            """
            UPDATE performance_tests
            SET test_id = :test_id,
                agreement_year = :agreement_year,
                test_type = :test_type,
                test_date = :test_date,
                requested_by = :requested_by,
                tde = :tde,
                measured_ramp_rate = :measured_ramp_rate,
                certified_by = :certified_by,
                prepa_approved = :prepa_approved,
                approval_date = :approval_date,
                cure_or_retest_date = :cure_or_retest_date,
                replaces_test_id = :replaces_test_id,
                ramp_failure_caused_outage = :ramp_failure_caused_outage,
                outage_start = :outage_start,
                outage_end = :outage_end,
                outage_equivalent_unavhrs = :outage_equivalent_unavhrs,
                source_reference = :source_reference,
                notes = :notes,
                updated_at = now()
            WHERE id = :id
            """
        ),
        record,
    )


def _insert_yearly_input(connection, dataset_config_id, record):
    return connection.execute(
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
            RETURNING id
            """
        ),
        {"dataset_config_id": dataset_config_id, **_without_id(record)},
    ).scalar_one()


def _update_yearly_input(connection, record):
    connection.execute(
        text(
            """
            UPDATE yearly_inputs
            SET agreement_year = :agreement_year,
                dde = :dde,
                tr = :tr,
                gc = :gc,
                source_reference = :source_reference,
                notes = :notes,
                updated_at = now()
            WHERE id = :id
            """
        ),
        record,
    )


def _insert_monthly_input(connection, dataset_config_id, record):
    return connection.execute(
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
            RETURNING id
            """
        ),
        {"dataset_config_id": dataset_config_id, **_without_id(record)},
    ).scalar_one()


def _update_monthly_input(connection, record):
    connection.execute(
        text(
            """
            UPDATE monthly_inputs
            SET timestamp_month = :timestamp_month,
                agreement_year = :agreement_year,
                other_adj = :other_adj,
                bphrs = :bphrs,
                pohrs = :pohrs,
                unavhrs = :unavhrs,
                unavprodhrs = :unavprodhrs,
                gse = :gse,
                pfm = :pfm,
                ip = :ip,
                source_reference = :source_reference,
                notes = :notes,
                updated_at = now()
            WHERE id = :id
            """
        ),
        record,
    )


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
):
    connection.execute(
        text(
            """
            INSERT INTO row_edit_history (
                dataset_config_id,
                table_name,
                row_id,
                action,
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
            "previous_data": _to_json(previous_data),
            "new_data": _to_json(new_data),
            "edit_reason": edit_reason,
            "source": source,
        },
    )


def _normalize_monthly_inputs_df(df, require_id):
    records = []
    for row_index, row in df.reset_index(drop=True).iterrows():
        if _is_empty_row(row):
            continue
        if not require_id and _is_incomplete_new_row(
            row,
            "id",
            ["timestamp_month", "agreement_year"],
        ):
            continue

        record = {}
        row_id = row.get("id")
        if not _is_blank(row_id):
            record["id"] = str(row_id)
        elif require_id:
            raise ValueError(f"Existing row {row_index + 1} is missing an id.")
        else:
            record["id"] = None

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
        if _is_empty_yearly_row(row):
            continue
        if not require_id and _is_incomplete_new_row(row, "id", ["agreement_year"]):
            continue

        record = {}
        row_id = row.get("id")
        if not _is_blank(row_id):
            record["id"] = str(row_id)
        elif require_id:
            raise ValueError(f"Existing row {row_index + 1} is missing an id.")
        else:
            record["id"] = None

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
        if _is_empty_performance_test_row(row):
            continue
        if not require_id and _is_incomplete_new_row(
            row,
            "id",
            ["test_id", "agreement_year"],
        ):
            continue

        record = {}
        row_id = row.get("id")
        if not _is_blank(row_id):
            record["id"] = str(row_id)
        elif require_id:
            raise ValueError(f"Existing row {row_index + 1} is missing an id.")
        else:
            record["id"] = None

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
        if _is_empty_monthly_performance_guarantee_row(row):
            continue
        if not require_id and _is_incomplete_new_row(
            row,
            "id",
            ["timestamp_month", "agreement_year"],
        ):
            continue

        record = {}
        row_id = row.get("id")
        if not _is_blank(row_id):
            record["id"] = str(row_id)
        elif require_id:
            raise ValueError(f"Existing row {row_index + 1} is missing an id.")
        else:
            record["id"] = None

        record["timestamp_month"] = _month_start(row.get("timestamp_month"), row_index)
        record["agreement_year"] = _required_int(row, "agreement_year", row_index)
        for column in MONTHLY_PERFORMANCE_GUARANTEE_NUMERIC_COLUMNS:
            record[column] = _required_float(row, column, row_index)
        record["source_reference"] = _optional_text(row.get("source_reference"))
        record["notes"] = _optional_text(row.get("notes"))
        records.append(record)

    return records


def _validate_no_duplicate_months(records):
    seen = set()
    for record in records:
        key = record["timestamp_month"]
        if key in seen:
            raise ValueError(f"Duplicate monthly input row for {key}.")
        seen.add(key)


def _validate_no_duplicate_agreement_years(records):
    seen = set()
    for record in records:
        key = record["agreement_year"]
        if key in seen:
            raise ValueError(f"Duplicate yearly input row for agreement year {key}.")
        seen.add(key)


def _validate_no_duplicate_test_ids(records):
    seen = set()
    for record in records:
        key = record["test_id"]
        if key in seen:
            raise ValueError(f"Duplicate performance test row for test_id {key}.")
        seen.add(key)


def _is_empty_row(row):
    return all(_is_blank(row.get(column)) for column in MONTHLY_INPUT_COLUMNS)


def _is_empty_yearly_row(row):
    return all(_is_blank(row.get(column)) for column in YEARLY_INPUT_COLUMNS)


def _is_empty_performance_test_row(row):
    return all(_is_blank(row.get(column)) for column in PERFORMANCE_TEST_COLUMNS)


def _is_empty_monthly_performance_guarantee_row(row):
    return all(
        _is_blank(row.get(column))
        for column in MONTHLY_PERFORMANCE_GUARANTEE_COLUMNS
    )


def _month_start(value, row_index):
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
    value = row.get(column)
    if _is_blank(value):
        raise ValueError(f"Row {row_index + 1}: {column} is required.")
    try:
        numeric_value = _coerce_number(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Row {row_index + 1}: {column} must be an integer "
            f"(got {value!r})."
        ) from exc
    if not numeric_value.is_integer():
        raise ValueError(
            f"Row {row_index + 1}: {column} must be an integer "
            f"(got {value!r})."
        )
    return int(numeric_value)


def _required_text(row, column, row_index):
    value = row.get(column)
    if _is_blank(value):
        raise ValueError(f"Row {row_index + 1}: {column} is required.")
    return str(value).strip()


def _required_float(row, column, row_index):
    value = row.get(column)
    if _is_blank(value):
        raise ValueError(f"Row {row_index + 1}: {column} is required.")
    try:
        return _coerce_number(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Row {row_index + 1}: {column} must be numeric "
            f"(got {value!r})."
        ) from exc


def _optional_float(value, default=None):
    if _is_blank(value):
        return default
    try:
        return _coerce_number(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Optional numeric fields must be numeric when provided (got {value!r})."
        ) from exc


def _optional_bool(value, default=False):
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
    if _is_blank(value):
        return None
    try:
        return pd.to_datetime(value).date().isoformat()
    except Exception as exc:
        raise ValueError("Date fields must be valid dates.") from exc


def _optional_datetime_iso(value):
    if _is_blank(value):
        return None
    try:
        return pd.to_datetime(value).to_pydatetime().isoformat()
    except Exception as exc:
        raise ValueError("Datetime fields must be valid datetimes.") from exc


def _optional_text(value):
    if _is_blank(value):
        return ""
    return str(value)


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
        restored_df.insert(0, "id", None)

    for row_index, original_id in enumerate(original_ids):
        if row_index >= len(restored_df):
            break
        if _is_blank(restored_df.at[row_index, "id"]):
            restored_df.at[row_index, "id"] = original_id

    return restored_df


def _is_blank(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() == ""


def _coerce_number(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        value = value.strip().replace(",", "")
    return float(value)


def _is_incomplete_new_row(row, id_column, required_columns):
    if not _is_blank(row.get(id_column)):
        return False
    return any(_is_blank(row.get(column)) for column in required_columns)
