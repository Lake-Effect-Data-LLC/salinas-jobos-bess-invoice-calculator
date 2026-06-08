import argparse
import csv
from pathlib import Path

from compensation_calculator import calculate_monthly_results
from data_reader import (
    load_bess_inputs,
    load_monthly_performance_guarantee_inputs,
    load_performance_tests,
)
from data_writer import write_bess_monthly_results
from error_checks import input_validation
from report import generate_bess_invoice_support_report

import pandas as pd


DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
PROJECTS_CSV = DATA_DIR / "projects.csv"


def main(project_id=None):
    project = load_project(project_id or "salinas")
    project_data_dir = Path(project["data_folder"])
    project_output_dir = Path(project["output_folder"])

    contract_values_csv = project_data_dir / "bess_contract_values_template.csv"
    yearly_inputs_csv = project_data_dir / "bess_yearly_inputs_template.csv"
    monthly_inputs_csv = project_data_dir / "bess_monthly_inputs_template.csv"
    monthly_performance_guarantee_csv = (
        project_data_dir / "Monthly_Performance_Guarantee.csv"
    )
    performance_tests_csv = project_data_dir / "Performance_Tests.csv"

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
    monthly_performance_guarantee_inputs = load_monthly_performance_guarantee_inputs(
        monthly_performance_guarantee_csv
    )
    performance_tests = load_performance_tests(performance_tests_csv)
    monthly_results = calculate_monthly_results(
        contract_values,
        yearly_inputs,
        monthly_inputs,
        performance_tests,
        monthly_performance_guarantee_inputs,
    )
    output_path = write_bess_monthly_results(
        monthly_results,
        output_dir=project_output_dir,
    )
    report_path = project_output_dir / "report.txt"
    monthly_results_df = pd.read_csv(output_path)
    generate_bess_invoice_support_report(monthly_results_df, report_path)

    print(f"Project: {project['project_name']} ({project['project_id']})")
    print("BESS input files passed validation.")
    print(f"Wrote monthly results to {output_path}.")
    print(f"Wrote invoice support report to {report_path}.")
    for result in monthly_results:
        print(
            f"{result.timestamp_month}: "
            f"agreement_year={result.agreement_year}, "
            f"MP=${result.mp:,.2f}"
        )


def load_project(project_id):
    projects = load_projects(PROJECTS_CSV)
    try:
        return projects[project_id]
    except KeyError as exc:
        available_projects = ", ".join(sorted(projects))
        raise ValueError(
            f"Unknown project_id '{project_id}'. Available projects: {available_projects}"
        ) from exc


def load_projects(projects_csv):
    with projects_csv.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return {row["project_id"]: row for row in reader}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate BESS monthly invoice results for a project."
    )
    parser.add_argument(
        "project_id",
        nargs="?",
        default="salinas",
        help="Project id from data/projects.csv. Defaults to salinas.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.project_id)
