import unittest

import pandas as pd

from app.services.table_editor import (
    _normalize_monthly_inputs_df,
    _normalize_monthly_performance_guarantee_df,
    _normalize_yearly_inputs_df,
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


if __name__ == "__main__":
    unittest.main()
