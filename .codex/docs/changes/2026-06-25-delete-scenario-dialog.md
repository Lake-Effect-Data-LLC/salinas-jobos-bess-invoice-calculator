# Request

1. The UI Element: Add a ' Delete Scenario' button in the sidebar right below the Scenario dropdown. This button should be available for all scenarios.
2. Confirmation Modal: Because this is highly destructive, clicking the delete button must pop up a confirmation dialog (e.g., using Streamlit's @st.dialog decorator). The dialog should warn them: 'Are you sure? This will permanently delete the entire scenario and all of its associated inputs and past runs from the database.'
3. Safe Deletion & Rerun: If they confirm:
- Execute the database deletion. Please ensure your SQL handles cascading deletes so that all child records (inputs, runs, etc.) are actually removed from the database and no orphaned rows are left behind.
- Reset the session state to point to a safe default scenario (or refresh the scenario list and pick the first available one).
- Trigger an st.rerun() to update the UI.
Please outline the SQL cascading delete logic you plan to use, and show me the Streamlit code for the sidebar button and confirmation modal.

---

## Plan

1. Add a database helper that deletes a scenario by `project_id` + scenario name.
2. Delete scenario-owned `file_object` rows first because that table uses `ON DELETE SET NULL` rather than cascading from `dataset_config`.
3. Delete the `dataset_config` row and rely on existing `ON DELETE CASCADE` constraints for input rows, snapshots, edit history, and validation rows.
4. Return the next available scenario name for the same facility after deletion.
5. Add a sidebar `Delete Scenario` button below the Scenario dropdown for real selected scenarios.
6. Add a native Streamlit confirmation dialog using `@st.dialog`.
7. On confirmed deletion, reset selected scenario session state/query param target and rerun.
8. Add focused tests for deletion behavior and next-scenario selection.

---

## SQL Strategy

The deletion helper will use:

```sql
DELETE FROM file_object
WHERE dataset_config_id = :dataset_config_id;

DELETE FROM dataset_config
WHERE id = :dataset_config_id
  AND project_id = :project_id;
```

`dataset_config` child tables already reference it with `ON DELETE CASCADE` for scenario-owned data such as inputs, monthly snapshots, row edit history, and validation results. `file_object` is explicitly deleted first because its schema is intentionally `ON DELETE SET NULL`.

---

## Feature Changes

- Added a sidebar `Delete Scenario` action for selected scenarios.
- Added a native Streamlit confirmation dialog for permanent scenario deletion.
- Added database deletion logic that removes scenario-owned file metadata and deletes the scenario row so child data cascades.
- After deletion, the app selects the next safe scenario when one exists and reruns.

---

## Files Changed

- `app/db/datasets.py`
  - Added `delete_dataset_config(...)`.
  - Deletes `file_object` rows for the scenario first, then deletes the `dataset_config` row.
  - Returns the next default/first available scenario name for the same project.

- `app/db/__init__.py`
  - Exported `delete_dataset_config`.

- `app/streamlit_app.py`
  - Added the sidebar `Delete Scenario` button below the Scenario dropdown.
  - Added `render_delete_scenario_dialog(...)` with the destructive warning and confirm/cancel buttons.
  - Resets selected scenario state/query params and reruns after deletion.

- `tests/test_dataset_creation.py`
  - Added test coverage for scenario deletion, file-object cleanup, child-row cascade behavior, and next-scenario selection.

- `.codex/docs/features/dataset-scenarios.md`
  - Documented scenario deletion behavior and SQL strategy.

---

## Summary And Concerns

Scenario deletion is now routed through one database helper and one Streamlit confirmation dialog. The deletion path removes `file_object` rows explicitly because they are `ON DELETE SET NULL`, then deletes `dataset_config` so Postgres cascades scenario-owned rows such as inputs, snapshots, row edit history, and validation results.

Verification:

- `.\.venv\Scripts\python.exe -m py_compile app\db\datasets.py app\db\__init__.py app\streamlit_app.py tests\test_dataset_creation.py`
- `.\.venv\Scripts\python.exe -m unittest tests.test_dataset_creation`
- `.\.venv\Scripts\python.exe -m unittest discover tests`
- Local Streamlit server returned HTTP 200 at `http://localhost:8503`.

Concern:

- This deletes database metadata for file objects, but it does not delete remote object-storage blobs. MinIO/object storage is intentionally not wired into the runtime yet.
