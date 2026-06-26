import unittest

import pandas as pd

from app.components.results import (
    build_inputs_csv_text,
    build_run_csv_text,
    build_run_snapshot_data,
)


class ResultsSnapshotTest(unittest.TestCase):
    def test_build_run_snapshot_data_stores_latest_summary_csv_and_report(self):
        results_df = pd.DataFrame(
            [
                {
                    "timestamp_month": "2026-01-01",
                    "CPP": 10,
                    "MCC": 90,
                    "FAA": 0.98,
                    "PRA": 1,
                    "MFP": 882,
                    "MP": 875,
                },
                {
                    "timestamp_month": "2026-02-01",
                    "CPP": 11,
                    "MCC": 95,
                    "FAA": 0.99,
                    "PRA": 1,
                    "MFP": 1034.55,
                    "MP": 1000.25,
                },
            ]
        )

        inputs = {
            "contract_values": [{"agreement_year": 1, "cppf": 100}],
            "yearly_inputs": [{"agreement_year": 1, "dde": 400}],
            "monthly_inputs": [{"timestamp_month": "2026-02-01", "bphrs": 672}],
            "monthly_performance_guarantee": [
                {"timestamp_month": "2026-02-01", "ce": 1000}
            ],
            "performance_tests": [{"test_id": "PT-1", "tde": 400}],
        }

        snapshot_data = build_run_snapshot_data(
            results_df,
            "report text",
            inputs=inputs,
        )

        self.assertEqual(
            snapshot_data["latest_month_summary"]["timestamp_month"],
            "2026-02-01",
        )
        self.assertEqual(snapshot_data["latest_month_summary"]["MP"], 1000.25)
        self.assertIn("2026-01-01", snapshot_data["csv_text"])
        self.assertIn("2026-02-01", snapshot_data["csv_text"])
        self.assertIn("SECTION,contract_values", snapshot_data["csv_text"])
        self.assertIn("SECTION,yearly_inputs", snapshot_data["csv_text"])
        self.assertIn("SECTION,monthly_inputs", snapshot_data["csv_text"])
        self.assertIn(
            "SECTION,monthly_performance_guarantee",
            snapshot_data["csv_text"],
        )
        self.assertIn("SECTION,performance_tests", snapshot_data["csv_text"])
        self.assertEqual(snapshot_data["inputs"], inputs)
        self.assertEqual(snapshot_data["report_text"], "report text")

    def test_build_run_snapshot_data_rejects_empty_results(self):
        with self.assertRaisesRegex(ValueError, "empty calculation results"):
            build_run_snapshot_data(pd.DataFrame(), "report text")

    def test_build_run_csv_text_without_inputs_still_exports_results(self):
        results_df = pd.DataFrame(
            [
                {
                    "timestamp_month": "2026-01-01",
                    "MP": 875,
                }
            ]
        )

        csv_text = build_run_csv_text(results_df)

        self.assertIn("SECTION,monthly_results", csv_text)
        self.assertIn("timestamp_month,MP", csv_text)
        self.assertIn("2026-01-01,875", csv_text)

    def test_build_inputs_csv_text_exports_all_five_input_sections(self):
        csv_text = build_inputs_csv_text(
            {
                "contract_values": [{"agreement_year": 1, "cppf": 100}],
                "yearly_inputs": [{"agreement_year": 1, "dde": 400}],
                "monthly_inputs": [{"timestamp_month": "2026-01-01"}],
                "monthly_performance_guarantee": [{"timestamp_month": "2026-01-01"}],
                "performance_tests": [{"test_id": "PT-1"}],
            }
        )

        self.assertIn("SECTION,contract_values", csv_text)
        self.assertIn("SECTION,yearly_inputs", csv_text)
        self.assertIn("SECTION,monthly_inputs", csv_text)
        self.assertIn("SECTION,monthly_performance_guarantee", csv_text)
        self.assertIn("SECTION,performance_tests", csv_text)
        self.assertNotIn("SECTION,monthly_results", csv_text)

    def test_build_inputs_csv_text_can_include_change_summary(self):
        csv_text = build_inputs_csv_text(
            {"monthly_inputs": [{"timestamp_month": "2026-01-01"}]},
            change_context={
                "audit_event_id": "audit_event_test",
                "table_name": "monthly_inputs",
                "change_result": {"inserted": 0, "updated": 0, "deleted": 1},
                "edit_reason": "Removed duplicate month",
            },
        )

        self.assertIn("SECTION,change_summary", csv_text)
        self.assertIn("audit_event_id,audit_event_test", csv_text)
        self.assertIn("table_name,monthly_inputs", csv_text)
        self.assertIn("deleted,1", csv_text)
        self.assertIn("edit_reason,Removed duplicate month", csv_text)
        self.assertIn("SECTION,monthly_inputs", csv_text)


if __name__ == "__main__":
    unittest.main()
