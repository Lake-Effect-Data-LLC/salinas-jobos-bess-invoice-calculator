ALTER TABLE row_edit_history
    ADD COLUMN IF NOT EXISTS audit_event_id text,
    ADD COLUMN IF NOT EXISTS artifact_bucket text,
    ADD COLUMN IF NOT EXISTS artifact_csv_key text,
    ADD COLUMN IF NOT EXISTS artifact_json_key text;

CREATE INDEX IF NOT EXISTS idx_row_edit_history_audit_event_id
    ON row_edit_history(audit_event_id);
