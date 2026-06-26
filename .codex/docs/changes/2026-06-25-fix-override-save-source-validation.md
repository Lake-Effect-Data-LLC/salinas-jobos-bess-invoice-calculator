# Request

In app/services/table_editor.py, the check at line 362 (if existing_row_changes and source is None: raise ValueError(...)) always fires during Override Mode saves because override_source in app/components/db_tables.py is hardcoded to None and never populated. Either remove the source requirement from the existing_row_changes validation block (keeping it only under require_edit_metadata), or add a source/editor text input to _render_save_controls in db_tables.py and wire it through. Verify the fix by turning on Override Mode, deleting a row, and confirming the save completes without error.

---

## Plan

1. Inspect `app/services/table_editor.py` and `app/components/db_tables.py` to confirm where `source` is required and where `override_source` is passed.
2. Keep the UI simple by not adding another editor/source field.
3. Make Override Mode existing-row edits/deletes require only the override edit reason unless a specific save path sets `require_edit_metadata=True`.
4. Update focused tests so an Override Mode delete with `source=None` succeeds.
5. Run the table-editor tests and a syntax check.

---

## Feature Changes

- Aligned Override Mode audit behavior with the current UI: existing-row edits/deletes require an edit reason, but do not require a separate source/editor field.
- Added regression coverage for Override Mode update/delete saves with `source=None`.
- Updated persistent runtime documentation so it no longer claims Override Mode requires an audit `source` value.

---

## Files Changed

- `tests/test_table_editor_normalization.py`
  - Removed the stale expectation that Override Mode saves fail without editor/source identity.
  - Updated audited update/delete tests to pass `source=None`.
  - Asserted the audit rows preserve nullable `source`.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Updated audit behavior documentation to say `source` remains nullable until explicit identity/source capture is wired in.
- `.codex/docs/changes/2026-06-25-fix-override-save-source-validation.md`
  - Added the plan and implementation summary for this fix.

---

## Summary And Concerns

The service code in `app/services/table_editor.py` is already in the intended shape: `source` is only required when `require_edit_metadata=True`, not for ordinary Override Mode existing-row changes. The stale part was test/documentation coverage that still assumed an override editor/source value was mandatory.

The regression tests now verify that Override Mode update/delete saves can complete with `source=None` as long as an edit reason is provided.

Verification:
- `python -m unittest tests.test_table_editor_normalization` passed.
- `python -m py_compile app/services/table_editor.py app/components/db_tables.py` passed.

Concern:
- I attempted a browser click-through verification, but the in-app browser connector failed before attaching to localhost. I did not perform the manual UI delete/save verification from the browser. The unit test covers the exact validation failure path that was blocking the UI.
