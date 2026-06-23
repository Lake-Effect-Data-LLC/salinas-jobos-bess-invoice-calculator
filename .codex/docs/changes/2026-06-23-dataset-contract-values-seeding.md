# Original Request And Plan

> Hmm, yeah they definitely need to display in there when you create a new dataset lol

---

## Overview

New database datasets/scenarios should visibly include contract values immediately after creation. Contract values are reference data for a facility, so a new scenario should not require the user to manually recreate them before the dataset is useful.

## Plan

1. Confirm the current dataset-creation behavior in `app/db/datasets.py`.
2. Make the "blank" dataset creation path explicit: it should seed contract values from the facility's default/actual dataset when available.
3. Return the number of copied contract-value rows from dataset creation so the UI can tell the user what happened.
4. Update the Streamlit create-dataset UI labels/messages so users understand that the default blank/scenario path includes contract values.
5. Add focused tests for dataset creation:
   - New scenario copies contract values from `actual`.
   - Full copy still copies all input tables.
6. Update feature documentation for dataset/scenario creation.

## Notes Before Implementation

The current code already attempts to copy contract values from `actual` when `copy_from_dataset_name` is not provided, but the UI does not make that visible and there is no test protecting the behavior. This change should make the behavior explicit and guarded by tests.

---

# Feature Changes

## Dataset Creation Now Explicitly Seeds Contract Values

New datasets created from the default start mode now explicitly start with contract values only. The backend selects the best available contract-value source for the selected facility:

1. Prefer the `actual` dataset if it has contract values.
2. Otherwise prefer the default dataset if it has contract values.
3. Otherwise use another dataset for the project that has contract values.

This preserves the desired behavior that new scenarios are not missing facility contract values.

## Create-Dataset UI Clarifies The Behavior

The Streamlit create-dataset form now uses the label `Start with contract values only` instead of `Blank dataset`. The success message reports how many contract value rows the new dataset has after creation.

---

# Files Changed

## `app/db/datasets.py`

- Added `_get_contract_seed_dataset_id()` to find a source dataset with contract values.
- Updated `create_dataset_config()` so non-copy dataset creation seeds contract values from the selected source dataset when possible.

## `app/streamlit_app.py`

- Renamed the default creation option to `Start with contract values only`.
- Added help text explaining that new scenarios start with facility contract values.
- Updated the creation success message to include the number of contract-value rows in the new dataset.

## `tests/test_dataset_creation.py`

- Added focused tests for dataset creation and contract-value seeding.
- Covered seeding from `actual` and fallback seeding from another dataset with contract values.

## `.codex/docs/features/dataset-scenarios.md`

- Added feature documentation for dataset/scenario creation behavior.

---

# Overall Summary And Concerns

The dataset creation flow now makes the expected behavior explicit: new scenarios are not fully populated, but they do start with contract values so the Contract values table displays useful facility reference data immediately.

Tests passed:

- `.\.venv\Scripts\python.exe -m unittest tests.test_dataset_creation`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests`

Remaining concern:

- If no existing dataset for the selected project has contract values, the new dataset will still be created with zero contract-value rows. The UI reports `0 contract value rows`, but there is not yet a blocking warning or import prompt for that case.
