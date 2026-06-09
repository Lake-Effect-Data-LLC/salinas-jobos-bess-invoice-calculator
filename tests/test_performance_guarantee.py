import unittest
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

from calculations import (
    calculate_FA,
    calculate_FA_with_included_POHRS,
    calculate_FAA,
    calculate_included_GSEHRS,
    calculate_risk_adjustment_with_waiting_periods,
    calculate_capability_liquidated_damages_per_day,
    calculate_degraded_duration_energy,
    calculate_efficiency_liquidated_damages,
    calculate_liquidated_damages_rate,
)
from classes import (
    BessContractValues,
    BessMonthlyInputs,
    BessPerformanceTest,
    BessYearlyInputs,
)
from compensation_calculator import (
    calculate_monthly_capability_liquidated_damages,
    calculate_monthly_results,
)
from error_checks import validate_input_files
from report import generate_bess_invoice_support_report

import pandas as pd

from classes import BessMonthlyResult
from data_reader import load_contract_values
from data_reader import load_performance_tests


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
            prepa_approved=True,
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

    def test_open_ended_failed_test_accrues_cld_through_billing_period_end(self):
        failed_test = BessPerformanceTest(
            test_id="FAIL-OPEN",
            agreement_year=1,
            test_type="PREPA Performance Test",
            test_date="2026-01-15",
            requested_by="PREPA",
            tde=390.0,
            measured_ramp_rate=6000.0,
            prepa_approved=True,
        )

        cld_per_day = calculate_capability_liquidated_damages_per_day(
            GC=400.0,
            TDE=390.0,
            RER=170.0,
            CPP=25096.0,
        )

        self.assertAlmostEqual(
            calculate_monthly_capability_liquidated_damages(
                timestamp_month="2026-01",
                agreement_year=1,
                performance_tests=[failed_test],
                dde=400.0,
                rer=170.0,
                cpp=25096.0,
            ),
            cld_per_day * 17,
        )

    def test_cld_ends_on_next_approved_passing_retest_row(self):
        failed_test = BessPerformanceTest(
            test_id="FAIL-1",
            agreement_year=1,
            test_type="PREPA Performance Test",
            test_date="2026-03-12",
            requested_by="PREPA",
            tde=390.0,
            measured_ramp_rate=6000.0,
            prepa_approved=True,
        )
        passing_retest = BessPerformanceTest(
            test_id="PASS-1",
            agreement_year=1,
            test_type="Resource Provider Performance Test",
            test_date="2026-04-08",
            requested_by="Resource Provider",
            tde=401.0,
            measured_ramp_rate=6000.0,
            prepa_approved=True,
            replaces_test_id="FAIL-1",
        )

        cld_per_day = calculate_capability_liquidated_damages_per_day(
            GC=400.0,
            TDE=390.0,
            RER=170.0,
            CPP=25096.0,
        )

        self.assertAlmostEqual(
            calculate_monthly_capability_liquidated_damages(
                timestamp_month="2026-03",
                agreement_year=1,
                performance_tests=[failed_test, passing_retest],
                dde=400.0,
                rer=170.0,
                cpp=25096.0,
            ),
            cld_per_day * 20,
        )
        self.assertAlmostEqual(
            calculate_monthly_capability_liquidated_damages(
                timestamp_month="2026-04",
                agreement_year=1,
                performance_tests=[failed_test, passing_retest],
                dde=400.0,
                rer=170.0,
                cpp=25096.0,
            ),
            cld_per_day * 7,
        )

    def test_unapproved_failed_test_does_not_accrue_cld(self):
        failed_test = BessPerformanceTest(
            test_id="FAIL-DRAFT",
            agreement_year=1,
            test_type="PREPA Performance Test",
            test_date="2026-01-15",
            requested_by="PREPA",
            tde=390.0,
            measured_ramp_rate=6000.0,
            prepa_approved=False,
            cure_or_retest_date="2026-01-20",
        )

        self.assertEqual(
            calculate_monthly_capability_liquidated_damages(
                timestamp_month="2026-01",
                agreement_year=1,
                performance_tests=[failed_test],
                dde=400.0,
                rer=170.0,
                cpp=25096.0,
                cld_uses_dde_multiplier=True,
            ),
            0.0,
        )

    def test_cld_can_use_gc_separate_from_dde(self):
        failed_test = BessPerformanceTest(
            test_id="FAIL-GC",
            agreement_year=1,
            test_type="PREPA Performance Test",
            test_date="2026-01-15",
            requested_by="PREPA",
            tde=390.0,
            measured_ramp_rate=6000.0,
            prepa_approved=True,
            cure_or_retest_date="2026-01-20",
        )

        cld_per_day = calculate_capability_liquidated_damages_per_day(
            GC=395.0,
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
                gc=395.0,
            ),
            cld_per_day * 5,
        )

    def test_cld_gc_passing_retest_stops_accrual_below_raw_dde(self):
        failed_test = BessPerformanceTest(
            test_id="FAIL-GC",
            agreement_year=1,
            test_type="PREPA Performance Test",
            test_date="2026-01-15",
            requested_by="PREPA",
            tde=390.0,
            measured_ramp_rate=6000.0,
            prepa_approved=True,
        )
        passing_retest = BessPerformanceTest(
            test_id="PASS-GC",
            agreement_year=1,
            test_type="Resource Provider Performance Test",
            test_date="2026-01-20",
            requested_by="Resource Provider",
            tde=396.0,
            measured_ramp_rate=6000.0,
            prepa_approved=True,
            replaces_test_id="FAIL-GC",
        )

        cld_per_day = calculate_capability_liquidated_damages_per_day(
            GC=395.0,
            TDE=390.0,
            RER=170.0,
            CPP=25096.0,
            DDE=400.0,
        )

        self.assertAlmostEqual(
            calculate_monthly_capability_liquidated_damages(
                timestamp_month="2026-01",
                agreement_year=1,
                performance_tests=[failed_test, passing_retest],
                dde=400.0,
                rer=170.0,
                cpp=25096.0,
                cld_uses_dde_multiplier=True,
                gc=395.0,
            ),
            cld_per_day * 5,
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

    def test_waiting_period_allowance_can_be_contract_specific(self):
        self.assertEqual(
            calculate_included_GSEHRS(
                GSEHRS=90.0,
                prior_GSEHRS=0.0,
                annual_allowance_hours=80.0,
            ),
            80.0,
        )
        self.assertEqual(
            calculate_included_GSEHRS(
                GSEHRS=90.0,
                prior_GSEHRS=0.0,
                annual_allowance_hours=100.0,
            ),
            90.0,
        )

    def test_pra_uses_contract_specific_waiting_periods(self):
        self.assertAlmostEqual(
            calculate_risk_adjustment_with_waiting_periods(
                BPHRS=100.0,
                GSEHRS=90.0,
                PFMHRS=0.0,
                IPHRS=0.0,
                prior_GSEHRS=0.0,
                prior_PFMHRS=0.0,
                grid_system_waiting_period_hours=80.0,
                force_majeure_waiting_period_hours=720.0,
            ),
            0.2,
        )
        self.assertAlmostEqual(
            calculate_risk_adjustment_with_waiting_periods(
                BPHRS=100.0,
                GSEHRS=90.0,
                PFMHRS=0.0,
                IPHRS=0.0,
                prior_GSEHRS=0.0,
                prior_PFMHRS=0.0,
                grid_system_waiting_period_hours=100.0,
                force_majeure_waiting_period_hours=720.0,
            ),
            0.1,
        )

    def test_dde_derives_from_design_duration_energy_and_degradation_rate(self):
        self.assertAlmostEqual(
            calculate_degraded_duration_energy(
                design_duration_energy=400.0,
                annual_duration_energy_degradation_rate=0.0,
                agreement_year=5,
            ),
            400.0,
        )
        self.assertAlmostEqual(
            calculate_degraded_duration_energy(
                design_duration_energy=400.0,
                annual_duration_energy_degradation_rate=0.01,
                agreement_year=3,
            ),
            392.04,
        )

    def test_monthly_results_validate_dde_against_contract_values(self):
        contract_values = {
            1: BessContractValues(
                agreement_year=1,
                cppf=23696.0,
                cpppif=1200.0,
                ddd=4.0,
                design_duration_energy=400.0,
                annual_duration_energy_degradation_rate=0.0,
            )
        }
        yearly_inputs = {
            1: BessYearlyInputs(
                agreement_year=1,
                dde=399.0,
                tr=100.0,
            )
        }
        monthly_inputs = [
            BessMonthlyInputs(
                timestamp_month="2026-01",
                agreement_year=1,
                adj=0.0,
                bphrs=744.0,
                pohrs=0.0,
                unavhrs=0.0,
                unavprodhrs=0.0,
                gse=0.0,
                pfm=0.0,
                ip=0.0,
            )
        ]

        with self.assertRaisesRegex(ValueError, "derived DDE=400.00"):
            calculate_monthly_results(
                contract_values,
                yearly_inputs,
                monthly_inputs,
            )

    def test_contract_values_validation_requires_ld_formula_columns(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bess_contract_values_template.csv"
            path.write_text("agreement_year,cppf,cpppif,DDD\n1,1,1,4\n")

            with self.assertRaisesRegex(
                ValueError,
                "CLD_uses_DDE_multiplier",
            ):
                validate_input_files([path])

    def test_performance_test_loader_reads_ramp_outage_fields(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Performance_Tests.csv"
            path.write_text(
                "test_id,agreement_year,test_type,test_date,requested_by,TDE,"
                "measured_ramp_rate,certified_by,prepa_approved,approval_date,"
                "cure_or_retest_date,replaces_test_id,ramp_failure_caused_outage,"
                "outage_start,outage_end,outage_equivalent_unavhrs,"
                "source_reference,notes\n"
                "RAMP-1,1,PREPA Performance Test,2026-01-15,PREPA,400,"
                "3000,Independent,TRUE,2026-01-20,,,TRUE,"
                "2026-01-15,2026-01-17,48,Appendix P Section 4,"
                "Ramp failure outage\n"
            )

            performance_test = load_performance_tests(path)[0]

            self.assertTrue(performance_test.ramp_failure_caused_outage)
            self.assertEqual(performance_test.outage_start, "2026-01-15")
            self.assertEqual(performance_test.outage_end, "2026-01-17")
            self.assertEqual(performance_test.outage_equivalent_unavhrs, 48.0)

    def test_performance_test_loader_rejects_invalid_optional_bool(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Performance_Tests.csv"
            path.write_text(
                "test_id,agreement_year,test_type,test_date,requested_by,TDE,"
                "measured_ramp_rate,certified_by,prepa_approved,approval_date,"
                "cure_or_retest_date,replaces_test_id,ramp_failure_caused_outage,"
                "outage_start,outage_end,outage_equivalent_unavhrs,"
                "source_reference,notes\n"
                "TEST-1,1,PREPA Performance Test,2026-01-15,PREPA,400,"
                "6000,Independent,Trye,2026-01-20,,,FALSE,"
                ",,,Appendix P Section 2,Typo should fail\n"
            )

            with self.assertRaisesRegex(ValueError, "prepa_approved"):
                load_performance_tests(path)

    def test_performance_test_loader_rejects_invalid_ramp_bool(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Performance_Tests.csv"
            path.write_text(
                "test_id,agreement_year,test_type,test_date,requested_by,TDE,"
                "measured_ramp_rate,certified_by,prepa_approved,approval_date,"
                "cure_or_retest_date,replaces_test_id,ramp_failure_caused_outage,"
                "outage_start,outage_end,outage_equivalent_unavhrs,"
                "source_reference,notes\n"
                "TEST-1,1,PREPA Performance Test,2026-01-15,PREPA,400,"
                "6000,Independent,TRUE,2026-01-20,,,Flase,"
                ",,,Appendix P Section 4,Typo should fail\n"
            )

            with self.assertRaisesRegex(ValueError, "ramp_failure_caused_outage"):
                load_performance_tests(path)

    def test_ramp_failure_outage_requires_outage_fields(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Performance_Tests.csv"
            path.write_text(
                "test_id,agreement_year,test_type,test_date,requested_by,TDE,"
                "measured_ramp_rate,certified_by,prepa_approved,approval_date,"
                "cure_or_retest_date,replaces_test_id,ramp_failure_caused_outage,"
                "outage_start,outage_end,outage_equivalent_unavhrs,"
                "source_reference,notes\n"
                "RAMP-1,1,PREPA Performance Test,2026-01-15,PREPA,400,"
                "3000,Independent,TRUE,2026-01-20,,,TRUE,"
                ",2026-01-17,48,Appendix P Section 4,Ramp failure outage\n"
            )

            with self.assertRaisesRegex(ValueError, "outage_start"):
                validate_input_files([path])

    def test_blank_required_contract_field_raises(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bess_contract_values_template.csv"
            # TA cell is intentionally blank
            path.write_text(
                "agreement_year,cppf,cpppif,DDD,TA,RER,GE,"
                "CLD_uses_DDE_multiplier,ELD_uses_CE_times_GE,"
                "design_dmax,design_duration_energy,"
                "annual_duration_energy_degradation_rate,design_charge_energy,"
                "grid_system_waiting_period_hours,force_majeure_waiting_period_hours,"
                "scheduled_maintenance_allowance_hours\n"
                "1,25000,1200,4,,170,0.97,FALSE,TRUE,100,400,0,400,80,720,160\n"
            )

            with self.assertRaisesRegex(ValueError, "TA"):
                load_contract_values(path)

    def test_contract_values_loader_rejects_invalid_required_bool(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bess_contract_values_template.csv"
            path.write_text(
                "agreement_year,cppf,cpppif,DDD,TA,RER,GE,"
                "CLD_uses_DDE_multiplier,ELD_uses_CE_times_GE,"
                "design_dmax,design_duration_energy,"
                "annual_duration_energy_degradation_rate,design_charge_energy,"
                "grid_system_waiting_period_hours,force_majeure_waiting_period_hours,"
                "scheduled_maintenance_allowance_hours\n"
                "1,25000,1200,4,0.70,170,0.97,Flase,TRUE,"
                "100,400,0,400,80,720,160\n"
            )

            with self.assertRaisesRegex(ValueError, "CLD_uses_DDE_multiplier"):
                load_contract_values(path)

    def test_validation_warns_when_tr_not_carried_from_prior_year_failed_test(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            contract_path = temp_path / "bess_contract_values_template.csv"
            yearly_path = temp_path / "bess_yearly_inputs_template.csv"
            monthly_path = temp_path / "bess_monthly_inputs_template.csv"
            tests_path = temp_path / "Performance_Tests.csv"
            guarantee_path = temp_path / "Monthly_Performance_Guarantee.csv"

            contract_path.write_text(
                "agreement_year,cppf,cpppif,DDD,TA,RER,GE,"
                "CLD_uses_DDE_multiplier,ELD_uses_CE_times_GE,"
                "design_dmax,design_duration_energy,"
                "annual_duration_energy_degradation_rate,design_charge_energy,"
                "grid_system_waiting_period_hours,force_majeure_waiting_period_hours,"
                "scheduled_maintenance_allowance_hours\n"
                "1,25000,1200,4,0.70,170,0.85,TRUE,FALSE,"
                "100,400,0,468,80,720,160\n"
                "2,25500,1224,4,0.70,170,0.85,TRUE,FALSE,"
                "100,400,0,468,80,720,160\n"
            )
            yearly_path.write_text(
                "agreement_year,DDE,TR\n"
                "1,400,100\n"
                "2,400,100\n"
            )
            monthly_path.write_text(
                "timestamp_month,agreement_year,Other_ADJ,BPHRS,POHRS,"
                "UNAVHRS,UNAVPRODHRS,GSE,PFM,IP\n"
                "2027-01,2,0,744,0,0,0,0,0,0\n"
            )
            tests_path.write_text(
                "test_id,agreement_year,test_type,test_date,requested_by,TDE,"
                "measured_ramp_rate,certified_by,prepa_approved,approval_date,"
                "cure_or_retest_date,replaces_test_id,ramp_failure_caused_outage,"
                "outage_start,outage_end,outage_equivalent_unavhrs,"
                "source_reference,notes\n"
                "FAIL-Y1,1,PREPA Performance Test,2026-12-15,PREPA,380,"
                "6000,Independent,TRUE,2026-12-20,,,FALSE,"
                ",,,Appendix F Section 3,Year-end failed test\n"
            )
            guarantee_path.write_text(
                "timestamp_month,agreement_year,CE,DE,AE_beg,AE_end,notes\n"
            )

            with self.assertWarnsRegex(UserWarning, "Expected TR"):
                validate_input_files(
                    [
                        contract_path,
                        yearly_path,
                        monthly_path,
                        tests_path,
                        guarantee_path,
                    ]
                )

    def test_validation_accepts_tr_carried_from_prior_year_failed_test(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            contract_path = temp_path / "bess_contract_values_template.csv"
            yearly_path = temp_path / "bess_yearly_inputs_template.csv"
            tests_path = temp_path / "Performance_Tests.csv"

            contract_path.write_text(
                "agreement_year,cppf,cpppif,DDD,TA,RER,GE,"
                "CLD_uses_DDE_multiplier,ELD_uses_CE_times_GE,"
                "design_dmax,design_duration_energy,"
                "annual_duration_energy_degradation_rate,design_charge_energy,"
                "grid_system_waiting_period_hours,force_majeure_waiting_period_hours,"
                "scheduled_maintenance_allowance_hours\n"
                "1,25000,1200,4,0.70,170,0.85,TRUE,FALSE,"
                "100,400,0,468,80,720,160\n"
                "2,25500,1224,4,0.70,170,0.85,TRUE,FALSE,"
                "100,400,0,468,80,720,160\n"
            )
            yearly_path.write_text(
                "agreement_year,DDE,TR\n"
                "1,400,100\n"
                "2,400,95\n"
            )
            tests_path.write_text(
                "test_id,agreement_year,test_type,test_date,requested_by,TDE,"
                "measured_ramp_rate,certified_by,prepa_approved,approval_date,"
                "cure_or_retest_date,replaces_test_id,ramp_failure_caused_outage,"
                "outage_start,outage_end,outage_equivalent_unavhrs,"
                "source_reference,notes\n"
                "FAIL-Y1,1,PREPA Performance Test,2026-12-15,PREPA,380,"
                "6000,Independent,TRUE,2026-12-20,,,FALSE,"
                ",,,Appendix F Section 3,Year-end failed test\n"
            )

            with warnings.catch_warnings(record=True) as recorded_warnings:
                warnings.simplefilter("always")
                validate_input_files([contract_path, yearly_path, tests_path])
                self.assertEqual(recorded_warnings, [])

    def test_monthly_result_has_no_adj_alias(self):
        self.assertFalse(
            hasattr(BessMonthlyResult, "adj"),
            "BessMonthlyResult.adj alias should have been removed (QUALITY-6)",
        )

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
