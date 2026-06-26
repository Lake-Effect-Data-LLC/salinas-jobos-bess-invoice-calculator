# Audit Event Linked MinIO Artifacts

## Original Request

Yeah, I think you understand the goal and have developed a good plan, let's give her a try! Plan
Create one audit_event_id per save
Every successful input-table save should generate one ID.
Example: audit_event_20260626T143022123456Z
This ID represents the save action, not an individual row.

Store audit_event_id in row_edit_history
Add a nullable audit_event_id text column to row_edit_history.
Every row-level insert/update/delete caused by that save gets the same audit_event_id.
So if one save deletes 3 rows, all 3 audit rows are grouped together.

Use the same audit_event_id in MinIO object names
Instead of only:scenario_state/salinas/actual/scenario_state_20260626T143022.csv

Use:scenario_state/salinas/actual/audit_event_20260626T143022123456Z.csv
scenario_state/salinas/actual/audit_event_20260626T143022123456Z.json

Put the same ID inside the MinIO files
CSV top section:SECTION,change_summary
audit_event_id,audit_event_20260626T143022123456Z
table_name,monthly_inputs
updated,1
deleted,0
edit_reason,Corrected suspicious input

JSON:{
  "audit_event_id": "...",
  "change_context": {...},
  "inputs": {...}
}

Optionally add MinIO references back into DB
Best version: add columns to row_edit_history:artifact_bucket
artifact_csv_key
artifact_json_key

Then DBeaver can show the exact MinIO file for that edit.
This avoids guessing which file matches which DB audit row.

Add an audit review UI later
A simple "Audit History" section in Streamlit could show:timestamp
table changed
action counts
edit reason
download CSV snapshot
download JSON snapshot

That would let you review suspicious changes without opening DBeaver.

## Plan

Implement the audit-linking portion now and leave the future Audit History UI as documented follow-up.

1. Add schema support for `audit_event_id` and MinIO artifact references on `row_edit_history`.
2. Generate one audit event ID per successful input-table save and pass it through all row audit inserts for that save.
3. Use the same audit event ID as the scenario-state CSV/JSON artifact name in MinIO.
4. Write the audit event ID into both scenario-state CSV and JSON payloads.
5. After MinIO upload succeeds, update all audit rows for that event with the exact bucket/key references.
6. Add/update focused tests for audit IDs, artifact payloads, and artifact reference updates.
7. Update feature documentation to describe how DB audit rows and MinIO snapshots are linked.

---

## Feature Changes

- Input-table saves now produce a single `audit_event_id` for the save action.
- Every row-level audit record created by that save stores the same `audit_event_id`, so multi-row edits/deletes can be reviewed as one event.
- Scenario-state MinIO exports now use the audit event ID as the file name for both CSV and JSON artifacts.
- Scenario-state CSV and JSON payloads include the audit event ID alongside the changed table, change counts, edit reason, and full five-table input snapshot.
- After a successful MinIO upload, `row_edit_history` rows for that event are updated with the artifact bucket, CSV key, and JSON key.

---

## Files Changed

- `app/services/table_editor.py`
  - Added `generate_audit_event_id()`.
  - Added optional `audit_event_id` parameters to table save functions.
  - Writes `audit_event_id` into each `row_edit_history` insert.

- `app/components/db_tables.py`
  - Generates an audit event ID before each save.
  - Includes the saved event ID in the post-save scenario-state callback.

- `app/streamlit_app.py`
  - Uses the audit event ID as the scenario-state artifact name.
  - Updates matching audit rows with MinIO artifact references after upload.

- `app/db/audit.py` and `app/db/__init__.py`
  - Added `update_audit_event_artifacts()` for linking audit rows to MinIO object keys.

- `app/artifacts.py`
  - Includes `audit_event_id` in scenario-state JSON artifacts and normalized change context.

- `app/components/results.py`
  - Includes `audit_event_id` in the scenario-state CSV change summary.

- `docker/postgres/init/001_app_schema.sql`
  - Added fresh-schema columns for audit event grouping and artifact references.

- `docker/postgres/init/004_audit_event_artifact_links.sql`
  - Added additive migration for existing databases.

- `tests/test_table_editor_normalization.py`
  - Verifies row audit records receive the expected audit event ID.

- `tests/test_artifacts.py`
  - Verifies scenario-state JSON stores the audit event ID.

- `tests/test_results_snapshot.py`
  - Verifies scenario-state CSV change summary stores the audit event ID.

- `tests/test_audit_artifacts.py`
  - Verifies audit rows are updated with artifact references by event ID.

---

## Summary And Concerns

This change closes the reviewability gap between Postgres audit rows and MinIO scenario snapshots. A suspicious edit can now be traced from `row_edit_history.audit_event_id` directly to the exact CSV/JSON snapshot generated after that save.

The MinIO link-back remains intentionally best-effort: if MinIO upload fails, the DB save and row audit still succeed, but artifact reference columns stay null. The planned Audit History UI is still not implemented; review currently happens through DBeaver plus MinIO links stored in the audit table.

Existing databases need the additive migration in `docker/postgres/init/004_audit_event_artifact_links.sql` applied once. The local shell could not run it because the `docker` command was unavailable in this environment.

Verification:

- `.\.venv\Scripts\python.exe -m py_compile app\services\table_editor.py app\components\db_tables.py app\streamlit_app.py app\artifacts.py app\components\results.py app\db\audit.py`
- `.\.venv\Scripts\python.exe -m unittest tests.test_table_editor_normalization tests.test_artifacts tests.test_results_snapshot tests.test_audit_artifacts`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests`
