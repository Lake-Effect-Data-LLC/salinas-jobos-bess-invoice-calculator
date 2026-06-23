# Dataset / Scenario Creation

## Overview

Database-backed runs are organized by facility and dataset:

- Facility maps to `project`, such as `salinas` or `jobos`.
- Dataset / Scenario maps to `dataset_config`, such as `actual`, `testing`, or `scenario_1`.
- Input rows belong to a dataset through `dataset_config_id`.

## Feature Behavior

Users can create a new dataset/scenario from the Streamlit sidebar while using the database data source.

Creation modes:

- **Start with contract values only**
  - Creates a new dataset for the selected facility.
  - Seeds the new dataset with contract values from the best available source dataset.
  - Leaves yearly inputs, monthly inputs, monthly performance guarantee rows, and performance tests empty.

- **Copy existing dataset**
  - Creates a new dataset for the selected facility.
  - Copies all five input tables from the selected base dataset.

After creation, the app selects the new dataset and reruns so the user can immediately see the seeded data in the input tables.

## Technical Details

Primary code:

- `app/db/datasets.py`
  - `create_dataset_config()`
  - `_get_contract_seed_dataset_id()`
  - `_copy_contract_values()`
  - `_copy_input_tables()`

- `app/streamlit_app.py`
  - `render_create_dataset_panel()`

Contract-value seed selection:

1. Prefer a dataset named `actual` for the same project if it has contract values.
2. Otherwise prefer the default dataset if it has contract values.
3. Otherwise use another dataset for the project that has contract values.
4. If no source dataset has contract values, the new dataset is created without contract-value rows.

The create-dataset UI reports how many contract value rows are present in the newly created dataset.

## Tests

Primary tests:

- `tests/test_dataset_creation.py`

Covered cases:

- New dataset copies contract values from `actual`.
- New dataset can fall back to another dataset with contract values when `actual` has none.
