# Request

I mean, it's kinda close, but look at the line I drew..

---

## Plan

1. Treat the visible mismatch as a left-gutter mismatch between the locked existing-row grid and the new-row entry grid.
2. Keep both grids using native Streamlit components.
3. Show the locked grid index/gutter so the first real data column starts at the same horizontal offset as the new-row editor.
4. Keep new-row behavior and save behavior unchanged.
5. Run focused checks.

---

## Feature Changes

- The locked existing-row input grid now shows its left index/gutter.
- This aligns the first real data column with the new-row entry grid below, which already has a left row-control gutter.
- Existing rows remain disabled/read-only in normal mode.

---

## Files Changed

- `app/components/db_tables.py`
  - Updated the normal-mode locked `st.data_editor` to use `hide_index=False`.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the visible left gutter alignment behavior.
- `.codex/docs/changes/2026-06-26-align-input-entry-left-gutter.md`
  - Added this implementation record.

---

## Summary And Concerns

The alignment issue came from different left gutters: the new-row editor had a leading row-control area, while the locked table did not. Showing the locked table's native left gutter makes the real data columns start at the same horizontal position.

Verification:
- `python -m py_compile app/components/db_tables.py` passed.
- `python -m unittest discover -s tests` passed: 73 tests.

Concern:
- This may show row index numbers on the locked table. It avoids custom CSS/DOM hacks and keeps the fix native to Streamlit.
