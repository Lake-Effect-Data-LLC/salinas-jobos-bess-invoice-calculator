# Request

Can we get the input columns and the entry field columns to line up, is that a clear request?

---

## Plan

1. Keep the normal-mode behavior: existing rows remain locked and new rows are entered separately.
2. Replace the normal-mode existing-row `st.dataframe` with a disabled `st.data_editor` so the locked table and new-row entry grid use the same Streamlit table renderer.
3. Keep column config, tooltips, hidden index, and new-row behavior unchanged.
4. Run focused syntax/tests.

---

## Feature Changes

- Normal-mode existing input rows now render through disabled `st.data_editor` instead of `st.dataframe`.
- The locked existing-row grid and the new-row entry grid now use the same Streamlit table component and column config, improving column alignment.
- Existing rows remain read-only in normal mode.

---

## Files Changed

- `app/components/db_tables.py`
  - Changed `_render_guarded_editor()` so the normal-mode locked table uses `st.data_editor(..., disabled=list(editable_table.columns))`.
  - Added a stable locked-editor key per table/project/dataset.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented that the locked rows use a disabled editor grid to align with the new-row entry grid.
- `.codex/docs/changes/2026-06-26-align-input-display-entry-columns.md`
  - Added this implementation record.

---

## Summary And Concerns

The existing input display and the entry grid now share the same renderer, which should line up columns much more consistently than mixing `st.dataframe` and `st.data_editor`.

Verification:
- `python -m py_compile app/components/db_tables.py` passed.
- `python -m unittest discover -s tests` passed: 73 tests.

Concern:
- Streamlit still controls some internal row-control/header spacing in `st.data_editor`, so exact pixel-perfect alignment may vary by browser width. This avoids brittle CSS/DOM hacks and uses native Streamlit behavior.
