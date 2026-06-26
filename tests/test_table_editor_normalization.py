import unittest
from unittest.mock import patch

import pandas as pd

from app.services.table_editor import (
    generate_audit_event_id,
    _normalize_monthly_inputs_df,
    _normalize_monthly_performance_guarantee_df,
    _normalize_yearly_inputs_df,
    save_contract_value_deletes,
    save_yearly_inputs_edits,
)


class TableEditorNormalizationTest(unittest.TestCase):
    def test_yearly_inputs_accept_normal_integer_cells(self):
        df = pd.DataFrame(
            [
                {
                    "id": "row-1",
                    "agreement_year": 1,
                    "dde": 400,
                    "tr": 100,
                    "gc": 3,
                    "source_reference": None,
                    "notes": None,
                }
            ]
        )

        self.assertEqual(
            _normalize_yearly_inputs_df(df, require_id=True),
            [
                {
                    "id": "row-1",
                    "agreement_year": 1,
                    "dde": 400.0,
                    "tr": 100.0,
                    "gc": 3.0,
                    "source_reference": "",
                    "notes": "",
                }
            ],
        )

    def test_yearly_inputs_unwrap_duplicate_column_series_cells(self):
        df = pd.DataFrame(
            [
                [
                    "row-1",
                    None,
                    1,
                    400,
                    100,
                    3,
                    None,
                    None,
                ]
            ],
            columns=[
                "id",
                "agreement_year",
                "agreement_year",
                "dde",
                "tr",
                "gc",
                "source_reference",
                "notes",
            ],
        )

        records = _normalize_yearly_inputs_df(df, require_id=True)

        self.assertEqual(records[0]["agreement_year"], 1)

    def test_yearly_inputs_unwrap_single_value_list_cells(self):
        df = pd.DataFrame(
            [
                {
                    "id": "row-1",
                    "agreement_year": [1],
                    "dde": 400,
                    "tr": 100,
                    "gc": 15,
                    "source_reference": None,
                    "notes": None,
                }
            ]
        )

        records = _normalize_yearly_inputs_df(df, require_id=True)

        self.assertEqual(records[0]["agreement_year"], 1)

    def test_monthly_inputs_unwrap_single_value_list_month_cells(self):
        df = pd.DataFrame(
            [
                {
                    "id": "row-1",
                    "timestamp_month": ["2026-01-15"],
                    "agreement_year": 1,
                    "other_adj": 0,
                    "bphrs": 744,
                    "pohrs": 8,
                    "unavhrs": 2,
                    "unavprodhrs": 1,
                    "gse": 3,
                    "pfm": 0,
                    "ip": 0,
                    "source_reference": None,
                    "notes": None,
                }
            ]
        )

        records = _normalize_monthly_inputs_df(df, require_id=True)

        self.assertEqual(records[0]["timestamp_month"], "2026-01-01")

    def test_monthly_performance_guarantee_unwrap_single_value_list_month_cells(self):
        df = pd.DataFrame(
            [
                {
                    "id": "row-1",
                    "timestamp_month": ["2026-01-15"],
                    "agreement_year": 1,
                    "ce": 100,
                    "de": 90,
                    "ae_beg": 50,
                    "ae_end": 45,
                    "source_reference": None,
                    "notes": None,
                }
            ]
        )

        records = _normalize_monthly_performance_guarantee_df(df, require_id=True)

        self.assertEqual(records[0]["timestamp_month"], "2026-01-01")

    def test_yearly_inputs_do_not_require_form_audit_metadata(self):
        df = pd.DataFrame(
            [
                {
                    "id": "row-1",
                    "agreement_year": 1,
                    "dde": 400,
                    "tr": 100,
                    "gc": 15,
                    "source_reference": None,
                    "notes": "Manual note in the table row",
                }
            ]
        )

        result = save_yearly_inputs_edits(
            engine=None,
            project_id="salinas",
            dataset_name="actual",
            original_df=df,
            edited_df=df.copy(),
            edit_reason=None,
            source=None,
        )

        self.assertEqual(result, {"inserted": 0, "updated": 0, "deleted": 0})

    def test_existing_update_requires_override_mode(self):
        original_df = _yearly_input_df()
        edited_df = original_df.copy()
        edited_df.loc[0, "dde"] = 401

        with self.assertRaisesRegex(ValueError, "Override Mode"):
            save_yearly_inputs_edits(
                engine=None,
                project_id="salinas",
                dataset_name="actual",
                original_df=original_df,
                edited_df=edited_df,
                edit_reason=None,
                source=None,
            )

    def test_delete_requires_override_mode(self):
        original_df = _yearly_input_df()
        edited_df = original_df.iloc[0:0].copy()

        with self.assertRaisesRegex(ValueError, "Override Mode"):
            save_yearly_inputs_edits(
                engine=None,
                project_id="salinas",
                dataset_name="actual",
                original_df=original_df,
                edited_df=edited_df,
                edit_reason=None,
                source=None,
            )

    def test_override_update_requires_edit_reason(self):
        original_df = _yearly_input_df()
        edited_df = original_df.copy()
        edited_df.loc[0, "dde"] = 401

        with self.assertRaisesRegex(ValueError, "edit reason"):
            save_yearly_inputs_edits(
                engine=None,
                project_id="salinas",
                dataset_name="actual",
                original_df=original_df,
                edited_df=edited_df,
                edit_reason=None,
                source="Override Mode",
                allow_existing_row_changes=True,
            )

    def test_override_update_is_audited(self):
        original_df = _yearly_input_df()
        edited_df = original_df.copy()
        edited_df.loc[0, "dde"] = 401
        engine = _FakeEngine()
        updated_records = []

        with patch(
            "app.services.table_editor.get_dataset_config_id",
            return_value="dataset-id",
        ), patch(
            "app.services.table_editor._update_yearly_input",
            side_effect=lambda _connection, record: updated_records.append(record),
        ):
            result = save_yearly_inputs_edits(
                engine=engine,
                project_id="salinas",
                dataset_name="actual",
                original_df=original_df,
                edited_df=edited_df,
                edit_reason="Correct source data",
                source=None,
                allow_existing_row_changes=True,
                audit_event_id="audit_event_test",
            )

        self.assertEqual(
            result,
            {
                "inserted": 0,
                "updated": 1,
                "deleted": 0,
                "audit_event_id": "audit_event_test",
            },
        )
        self.assertEqual(updated_records[0]["dde"], 401.0)
        self.assertEqual(engine.connection.executions[0]["action"], "update")
        self.assertEqual(
            engine.connection.executions[0]["audit_event_id"],
            "audit_event_test",
        )
        self.assertEqual(
            engine.connection.executions[0]["edit_reason"],
            "Correct source data",
        )
        self.assertIsNone(engine.connection.executions[0]["source"])

    def test_override_delete_is_audited(self):
        original_df = _yearly_input_df()
        edited_df = original_df.iloc[0:0].copy()
        engine = _FakeEngine()
        deleted_ids = []

        with patch(
            "app.services.table_editor.get_dataset_config_id",
            return_value="dataset-id",
        ), patch(
            "app.services.table_editor._delete_yearly_input",
            side_effect=lambda _connection, row_id: deleted_ids.append(row_id),
        ):
            result = save_yearly_inputs_edits(
                engine=engine,
                project_id="salinas",
                dataset_name="actual",
                original_df=original_df,
                edited_df=edited_df,
                edit_reason="Remove duplicate year",
                source=None,
                allow_existing_row_changes=True,
                audit_event_id="audit_event_delete_test",
            )

        self.assertEqual(
            result,
            {
                "inserted": 0,
                "updated": 0,
                "deleted": 1,
                "audit_event_id": "audit_event_delete_test",
            },
        )
        self.assertEqual(deleted_ids, ["row-1"])
        self.assertEqual(engine.connection.executions[0]["action"], "delete")
        self.assertEqual(
            engine.connection.executions[0]["audit_event_id"],
            "audit_event_delete_test",
        )
        self.assertEqual(engine.connection.executions[0]["new_data"], None)
        self.assertIsNone(engine.connection.executions[0]["source"])

    def test_generate_audit_event_id_uses_utc_timestamp(self):
        audit_event_id = generate_audit_event_id(
            pd.Timestamp("2026-06-26T14:30:22.123456Z").to_pydatetime()
        )

        self.assertEqual(audit_event_id, "audit_event_20260626T143022123456Z")

    def test_contract_values_are_delete_only(self):
        original_df = _contract_value_df()
        edited_df = original_df.copy()
        edited_df.loc[0, "cppf"] = 24000

        with self.assertRaisesRegex(ValueError, "Editing existing contract value"):
            save_contract_value_deletes(
                engine=None,
                project_id="salinas",
                dataset_name="actual",
                original_df=original_df,
                edited_df=edited_df,
                edit_reason="Contract correction",
                source="Override Mode",
                allow_existing_row_changes=True,
            )


class _FakeEngine:
    def __init__(self):
        self.connection = _FakeConnection()

    def begin(self):
        return self.connection


class _FakeConnection:
    def __init__(self):
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, _statement, params):
        self.executions.append(params)


def _yearly_input_df():
    return pd.DataFrame(
        [
            {
                "id": "row-1",
                "agreement_year": 1,
                "dde": 400,
                "tr": 100,
                "gc": 15,
                "source_reference": None,
                "notes": "Manual note in the table row",
            }
        ]
    )


def _contract_value_df():
    return pd.DataFrame(
        [
            {
                "id": "contract-1",
                "agreement_year": 1,
                "cppf": 23696,
                "cpppif": 1200,
                "ddd": 4,
                "ta": 0.7,
                "rer": 170,
                "ge": 0.85,
                "design_dmax": 100,
                "design_duration_energy": 400,
                "annual_duration_energy_degradation_rate": 0,
                "design_charge_energy": 468,
                "grid_system_waiting_period_hours": 80,
                "force_majeure_waiting_period_hours": 720,
                "scheduled_maintenance_allowance_hours": 100,
                "source_reference": "",
                "notes": "",
            }
        ]
    )


if __name__ == "__main__":
    unittest.main()
