import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from calculations import (
    calculate_FA,
    calculate_FA_with_included_POHRS,
    calculate_FAA,
    calculate_capability_liquidated_damages_per_day,
    calculate_efficiency_liquidated_damages,
    calculate_liquidated_damages_rate,
)
from classes import BessPerformanceTest
from compensation_calculator import calculate_monthly_capability_liquidated_damages
from error_checks import validate_input_files
from report import generate_bess_invoice_support_report

import pandas as pd


class PerformanceGuaranteeTest(unittest.TestCase):
    def test_cld_per_day_uses_salinas_dde_multiplier(self):
        self.assertAlmostEqual(
            calculate_capability_liquidated_damages_per_day(
                GC=400.0,
                TDE=390.0,
                RER=170.0,
                CPP=25096.0,
                DDE=400.0,
            ),
            4000.0 * calculate_liquidated_damages_rate(170.0, 25096.0),
        )

    def test_cld_per_day_can_omit_jobos_dde_multiplier(self):
        self.assertAlmostEqual(
            calculate_capability_liquidated_damages_per_day(
                GC=400.0,
                TDE=390.0,
                RER=170.0,
                CPP=25096.0,
            ),
            10.0 * calculate_liquidated_damages_rate(170.0, 25096.0),
        )

    def test_cld_allocates_failed_test_days_inside_billing_period(self):
        failed_test = BessPerformanceTest(
            test_id="FAIL-1",
            agreement_year=1,
            test_type="PREPA Performance Test",
            test_date="2026-01-15",
            requested_by="PREPA",
            tde=390.0,
            measured_ramp_rate=6000.0,
            cure_or_retest_date="2026-01-20",
        )

        cld_per_day = calculate_capability_liquidated_damages_per_day(
            GC=400.0,
            TDE=390.0,
            RER=170.0,
            CPP=25096.0,
            DDE=400.0,
        )

        self.assertAlmostEqual(
            calculate_monthly_capability_liquidated_damages(
                timestamp_month="2026-01",
                agreement_year=1,
                performance_tests=[failed_test],
                dde=400.0,
                rer=170.0,
                cpp=25096.0,
                cld_uses_dde_multiplier=True,
            ),
            cld_per_day * 5,
        )

    def test_open_ended_failed_test_does_not_accrue_cld_without_end_date(self):
        failed_test = BessPerformanceTest(
            test_id="FAIL-OPEN",
            agreement_year=1,
            test_type="PREPA Performance Test",
            test_date="2026-01-15",
            requested_by="PREPA",
            tde=390.0,
            measured_ramp_rate=6000.0,
        )

        self.assertEqual(
            calculate_monthly_capability_liquidated_damages(
                timestamp_month="2026-01",
                agreement_year=1,
                performance_tests=[failed_test],
                dde=400.0,
                rer=170.0,
                cpp=25096.0,
            ),
            0.0,
        )

    def test_eld_uses_jobos_ce_times_ge_formula(self):
        self.assertAlmostEqual(
            calculate_efficiency_liquidated_damages(
                RER=170.0,
                CPP=25096.0,
                CE=100.0,
                GE=0.97,
                DE=95.0,
                actual_efficiency=0.95,
                uses_ce_times_ge=True,
            ),
            calculate_liquidated_damages_rate(170.0, 25096.0) * 2.0,
        )

    def test_eld_can_use_salinas_displayed_ce_minus_ge_formula(self):
        self.assertAlmostEqual(
            calculate_efficiency_liquidated_damages(
                RER=170.0,
                CPP=25096.0,
                CE=100.0,
                GE=0.97,
                DE=95.0,
                actual_efficiency=0.95,
                uses_ce_times_ge=False,
            ),
            calculate_liquidated_damages_rate(170.0, 25096.0) * 4.03,
        )

    def test_fa_helper_counts_excess_permitted_outage_as_unavailable(self):
        self.assertAlmostEqual(
            calculate_FA_with_included_POHRS(
                currentPOHRS=200.0,
                prior_POHRS=0.0,
                BPHRS=744.0,
                UNAVHRS=0.0,
                UNAVPRODHRS=0.0,
            ),
            calculate_FA(
                BPHRS=744.0,
                POHRS=160.0,
                UNAVHRS=40.0,
                UNAVPRODHRS=0.0,
            ),
        )

    def test_faa_at_exactly_70_percent_uses_last_nonzero_point(self):
        self.assertAlmostEqual(calculate_FAA(0.70), 0.44)

    def test_contract_values_validation_requires_ld_formula_columns(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bess_contract_values_template.csv"
            path.write_text("agreement_year,cppf,cpppif,DDD\n1,1,1,4\n")

            with self.assertRaisesRegex(
                ValueError,
                "CLD_uses_DDE_multiplier",
            ):
                validate_input_files([path])

    def test_report_header_uses_project_name(self):
        with TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "report.txt"
            results_df = pd.DataFrame(
                [
                    {
                        "timestamp_month": "2026-01",
                        "agreement_year": 1,
                        "CPP": 25096.0,
                        "MCC": 100.0,
                        "FA": 1.0,
                        "FAA": 1.0,
                        "PRA": 1.0,
                        "MFP": 2509600.0,
                        "Other_ADJ": 0.0,
                        "ALD": 0.0,
                        "CLD": 0.0,
                        "Actual_Efficiency": 0.97,
                        "ELD": 0.0,
                        "ADJ_Total": 0.0,
                        "MP": 2509600.0,
                    }
                ]
            )

            report_text = generate_bess_invoice_support_report(
                results_df,
                output_file,
                project_name="Jobos BESS",
            )

            self.assertIn("JOBOS BESS MONTHLY INVOICE SUPPORT REPORT", report_text)


if __name__ == "__main__":
    unittest.main()
