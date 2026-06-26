# Request

Hmm, I dunno, this still isn't working very well. Is there any way that we can do the adding new rows just within the table above, like it was earlier?

---

## Plan

1. Replace the split normal-mode locked table plus separate new-row editor with one `st.data_editor`.
2. Keep `num_rows="dynamic"` so users add new rows at the bottom of the same table.
3. Keep save-time protection: existing-row edits/deletes are still rejected unless Override Mode is on.
4. Remove the spacer-column workaround from the previous alignment attempt.
5. Update docs and run focused tests.

---

## Feature Changes

- Normal-mode input tables now use one `st.data_editor` grid.
- Users add new rows directly at the bottom of the existing table.
- Existing-row edits/deletes are still blocked at save time unless Override Mode is on.
- Removed the previous split-grid spacer workaround.

---

## Files Changed

- `app/components/db_tables.py`
  - Replaced the locked-grid plus new-row-grid normal mode with a single dynamic `st.data_editor`.
  - Removed display-only spacer-column code.
  - Updated normal-mode guidance copy.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Updated the normal-mode input-table behavior documentation.
- `.codex/docs/changes/2026-06-26-single-grid-normal-row-entry.md`
  - Added this implementation record.

---

## Summary And Concerns

The UI now avoids the column alignment problem by using a single table for existing rows and new-row entry. Users can add new rows at the bottom of the table, like the earlier behavior.

Data protection remains in the service layer: if a user changes or deletes an existing row while Override Mode is off, saving raises the existing Override Mode validation error instead of writing the change.

Verification:
- `python -m py_compile app/components/db_tables.py` passed.
- `python -m unittest tests.test_table_editor_normalization` passed.
- `python -m unittest discover -s tests` passed: 73 tests.

Concern:
- Streamlit does not support true row-level locking in one `st.data_editor`. Existing rows are visually editable in normal mode, but they will not save unless Override Mode is enabled.
