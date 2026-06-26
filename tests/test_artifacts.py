import json
import unittest
from datetime import datetime, timezone

from app.artifacts import (
    artifact_to_json_bytes,
    build_calculation_package_artifact,
    build_scenario_state_artifact,
)
from app.storage import build_run_artifact_key, build_scenario_state_key


class ArtifactTest(unittest.TestCase):
    def test_build_scenario_state_artifact_stores_all_inputs(self):
        exported_at = datetime(2026, 6, 25, 12, 30, tzinfo=timezone.utc)
        inputs = {
            "contract_values": [{"agreement_year": 1}],
            "yearly_inputs": [{"agreement_year": 1}],
            "monthly_inputs": [{"timestamp_month": "2026-01-01"}],
            "monthly_performance_guarantee": [{"timestamp_month": "2026-01-01"}],
            "performance_tests": [{"test_id": "PT-1"}],
        }

        artifact = build_scenario_state_artifact(
            "salinas",
            "actual",
            inputs,
            exported_at=exported_at,
        )

        self.assertEqual(artifact["artifact_type"], "scenario_state")
        self.assertEqual(artifact["project_id"], "salinas")
        self.assertEqual(artifact["dataset_name"], "actual")
        self.assertEqual(artifact["exported_at"], "2026-06-25T12:30:00+00:00")
        self.assertEqual(artifact["inputs"], inputs)

    def test_build_scenario_state_artifact_stores_change_context(self):
        artifact = build_scenario_state_artifact(
            "salinas",
            "actual",
            {"monthly_inputs": []},
            change_context={
                "audit_event_id": "audit_event_test",
                "table_name": "monthly_inputs",
                "change_result": {"inserted": 0, "updated": 1, "deleted": 0},
                "edit_reason": "Corrected January inputs",
            },
            exported_at=datetime(2026, 6, 25, 12, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(artifact["audit_event_id"], "audit_event_test")
        self.assertEqual(
            artifact["change_context"],
            {
                "audit_event_id": "audit_event_test",
                "table_name": "monthly_inputs",
                "change_result": {"inserted": 0, "updated": 1, "deleted": 0},
                "edit_reason": "Corrected January inputs",
            },
        )

    def test_build_calculation_package_artifact_includes_outputs_and_inputs(self):
        snapshot_data = {
            "latest_month_summary": {"timestamp_month": "2026-02-01", "MP": 100},
            "csv_text": "timestamp_month,MP\n2026-02-01,100\n",
            "report_text": "report",
            "inputs": {"monthly_inputs": [{"timestamp_month": "2026-02-01"}]},
        }

        artifact = build_calculation_package_artifact(
            "salinas",
            "actual",
            "2026-02-01",
            "calculation_run_test",
            snapshot_data,
            exported_at=datetime(2026, 6, 25, tzinfo=timezone.utc),
        )

        self.assertEqual(artifact["artifact_type"], "calculation_package")
        self.assertEqual(artifact["latest_month_summary"]["MP"], 100)
        self.assertIn("2026-02-01", artifact["csv_text"])
        self.assertEqual(artifact["report_text"], "report")
        self.assertEqual(
            artifact["inputs"]["monthly_inputs"][0]["timestamp_month"],
            "2026-02-01",
        )

    def test_artifact_to_json_bytes_is_readable_json(self):
        data = artifact_to_json_bytes({"artifact_type": "scenario_state"})

        self.assertEqual(
            json.loads(data.decode("utf-8")),
            {"artifact_type": "scenario_state"},
        )

    def test_storage_keys_separate_scenario_state_and_run_packages(self):
        self.assertEqual(
            build_scenario_state_key("salinas", "actual", "scenario_state_test"),
            "scenario_state/salinas/actual/scenario_state_test.json",
        )
        self.assertEqual(
            build_scenario_state_key(
                "salinas",
                "actual",
                "scenario_state_test",
                "csv",
            ),
            "scenario_state/salinas/actual/scenario_state_test.csv",
        )
        self.assertEqual(
            build_run_artifact_key(
                "salinas",
                "actual",
                "2026-02-01",
                "calculation_run_test",
                "package.json",
            ),
            "run_history/salinas/actual/2026-02/calculation_run_test.package.json",
        )


if __name__ == "__main__":
    unittest.main()
