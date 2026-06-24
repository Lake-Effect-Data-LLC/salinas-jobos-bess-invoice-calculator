import unittest

import pandas as pd

from app.components.results import build_run_snapshot_data


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

        snapshot_data = build_run_snapshot_data(results_df, "report text")

        self.assertEqual(
            snapshot_data["latest_month_summary"]["timestamp_month"],
            "2026-02-01",
        )
        self.assertEqual(snapshot_data["latest_month_summary"]["MP"], 1000.25)
        self.assertIn("2026-01-01", snapshot_data["csv_text"])
        self.assertIn("2026-02-01", snapshot_data["csv_text"])
        self.assertEqual(snapshot_data["report_text"], "report text")

    def test_build_run_snapshot_data_rejects_empty_results(self):
        with self.assertRaisesRegex(ValueError, "empty calculation results"):
            build_run_snapshot_data(pd.DataFrame(), "report text")


if __name__ == "__main__":
    unittest.main()
