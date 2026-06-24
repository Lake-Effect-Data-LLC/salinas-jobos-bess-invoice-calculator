# User Request And Plan

> "That makes sense regarding Streamlit's native limitations; let's definitely avoid any brittle DOM/JavaScript hacks.
> Looking back at our design meeting notes, our primary constraint was to provide clear variable descriptions for data entry without turning the UI into a bloated, vertical 'form-style flow'. We want to keep the clean, spreadsheet-like layout.
> Given that, your suggestion for Option 2 (a compact 'Column guide' expander under each table) is the best path forward.
> Please proceed with that approach:
> 1. Add an st.expander(" Column Guide") directly underneath the st.data_editor so it sits right below the new row entry area.
> 2. Inside the expander, list the column names and their contract-derived descriptions in a clean, readable format (e.g., markdown bullet points).
> 3. Keep the expander collapsed by default so it doesn't clutter the screen.
> 4. We can leave the native header tooltips in place as a secondary help mechanism."

## Plan

Add native Streamlit column-guide expanders below each editable input table.

- Reuse the existing `INPUT_COLUMN_TOOLTIPS` mapping.
- Render a collapsed `st.expander("Column Guide")` immediately after each `st.data_editor`.
- Show concise markdown bullets with column names and descriptions.
- Keep header tooltips in place.
- Avoid JavaScript, DOM hacks, database changes, or calculation changes.
- Verify `app/components/db_tables.py` compiles.

---

# Feature Changes

- Editable input tables now show a collapsed `Column Guide` expander directly below the data editor.
- The guide lists each column name with its contract-derived description.
- Existing header tooltips remain in place.
- The UI stays spreadsheet-like because the descriptions are hidden until the user opens the guide.

---

# Files Changed

- `app/components/db_tables.py`
  - Calls `_render_column_guide(...)` after each editable `st.data_editor`.
  - Adds `_render_column_guide` helper that renders markdown bullets from `INPUT_COLUMN_TOOLTIPS`.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documents the collapsed column-guide behavior for editable input tables.

---

# Summary And Concerns

This adds a native Streamlit help pattern near the bottom entry area without relying on unsupported cell-click events or brittle JavaScript. Users can keep the spreadsheet-like editor clean by default and open the guide when they need field definitions during data entry.

Verification completed:

- `python -m py_compile app/components/db_tables.py`

Concern:

- The guide appears below the whole editor rather than attached to a specific focused cell, because native Streamlit does not expose per-cell focus events.
