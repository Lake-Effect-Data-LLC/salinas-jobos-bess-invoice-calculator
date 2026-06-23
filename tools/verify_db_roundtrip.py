import argparse
import sys
from dataclasses import asdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.db import get_engine
from app.db.import_csv import import_project_csvs
from app.db.readers import (
    load_bess_inputs_from_db,
    load_monthly_performance_guarantee_inputs_from_db,
    load_performance_tests_from_db,
)
from app.settings import load_settings
from compensation_calculator import calculate_monthly_results
from data_reader import (
    load_bess_inputs,
    load_monthly_performance_guarantee_inputs,
    load_performance_tests,
)
from main import load_projects


PROJECTS_CSV = Path("data") / "projects.csv"


def main():
    args = parse_args()
    projects = load_projects(PROJECTS_CSV)
    settings = load_settings()
    engine = get_engine(settings.database.url)

    selected_project_ids = [args.project_id] if args.project_id else sorted(projects)
    for project_id in selected_project_ids:
        project = projects[project_id]
        _import_project(engine, project, args.dataset)
        csv_results = _calculate_from_csv(project)
        db_results = _calculate_from_db(engine, project_id, args.dataset)
        _assert_results_match(project_id, csv_results, db_results)
        print(f"{project_id}/{args.dataset}: DB-backed results match CSV-backed results")


def _import_project(engine, project, dataset_name):
    import_project_csvs(
        engine,
        project_id=project["project_id"],
        project_name=project["project_name"],
        data_dir=project["data_folder"],
        dataset_name=dataset_name,
        replace=True,
    )


def _calculate_from_csv(project):
    data_dir = Path(project["data_folder"])
    contract_values, yearly_inputs, monthly_inputs = load_bess_inputs(
        data_dir / "bess_contract_values_template.csv",
        data_dir / "bess_yearly_inputs_template.csv",
        data_dir / "bess_monthly_inputs_template.csv",
    )
    monthly_performance_guarantee_inputs = load_monthly_performance_guarantee_inputs(
        data_dir / "Monthly_Performance_Guarantee.csv"
    )
    performance_tests = load_performance_tests(data_dir / "Performance_Tests.csv")
    return calculate_monthly_results(
        contract_values,
        yearly_inputs,
        monthly_inputs,
        performance_tests,
        monthly_performance_guarantee_inputs,
    )


def _calculate_from_db(engine, project_id, dataset_name):
    contract_values, yearly_inputs, monthly_inputs = load_bess_inputs_from_db(
        engine,
        project_id,
        dataset_name,
    )
    monthly_performance_guarantee_inputs = (
        load_monthly_performance_guarantee_inputs_from_db(
            engine,
            project_id,
            dataset_name,
        )
    )
    performance_tests = load_performance_tests_from_db(
        engine,
        project_id,
        dataset_name,
    )
    return calculate_monthly_results(
        contract_values,
        yearly_inputs,
        monthly_inputs,
        performance_tests,
        monthly_performance_guarantee_inputs,
    )


def _assert_results_match(project_id, csv_results, db_results):
    if len(csv_results) != len(db_results):
        raise AssertionError(
            f"{project_id}: result count differs: CSV={len(csv_results)} DB={len(db_results)}"
        )

    for csv_result, db_result in zip(csv_results, db_results):
        csv_data = asdict(csv_result)
        db_data = asdict(db_result)
        for key, csv_value in csv_data.items():
            db_value = db_data[key]
            if isinstance(csv_value, float) or isinstance(db_value, float):
                if abs((csv_value or 0.0) - (db_value or 0.0)) > 0.000001:
                    raise AssertionError(
                        f"{project_id} {csv_result.timestamp_month} {key}: "
                        f"CSV={csv_value} DB={db_value}"
                    )
            elif csv_value != db_value:
                raise AssertionError(
                    f"{project_id} {csv_result.timestamp_month} {key}: "
                    f"CSV={csv_value} DB={db_value}"
                )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Verify DB-backed calculations match CSV-backed calculations."
    )
    parser.add_argument(
        "project_id",
        nargs="?",
        help="Project id from data/projects.csv. Defaults to all projects.",
    )
    parser.add_argument(
        "--dataset",
        default="actual",
        help="Dataset config name to import/read. Defaults to actual.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
