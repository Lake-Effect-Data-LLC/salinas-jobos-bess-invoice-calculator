import csv
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from compensation_calculator import calculate_monthly_results
from data_reader import (
    load_bess_inputs,
    load_monthly_performance_guarantee_inputs,
    load_performance_tests,
)
from data_writer import BESS_MONTHLY_RESULT_COLUMNS, write_bess_monthly_results
from error_checks import input_validation
from report import generate_bess_invoice_support_report


SCENARIOS = [
    ("scenario_1_baseline", "Scenario 1 - Baseline", "scenario_1_report.txt"),
    ("scenario_2_fa_band", "Scenario 2 - FA Band", "scenario_2_report.txt"),
    ("scenario_3_pohrs_cap", "Scenario 3 - POHRS Cap", "scenario_3_report.txt"),
    ("scenario_4_gse_cap", "Scenario 4 - GSE Cap", "scenario_4_report.txt"),
    (
        "scenario_5_cld_month_boundary",
        "Scenario 5 - CLD Month Boundary",
        "scenario_5_report.txt",
    ),
    ("scenario_6_all_lds", "Scenario 6 - All LDs", "scenario_6_report.txt"),
]

DATA_DIR = ROOT_DIR / "data" / "validation"
OUTPUT_DIR = ROOT_DIR / "output" / "validation"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    aggregate_rows = []

    for scenario_dir_name, scenario_name, report_filename in SCENARIOS:
        scenario_dir = DATA_DIR / scenario_dir_name
        output_dir = OUTPUT_DIR / scenario_dir_name

        contract_values_csv = scenario_dir / "bess_contract_values.csv"
        yearly_inputs_csv = scenario_dir / "bess_yearly_inputs.csv"
        monthly_inputs_csv = scenario_dir / "bess_monthly_inputs.csv"
        monthly_performance_guarantee_csv = (
            scenario_dir / "Monthly_Performance_Guarantee.csv"
        )
        performance_tests_csv = scenario_dir / "Performance_Tests.csv"

        input_validation(
            contract_values_csv,
            yearly_inputs_csv,
            monthly_inputs_csv,
            monthly_performance_guarantee_csv,
            performance_tests_csv,
        )

        contract_values, yearly_inputs, monthly_inputs = load_bess_inputs(
            contract_values_csv,
            yearly_inputs_csv,
            monthly_inputs_csv,
        )
        monthly_performance_guarantee_inputs = (
            load_monthly_performance_guarantee_inputs(
                monthly_performance_guarantee_csv
            )
        )
        performance_tests = load_performance_tests(performance_tests_csv)
        monthly_results = calculate_monthly_results(
            contract_values,
            yearly_inputs,
            monthly_inputs,
            performance_tests,
            monthly_performance_guarantee_inputs,
        )

        scenario_csv = write_bess_monthly_results(
            monthly_results,
            output_dir=output_dir,
        )
        results_df = pd.read_csv(scenario_csv)
        generate_bess_invoice_support_report(
            results_df,
            OUTPUT_DIR / report_filename,
            project_name=scenario_name,
        )

        for row in csv.DictReader(scenario_csv.open(newline="")):
            aggregate_rows.append(
                {
                    "scenario": scenario_dir_name,
                    "scenario_name": scenario_name,
                    **row,
                }
            )

        print(f"{scenario_name}: wrote {len(monthly_results)} result row(s)")

    aggregate_columns = [
        "scenario",
        "scenario_name",
        *BESS_MONTHLY_RESULT_COLUMNS,
    ]
    aggregate_csv = OUTPUT_DIR / "bess_monthly_results.csv"
    with aggregate_csv.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=aggregate_columns)
        writer.writeheader()
        writer.writerows(aggregate_rows)

    print(f"Wrote aggregate validation results to {aggregate_csv}")


if __name__ == "__main__":
    main()
