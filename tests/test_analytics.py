import unittest

from app.components.analytics import build_analytics_trend_frames


class AnalyticsTrendFrameTest(unittest.TestCase):
    def test_builds_chronological_financial_and_generation_frames(self):
        runs = [
            {
                "snapshot_month": "2026-03-01",
                "snapshot_data": {
                    "latest_month_summary": {
                        "timestamp_month": "2026-03-01",
                        "MP": 300,
                        "MFP": 330,
                        "MCC": 102,
                        "FAA": 0.98,
                        "PRA": 0.95,
                    }
                },
            },
            {
                "snapshot_month": "2026-02-01",
                "snapshot_data": {
                    "latest_month_summary": {
                        "timestamp_month": "2026-02-01",
                        "MP": 200,
                        "MFP": 220,
                        "MCC": 101,
                        "FAA": 0.99,
                        "PRA": 0.96,
                    }
                },
            },
        ]

        financial_df, generation_df = build_analytics_trend_frames(runs)

        self.assertEqual(list(financial_df.index), ["2026-02-01", "2026-03-01"])
        self.assertEqual(list(financial_df.columns), ["MP", "MFP"])
        self.assertEqual(financial_df.loc["2026-02-01", "MP"], 200.0)
        self.assertEqual(financial_df.loc["2026-03-01", "MFP"], 330.0)

        self.assertEqual(list(generation_df.columns), ["MCC", "FAA %", "PRA %"])
        self.assertEqual(generation_df.loc["2026-02-01", "MCC"], 101.0)
        self.assertEqual(generation_df.loc["2026-02-01", "FAA %"], 99.0)
        self.assertEqual(generation_df.loc["2026-03-01", "PRA %"], 95.0)

    def test_skips_empty_metric_rows(self):
        financial_df, generation_df = build_analytics_trend_frames(
            [
                {
                    "snapshot_month": "2026-01-01",
                    "snapshot_data": {"latest_month_summary": {}},
                }
            ]
        )

        self.assertTrue(financial_df.empty)
        self.assertTrue(generation_df.empty)


if __name__ == "__main__":
    unittest.main()
