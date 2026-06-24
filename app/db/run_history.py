import json
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import text

from app.db.datasets import get_dataset_config_id


CALCULATION_SNAPSHOT_PREFIX = "calculation_run"
CSV_EXPORT_OBJECT_TYPE = "csv_export"


def generate_calculation_snapshot_name(timestamp=None):
    timestamp = timestamp or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    normalized = timestamp.astimezone(timezone.utc)
    return f"{CALCULATION_SNAPSHOT_PREFIX}_{normalized.strftime('%Y%m%dT%H%M%S%fZ')}"


def record_calculation_run(
    engine,
    project_id,
    dataset_name,
    snapshot_month,
    snapshot_data,
    snapshot_name=None,
    csv_artifact=None,
    created_by=None,
):
    with engine.begin() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        file_object_id = None
        if csv_artifact is not None:
            file_object_id = create_csv_export_file_object(
                connection,
                project_id=project_id,
                dataset_config_id=dataset_config_id,
                **csv_artifact,
            )

        snapshot_id = create_calculation_snapshot(
            connection,
            dataset_config_id=dataset_config_id,
            snapshot_month=snapshot_month,
            snapshot_name=snapshot_name or generate_calculation_snapshot_name(),
            snapshot_data=snapshot_data,
            source_file_object_id=file_object_id,
            created_by=created_by,
        )

    return {
        "snapshot_id": snapshot_id,
        "file_object_id": file_object_id,
    }


def create_csv_export_file_object(
    connection,
    project_id,
    dataset_config_id,
    original_filename,
    storage_bucket,
    storage_key,
    content_type="text/csv",
    checksum_sha256=None,
    size_bytes=None,
    uploaded_by=None,
):
    return connection.execute(
        text(
            """
            INSERT INTO file_object (
                project_id,
                dataset_config_id,
                object_type,
                original_filename,
                content_type,
                storage_bucket,
                storage_key,
                checksum_sha256,
                size_bytes,
                uploaded_by
            )
            VALUES (
                :project_id,
                :dataset_config_id,
                :object_type,
                :original_filename,
                :content_type,
                :storage_bucket,
                :storage_key,
                :checksum_sha256,
                :size_bytes,
                :uploaded_by
            )
            RETURNING id
            """
        ),
        {
            "project_id": project_id,
            "dataset_config_id": dataset_config_id,
            "object_type": CSV_EXPORT_OBJECT_TYPE,
            "original_filename": original_filename,
            "content_type": content_type,
            "storage_bucket": storage_bucket,
            "storage_key": storage_key,
            "checksum_sha256": checksum_sha256,
            "size_bytes": size_bytes,
            "uploaded_by": uploaded_by,
        },
    ).scalar_one()


def create_calculation_snapshot(
    connection,
    dataset_config_id,
    snapshot_month,
    snapshot_name,
    snapshot_data,
    source_file_object_id=None,
    created_by=None,
):
    snapshot_data_value = _to_json(snapshot_data)
    snapshot_data_expression = _json_insert_expression(connection, "snapshot_data")
    return connection.execute(
        text(
            f"""
            INSERT INTO monthly_snapshot (
                dataset_config_id,
                snapshot_month,
                snapshot_name,
                snapshot_data,
                source_file_object_id,
                created_by
            )
            VALUES (
                :dataset_config_id,
                :snapshot_month,
                :snapshot_name,
                {snapshot_data_expression},
                :source_file_object_id,
                :created_by
            )
            RETURNING id
            """
        ),
        {
            "dataset_config_id": dataset_config_id,
            "snapshot_month": _month_start_iso(snapshot_month),
            "snapshot_name": snapshot_name,
            "snapshot_data": snapshot_data_value,
            "source_file_object_id": source_file_object_id,
            "created_by": created_by,
        },
    ).scalar_one()


def get_latest_calculation_run(engine, project_id, dataset_name):
    runs = list_latest_calculation_runs_by_month(
        engine,
        project_id=project_id,
        dataset_name=dataset_name,
        limit=1,
    )
    if not runs:
        return None
    return runs[0]


def list_latest_calculation_runs_by_month(engine, project_id, dataset_name, limit=13):
    limit = _positive_limit(limit)
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        rows = connection.execute(
            text(
                """
                WITH ranked_runs AS (
                    SELECT
                        snapshot.id AS snapshot_id,
                        snapshot.snapshot_month,
                        snapshot.snapshot_name,
                        snapshot.snapshot_data,
                        snapshot.source_file_object_id,
                        snapshot.created_at,
                        file_object.original_filename,
                        file_object.content_type,
                        file_object.storage_bucket,
                        file_object.storage_key,
                        file_object.checksum_sha256,
                        file_object.size_bytes,
                        file_object.uploaded_at,
                        row_number() OVER (
                            PARTITION BY snapshot.snapshot_month
                            ORDER BY snapshot.created_at DESC, snapshot.id DESC
                        ) AS run_rank
                    FROM monthly_snapshot snapshot
                    LEFT JOIN file_object
                        ON file_object.id = snapshot.source_file_object_id
                    WHERE snapshot.dataset_config_id = :dataset_config_id
                      AND snapshot.snapshot_name LIKE :snapshot_name_pattern
                )
                SELECT
                    snapshot_id,
                    snapshot_month,
                    snapshot_name,
                    snapshot_data,
                    source_file_object_id,
                    created_at,
                    original_filename,
                    content_type,
                    storage_bucket,
                    storage_key,
                    checksum_sha256,
                    size_bytes,
                    uploaded_at
                FROM ranked_runs
                WHERE run_rank = 1
                ORDER BY snapshot_month DESC
                LIMIT :limit
                """
            ),
            {
                "dataset_config_id": dataset_config_id,
                "snapshot_name_pattern": f"{CALCULATION_SNAPSHOT_PREFIX}%",
                "limit": limit,
            },
        ).mappings()

        return [_run_from_row(row) for row in rows]


def list_recent_calculation_runs(engine, project_id, dataset_name, limit=5):
    limit = _positive_limit(limit)
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        rows = connection.execute(
            text(
                """
                SELECT
                    snapshot.id AS snapshot_id,
                    snapshot.snapshot_month,
                    snapshot.snapshot_name,
                    snapshot.snapshot_data,
                    snapshot.source_file_object_id,
                    snapshot.created_at,
                    file_object.original_filename,
                    file_object.content_type,
                    file_object.storage_bucket,
                    file_object.storage_key,
                    file_object.checksum_sha256,
                    file_object.size_bytes,
                    file_object.uploaded_at
                FROM monthly_snapshot snapshot
                LEFT JOIN file_object
                    ON file_object.id = snapshot.source_file_object_id
                WHERE snapshot.dataset_config_id = :dataset_config_id
                  AND snapshot.snapshot_name LIKE :snapshot_name_pattern
                ORDER BY snapshot.created_at DESC, snapshot.id DESC
                LIMIT :limit
                """
            ),
            {
                "dataset_config_id": dataset_config_id,
                "snapshot_name_pattern": f"{CALCULATION_SNAPSHOT_PREFIX}%",
                "limit": limit,
            },
        ).mappings()

        return [_run_from_row(row) for row in rows]


def get_file_object(engine, file_object_id):
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    id,
                    project_id,
                    dataset_config_id,
                    object_type,
                    original_filename,
                    content_type,
                    storage_bucket,
                    storage_key,
                    checksum_sha256,
                    size_bytes,
                    uploaded_at
                FROM file_object
                WHERE id = :file_object_id
                """
            ),
            {"file_object_id": file_object_id},
        ).mappings().one_or_none()

    if row is None:
        return None
    return dict(row)


def _run_from_row(row):
    return {
        "snapshot_id": row["snapshot_id"],
        "snapshot_month": _date_iso(row["snapshot_month"]),
        "snapshot_name": row["snapshot_name"],
        "snapshot_data": _from_json(row["snapshot_data"]),
        "source_file_object_id": row["source_file_object_id"],
        "created_at": row["created_at"],
        "csv_artifact": _csv_artifact_from_row(row),
    }


def _csv_artifact_from_row(row):
    if row["source_file_object_id"] is None:
        return None
    return {
        "file_object_id": row["source_file_object_id"],
        "original_filename": row["original_filename"],
        "content_type": row["content_type"],
        "storage_bucket": row["storage_bucket"],
        "storage_key": row["storage_key"],
        "checksum_sha256": row["checksum_sha256"],
        "size_bytes": row["size_bytes"],
        "uploaded_at": row["uploaded_at"],
    }


def _positive_limit(limit):
    try:
        parsed_limit = int(limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("Run history limit must be a positive integer.") from exc
    if parsed_limit < 1:
        raise ValueError("Run history limit must be a positive integer.")
    return parsed_limit


def _json_insert_expression(connection, bind_name):
    if connection.dialect.name == "postgresql":
        return f"CAST(:{bind_name} AS jsonb)"
    return f":{bind_name}"


def _to_json(value):
    return json.dumps(value, sort_keys=True, default=_json_default)


def _from_json(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


def _json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def _date_iso(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _month_start_iso(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().replace(day=1).isoformat()
    if isinstance(value, date):
        return value.replace(day=1).isoformat()

    text_value = str(value).strip()
    if len(text_value) == 7:
        text_value = f"{text_value}-01"

    try:
        return date.fromisoformat(text_value).replace(day=1).isoformat()
    except ValueError as exc:
        raise ValueError(
            f"Snapshot month must be a valid date or YYYY-MM value, got {value!r}."
        ) from exc
