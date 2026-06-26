from sqlalchemy import text


def update_audit_event_artifacts(
    engine,
    audit_event_id,
    artifact_bucket,
    artifact_csv_key,
    artifact_json_key,
):
    if not audit_event_id:
        return 0

    with engine.begin() as connection:
        result = connection.execute(
            text(
                """
                UPDATE row_edit_history
                SET artifact_bucket = :artifact_bucket,
                    artifact_csv_key = :artifact_csv_key,
                    artifact_json_key = :artifact_json_key
                WHERE audit_event_id = :audit_event_id
                """
            ),
            {
                "audit_event_id": audit_event_id,
                "artifact_bucket": artifact_bucket,
                "artifact_csv_key": artifact_csv_key,
                "artifact_json_key": artifact_json_key,
            },
        )
    return result.rowcount or 0
