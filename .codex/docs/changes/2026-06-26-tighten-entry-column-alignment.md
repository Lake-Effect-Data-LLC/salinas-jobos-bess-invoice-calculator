# Request

Not bad, could be better, and you only did it to the monthly input

---

## Plan

1. Improve the remaining horizontal offset between locked rows and the new-row entry grid.
2. Replace the visible row index approach with a narrow blank spacer column on the locked grid.
3. Keep the change inside the shared `_render_guarded_editor()` path so it applies to all normal add-row input tables.
4. Keep contract values unchanged because they do not use the normal add-new-rows flow.
5. Run focused checks.

---

## Feature Changes

- Replaced the locked grid's visible row-index alignment approach with a narrow blank spacer column.
- The spacer exists only in the locked display grid and is not included in saved data.
- The shared normal input-table renderer applies this to monthly inputs, yearly inputs, monthly performance guarantee, and performance tests.

---

## Files Changed

- `app/components/db_tables.py`
  - Added `_with_entry_gutter_spacer()` to prepend a display-only spacer column to locked tables.
  - Added a narrow blank `st.column_config.TextColumn` for the spacer.
  - Switched locked tables back to `hide_index=True`.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Updated the alignment behavior documentation.
- `.codex/docs/changes/2026-06-26-tighten-entry-column-alignment.md`
  - Added this implementation record.

---

## Summary And Concerns

The remaining mismatch was caused by gutter sizing. The previous visible-index approach added too much width. This change uses a display-only blank spacer column instead, so the first real data column should align more closely with the new-row editor below.

Verification:
- `python -m py_compile app/components/db_tables.py` passed.
- `python -m unittest discover -s tests` passed: 73 tests.

Concern:
- This is still constrained by Streamlit's internal table layout. The spacer width may need a small tweak if browser/device rendering differs, but this avoids brittle DOM/CSS manipulation.
