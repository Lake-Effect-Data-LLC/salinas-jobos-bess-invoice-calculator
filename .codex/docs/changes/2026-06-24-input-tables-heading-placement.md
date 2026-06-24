# User Request And Plan

> Can you put the header Input Tables above the table above it? Does that make sense?

## Plan

Yes. The row-count summary table belongs to the input tables section, but the `Input Tables` heading currently renders below it.

- Move the `Input Tables` heading into `streamlit_app.py` before the row-count summary table.
- Remove the duplicate heading from `render_database_table_views`.
- Keep the row-count summary, warnings, tabs, editors, database behavior, and run-history behavior unchanged.
- Verify `app/streamlit_app.py` and `app/components/db_tables.py` compile.

---

# Feature Changes

- The `Input Tables` heading now appears above the input row-count summary table.
- The row-count summary is visually grouped with the input table tabs below it.

---

# Files Changed

- `app/streamlit_app.py`
  - Added `st.subheader("Input Tables")` immediately before the row-count summary dataframe.

- `app/components/db_tables.py`
  - Removed the duplicate `Input Tables` heading from `render_database_table_views`.

---

# Summary And Concerns

This reorders the section heading so the row-count summary table is clearly part of the input tables section. The database reads, warnings, tabs, editors, run history, and calculation behavior are unchanged.

Verification completed:

- `python -m py_compile app/streamlit_app.py app/components/db_tables.py`

Concern:

- No browser screenshot verification was performed; visually confirm spacing after Streamlit refresh.
