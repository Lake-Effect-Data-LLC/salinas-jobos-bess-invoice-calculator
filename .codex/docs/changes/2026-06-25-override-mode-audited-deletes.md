# Request

I trust this. Yes. I’d scope delete buttons very narrowly.
Delete Button Extent
Default state, Override OFF:
Contract values: no delete button / delete unavailable
Yearly inputs: no delete button / delete unavailable
Monthly inputs: no delete button / delete unavailable
Monthly performance guarantee: no delete button / delete unavailable
Performance tests: no delete button / delete unavailable
Override ON:
Contract values: delete allowed, but only with required edit reason
Yearly inputs: delete allowed, but only with required edit reason
Monthly inputs: delete allowed, but only with required edit reason
Monthly performance guarantee: delete allowed, but only with required edit reason
Performance tests: delete allowed, but only with required edit reason
If you specifically mean contract values should be delete-only in Override Mode, then the safest table behavior is:
Contract values, Override OFF:
read-only
no insert
no edit
no delete

Contract values, Override ON:
allow delete
maybe still block edits unless we explicitly decide contract edits are allowed
require edit reason/source
full audit log required

For the other input tables, I’d keep the same principle:
normal mode: add new rows only
override mode: edit/delete existing rows
So the delete rule is simple: delete never exists outside Override Mode, anywhere. Contract values just get the strictest version of that rule because they are reference data.

---

## Plan

Implement Override Mode as a guarded editing workflow:

1. Add an Override Mode control above the input tables.
2. Keep normal mode insert-only for non-contract input tables.
3. Keep contract values read-only in normal mode.
4. In Override Mode, allow existing-row updates/deletes for non-contract tables and delete-only behavior for contract values if the current UI can support it without schema churn.
5. Require an edit reason for updates/deletes.
6. Enforce update/delete protection in backend save logic, not only in the Streamlit UI.
7. Write update/delete audit rows to `row_edit_history` in the same transaction as data changes.
8. Add tests for insert-only normal mode, update/delete rejection without override, and audited update/delete with override.

---

## Feature Changes

- Added Override Mode as the only path for editing or deleting existing database rows.
- Normal mode now displays existing non-contract rows as locked/read-only and provides a separate new-row editor for additions.
- Contract values are read-only in normal mode and delete-only in Override Mode.
- Existing-row updates/deletes require both an override editor and an edit reason.
- Existing-row updates/deletes are audited in `row_edit_history` before the data change is committed.

---

## Files Changed

- `app/components/db_tables.py`
  - Added the Override Mode toggle, override editor field, and override edit reason field.
  - Split normal-mode table behavior into read-only existing rows plus a new-row entry editor.
  - Added contract-values delete-only override behavior.
  - Preserved column tooltips and the `Column Guide` expander.

- `app/services/table_editor.py`
  - Extended save coordination to classify inserts, updates, and deletes.
  - Enforced backend protection: update/delete requires Override Mode, override editor, and edit reason.
  - Added contract-value normalization and delete-only save handling.
  - Added a row-ID safety check when Streamlit does not return IDs during row count changes.

- `app/db/writers.py`
  - Added delete writer functions for the five input tables.

- `tests/test_table_editor_normalization.py`
  - Added focused tests for update/delete rejection, override reason requirements, audited update/delete behavior, and contract-value delete-only behavior.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the new guarded editing/deleting behavior.

---

## Summary And Concerns

Override Mode now gates all existing-row edits and deletes. Normal users can add rows without turning on Override Mode, but existing data is presented read-only. When Override Mode is on, update/delete saves require an override editor and an edit reason, and the backend enforces those requirements regardless of the Streamlit UI state.

Verification:

- `.\.venv\Scripts\python.exe -m py_compile app\components\db_tables.py app\services\table_editor.py app\db\writers.py tests\test_table_editor_normalization.py`
- `.\.venv\Scripts\python.exe -m unittest tests.test_table_editor_normalization`
- `.\.venv\Scripts\python.exe -m unittest discover tests`
- Local Streamlit server responded with HTTP 200 at `http://localhost:8503`.

Concern:

- The app does not yet have authenticated user identity wired into the runtime, so the override editor is stored in `row_edit_history.source`. The schema-level `edited_by` field remains nullable until real user identity is implemented.
