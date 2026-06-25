# Scenario Creation

## Overview

Database-backed runs are organized by facility and dataset:

- Facility maps to `project`, such as `salinas` or `jobos`.
- Scenario maps to `dataset_config`, such as `actual`, `testing`, or `scenario_1`.
- Input rows belong to a dataset through `dataset_config_id`.

Working structure:

```text
project
  -> dataset_config
    -> input rows
    -> run snapshots
      -> output file metadata
```

Meaning:

- `project` is the facility.
- `dataset_config` is the named input version/scenario for that facility.
- The five input tables are scoped to `dataset_config`.
- A run snapshot is a record that a specific `dataset_config` was calculated at a specific time.
- Output file metadata is stored separately and can be linked to the run snapshot.

Run snapshots should not be treated as datasets. They are children of a dataset/scenario.

## Feature Behavior

Users can create a new dataset/scenario from the Streamlit sidebar while using the database data source.

Users can also delete a selected dataset/scenario from the Streamlit sidebar. Deletion is destructive and requires confirmation in a native Streamlit dialog.

Creation modes:

- **Start with contract values only**
  - Creates a new dataset for the selected facility.
  - Seeds the new dataset with contract values from the best available source dataset.
  - Leaves yearly inputs, monthly inputs, monthly performance guarantee rows, and performance tests empty.

- **Copy existing dataset**
  - Creates a new dataset for the selected facility.
  - Copies all five input tables from the selected base dataset.

After creation, the app selects the new dataset and reruns so the user can immediately see the seeded data in the input tables.

After deletion, the app selects the default or first available remaining scenario for the same facility and reruns. If no scenarios remain, the app clears the selected scenario and returns to the no-datasets state.

## Technical Details

Primary code:

- `app/db/datasets.py`
  - `create_dataset_config()`
  - `delete_dataset_config()`
  - `_get_contract_seed_dataset_id()`
  - `_copy_contract_values()`
  - `_copy_input_tables()`

- `app/streamlit_app.py`
  - `render_create_dataset_panel()`
  - `render_delete_scenario_dialog()`

Delete behavior:

1. Delete `file_object` rows for the selected `dataset_config_id`.
2. Delete the `dataset_config` row for the selected facility and scenario.
3. Let `ON DELETE CASCADE` remove child input rows, run snapshots, row edit history, and validation rows.

`file_object` is explicitly deleted first because its foreign key to `dataset_config` is `ON DELETE SET NULL`; without the explicit delete, file metadata would remain detached from the deleted scenario.

Run-history model:

- `monthly_snapshot.dataset_config_id` links a calculation run snapshot to the dataset/scenario that produced it.
- `monthly_snapshot.snapshot_month` identifies the most recent or representative calculation month for that run and is stored as the first day of the month.
- `monthly_snapshot.snapshot_name` should be unique per run, such as a timestamped `calculation_run_...` name.
- `monthly_snapshot.snapshot_data` stores the run summary payload.
- Current no-MinIO dashboard snapshots store `latest_month_summary`, `csv_text`, and `report_text` in `snapshot_data`.
- `monthly_snapshot.source_file_object_id` can link the run to downloadable output metadata in `file_object`.
- `file_object.dataset_config_id` links output file metadata back to the dataset/scenario.

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
- Deleting a dataset removes scenario-owned file metadata and cascades child scenario rows.
