# User Request And Plan

> If there are any ambiguities, check the meeting notes here... [38890e34a50d80b7af91d669cb66d822](https://www.notion.so/38890e34a50d80b7af91d669cb66d822?source=copy_link) > - Keep 'edit reason' field only for contract values; replace source/editor fields with notes for other input types

## Plan

The current database-backed input editors show form-level `Edit reason` and `Source` fields for yearly inputs, monthly inputs, monthly performance guarantee rows, and performance tests. The meeting-note search confirms those fields existed mainly because contract values need stronger provenance.

This change will:

- Remove the form-level `Edit reason` and `Source` inputs from non-contract input editors.
- Keep the existing row-level `notes` column as the place for operator context on non-contract input rows.
- Allow non-contract table saves without requiring audit `edit_reason` or `source` metadata.
- Keep public save function signatures stable for now, so existing callers are not broken.
- Update the persistent action tracker and feature docs to reflect the table-editing behavior.

## Verification Plan

- Run Python compilation for the edited app modules.
- Run the unit test suite.

---

# Feature Changes

- Non-contract database input editors no longer show form-level `Edit reason` and `Source` fields.
- Operators should use the existing row-level `notes` column to capture context for yearly inputs, monthly inputs, monthly performance guarantee rows, and performance tests.
- Non-contract table saves now accept missing audit metadata and persist nullable `edit_reason` / `source` in `row_edit_history` when rows are inserted or updated.
- Contract values remain read-only in the current UI. The intended future behavior is that contract values are the only input table requiring stricter form-level edit provenance.

---

# Files Changed

- `app/components/db_tables.py`
  - Removed `Edit reason` and `Source` text inputs from non-contract editors.
  - Updated save calls for those editors to pass `None` for form-level audit metadata.

- `app/services/table_editor.py`
  - Added optional audit text normalization.
  - Made audit metadata optional by default while keeping a `require_edit_metadata` option available for future contract-value editing.

- `tests/test_table_editor_normalization.py`
  - Added a regression test confirming yearly input saves no longer require form-level audit metadata.

- `docs/action_items.md`
  - Marked the edit reason/source replacement item as `Done`.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented row-level notes as the non-contract edit context mechanism.
  - Documented that form-level edit provenance is reserved for future contract-value editing.

---

# Summary And Concerns

This change aligns the app with the meeting decision: non-contract input tables should not make users fill duplicate form-level provenance fields when each row already has `notes`. The save service still keeps its public function signatures stable, but it now handles missing `edit_reason` and `source` safely.

Verification completed:

- `python -m py_compile app/components/db_tables.py app/services/table_editor.py`
- `python -m unittest discover -s tests` ran 42 tests successfully.

Concern:

- Contract values are still read-only. When contract-value editing is added, it should explicitly call the table-save path with required edit metadata or use a dedicated contract-value editor that enforces edit reason/source provenance.
