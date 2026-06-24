# User Request And Plan

> Let's do this too. Tab label
> Brief table guidance
> Column Guide
> Editable table
> Save button

## Plan

Move the existing collapsed Column Guide above each editable data editor.

- Keep tab labels and brief guidance captions as-is.
- Render `Column Guide` immediately after guidance and before the editable table.
- Keep the guide collapsed by default.
- Preserve header tooltips, editor behavior, save behavior, database behavior, and calculations.
- Verify `app/components/db_tables.py` compiles.

---

# Feature Changes

- Column Guide expanders now render before each editable table.
- The input table flow is now: tab label, brief guidance, Column Guide, editable table, save button.
- Header tooltips and collapsed guide behavior are unchanged.

---

# Files Changed

- `app/components/db_tables.py`
  - Moved `_render_column_guide(...)` calls from below each `st.data_editor` to above each `st.data_editor`.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Updated Column Guide placement wording.

---

# Summary And Concerns

This is a UI placement change only. It makes the field guide more discoverable before users scan or edit the table while preserving the compact collapsed state and existing editor behavior.

Verification completed:

- `python -m py_compile app/components/db_tables.py`
