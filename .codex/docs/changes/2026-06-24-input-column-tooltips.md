# User Request And Plan

> This is a great idea 'One design note: these should probably live beside TABLE_CONFIGS or in a small column_tooltips.py, then be passed into Streamlit column_config per table. That keeps the UI concise without turning the page into form instructions.' After skimming through them, they look good

## Plan

Add concise contract-aware tooltips to the input table column headers.

- Create a small `app/components/column_tooltips.py` module with the reviewed tooltip mapping.
- Add helper functions in `db_tables.py` that convert that mapping into Streamlit `column_config`.
- Preserve existing date, number, checkbox, required, and disabled behavior in the table editors.
- Apply tooltips to read-only contract values and editable input tables.
- Avoid changing database, calculation, persistence, or run-history behavior.
- Verify the touched Python files compile.

---

# Feature Changes

- Input tables now expose concise contract-aware help text through Streamlit column header tooltips.
- Tooltips are centralized in a dedicated component module instead of being mixed into the main table configuration.
- Existing date, number, checkbox, required, disabled, and dynamic-row editor behavior is preserved.

---

# Files Changed

- `app/components/column_tooltips.py`
  - Added `INPUT_COLUMN_TOOLTIPS`, grouped by input table name.
  - Includes reviewed descriptions for contract values, yearly inputs, monthly inputs, monthly performance guarantee, and performance tests.

- `app/components/db_tables.py`
  - Imports the tooltip mapping.
  - Adds helper functions to build Streamlit `column_config` objects from the mapping.
  - Applies generic tooltip configs to read-only contract values.
  - Applies tooltips to editable tables while preserving specialized date, number, and checkbox column configs.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documents column-header tooltips as part of the database-backed input table behavior.

---

# Summary And Concerns

The input table UI now has inline column guidance without adding long form-style instructions above the tables. The tooltip text is centralized so future wording updates do not require digging through each editor function.

Verification completed:

- `python -m py_compile app/components/db_tables.py app/components/column_tooltips.py`
- Streamlit column config constructor check for `Column`, `DateColumn`, `NumberColumn`, and `CheckboxColumn` with `help=...`

Concern:

- No browser screenshot verification was performed. Streamlit should show these as column-header help tooltips/icons, but final hover behavior should be checked in the running app.
