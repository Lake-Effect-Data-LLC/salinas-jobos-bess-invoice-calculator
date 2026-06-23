# Original Request And Plan

> Remove dead compatibility paths

---

## Overview

The app direction is database-first. The Streamlit runtime still contains a `CSV / local files` vs `Database` data-source toggle and CSV-only run helpers. That path is now compatibility UI rather than the main product workflow.

## Plan

1. Review existing feature/action documentation for the refactoring item.
2. Remove the Streamlit data-source toggle and make the database-backed flow the default app path.
3. Remove now-unused CSV runtime helper imports/functions from `app/streamlit_app.py`.
4. Leave CSV import/roundtrip tooling intact because CSV remains import/export/audit tooling, not the steady-state app source of truth.
5. Run compile and test checks.
6. Update `docs/action_items.md` and this change note with the completed work and any concerns.

---

# Feature Changes

## Streamlit Runtime Is Database-First

The main Streamlit app now goes directly into the database-backed workflow. Users no longer choose between `CSV / local files` and `Database` in the sidebar.

## CSV Runtime Compatibility UI Removed

Removed the Streamlit CSV upload/preview/validate/run path from `app/streamlit_app.py` and deleted the now-unused `app/components/inputs.py` component.

CSV support remains through command-line import and verification tools:

- `tools/import_csv_to_db.py`
- `tools/verify_db_roundtrip.py`

---

# Files Changed

## `app/streamlit_app.py`

- Removed the data-source radio toggle.
- Removed `render_csv_flow()`.
- Removed CSV-only validation/run helper functions and imports.
- Kept database-backed calculation and report generation.

## `app/components/inputs.py`

- Deleted. It only supported the removed runtime CSV upload UI.

## `README`

- Updated the Streamlit App section to describe the database-backed runtime.
- Clarified that CSV is now import/verification tooling rather than the live app source.

## `docs/action_items.md`

- Marked the dead compatibility/toggle cleanup item as `Done`.
- Updated the refactoring plan notes to show what was removed and what remains.

## `.codex/docs/features/database-backed-streamlit-runtime.md`

- Added feature documentation for the database-first Streamlit runtime.

---

# Overall Summary And Concerns

The runtime app no longer carries the old CSV/local-file compatibility path. This reduces sidebar clutter and aligns the UI with the project direction that Postgres is the source of truth.

Concern:

- Users who still need CSV data entry must use import tooling. The app does not yet provide a replacement in-app CSV import/export workflow.
