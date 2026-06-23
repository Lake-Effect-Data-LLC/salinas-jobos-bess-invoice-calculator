import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.db import get_engine
from app.db.import_csv import import_project_csvs
from app.settings import load_settings
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
        counts = import_project_csvs(
            engine,
            project_id=project["project_id"],
            project_name=project["project_name"],
            data_dir=project["data_folder"],
            dataset_name=args.dataset,
            replace=not args.append,
        )
        print(f"Imported {project_id}/{args.dataset}: {counts}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import existing project CSV inputs into Postgres."
    )
    parser.add_argument(
        "project_id",
        nargs="?",
        help="Project id from data/projects.csv. Defaults to all projects.",
    )
    parser.add_argument(
        "--dataset",
        default="actual",
        help="Dataset config name to import into. Defaults to actual.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append rows instead of replacing existing rows for the dataset.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
