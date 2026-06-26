import json
from datetime import datetime, timezone


def build_scenario_state_artifact(
    project_id,
    dataset_name,
    inputs,
    change_context=None,
    exported_at=None,
):
    artifact = {
        "artifact_type": "scenario_state",
        "audit_event_id": (change_context or {}).get("audit_event_id"),
        "project_id": project_id,
        "dataset_name": dataset_name,
        "exported_at": _utc_timestamp(exported_at),
        "inputs": inputs,
    }
    if change_context:
        artifact["change_context"] = _normalize_change_context(change_context)
    return artifact


def build_calculation_package_artifact(
    project_id,
    dataset_name,
    snapshot_month,
    snapshot_name,
    snapshot_data,
    exported_at=None,
):
    return {
        "artifact_type": "calculation_package",
        "project_id": project_id,
        "dataset_name": dataset_name,
        "snapshot_month": snapshot_month,
        "snapshot_name": snapshot_name,
        "exported_at": _utc_timestamp(exported_at),
        "latest_month_summary": snapshot_data.get("latest_month_summary"),
        "csv_text": snapshot_data.get("csv_text"),
        "report_text": snapshot_data.get("report_text"),
        "inputs": snapshot_data.get("inputs", {}),
    }


def artifact_to_json_bytes(artifact):
    return json.dumps(
        artifact,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")


def _utc_timestamp(value=None):
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _normalize_change_context(change_context):
    return {
        "audit_event_id": change_context.get("audit_event_id"),
        "table_name": change_context.get("table_name"),
        "change_result": {
            "inserted": _count_value(change_context, "inserted"),
            "updated": _count_value(change_context, "updated"),
            "deleted": _count_value(change_context, "deleted"),
        },
        "edit_reason": change_context.get("edit_reason"),
    }


def _count_value(change_context, key):
    result = change_context.get("change_result") or {}
    return int(result.get(key, 0) or 0)
