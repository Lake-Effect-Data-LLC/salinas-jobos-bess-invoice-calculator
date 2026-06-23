from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.components.banner import render_banner
from app.components.db_tables import render_database_table_views
from app.components.results import monthly_results_to_dataframe, render_results
from app.db import (
    check_connection,
    create_dataset_config,
    get_dataset_row_counts,
    get_engine,
    list_dataset_configs,
)
from app.db.readers import (
    load_bess_inputs_from_db,
    load_monthly_performance_guarantee_inputs_from_db,
    load_performance_tests_from_db,
)
from app.settings import load_settings
from compensation_calculator import calculate_monthly_results
from main import load_projects
from report import generate_bess_invoice_support_report


PROJECTS_CSV = ROOT_DIR / "data" / "projects.csv"
BANNER_IMAGE = ROOT_DIR / "assets" / "puerto_rico_flag_banner.png"
CREATE_DATASET_OPTION = "+ Create Dataset / Scenario"
START_WITH_CONTRACT_VALUES = "Start with contract values only"
COPY_EXISTING_DATASET = "Copy existing dataset"

ROW_COUNT_LABELS = {
    "contract_values": "Contract values",
    "yearly_inputs": "Yearly inputs",
    "monthly_inputs": "Monthly inputs",
    "monthly_performance_guarantee": "Monthly performance guarantee",
    "performance_tests": "Performance tests",
}


st.set_page_config(
    page_title="BESS Invoice Calculator",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        min-width: 25rem;
        width: 25rem;
    }

    [data-testid="stSidebar"] > div:first-child {
        min-width: 25rem;
        width: 25rem;
    }

    .app-banner {
        position: relative;
        left: 50%;
        width: calc(100vw - 25rem - 4rem);
        max-width: none;
        height: 11rem;
        margin: -1.25rem 0 1.75rem calc(-50vw + 12.5rem + 2rem);
        overflow: hidden;
        border-radius: 0;
    }

    .app-banner img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center 44%;
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    render_banner(BANNER_IMAGE)
    st.title("BESS Invoice Calculator")

    projects = load_available_projects()
    project_id = st.sidebar.radio(
        "Facility",
        options=list(projects),
        format_func=lambda value: projects[value]["project_name"],
    )
    project = projects[project_id]
    project_name = project["project_name"]
    render_database_flow(project_id, project_name)


def render_database_flow(project_id, project_name):
    st.subheader("Database Source")

    try:
        settings = load_settings()
        engine = get_engine(settings.database.url)
        check_connection(engine)
        datasets = list_dataset_configs(engine, project_id)
    except Exception as exc:
        st.error(f"Could not connect to Postgres: {exc}")
        return

    dataset_names = [dataset["name"] for dataset in datasets]
    if not datasets:
        st.warning(f"No datasets found for facility `{project_id}`.")
        render_create_dataset_toggle(engine, project_id, datasets)
        return

    preferred_dataset_name = st.session_state.pop(
        f"selected-dataset-{project_id}",
        None,
    )
    default_index = next(
        (
            index
            for index, dataset_name in enumerate(dataset_names)
            if dataset_name == preferred_dataset_name
        ),
        None,
    )
    if default_index is None:
        default_index = next(
        (
            index
            for index, dataset in enumerate(datasets)
            if dataset.get("is_default")
        ),
        0,
    )
    selected_dataset_option = st.sidebar.selectbox(
        "Dataset / Scenario",
        options=[*dataset_names, CREATE_DATASET_OPTION],
        index=default_index,
    )

    if selected_dataset_option == CREATE_DATASET_OPTION:
        render_create_dataset_panel(engine, project_id, datasets, force_visible=True)
        return

    dataset_name = selected_dataset_option

    try:
        row_counts = get_dataset_row_counts(engine, project_id, dataset_name)
    except Exception as exc:
        st.error(f"Could not read dataset status: {exc}")
        return

    st.caption(f"Facility: `{project_id}` · Dataset / Scenario: `{dataset_name}`")
    st.dataframe(
        [
            {
                "table": ROW_COUNT_LABELS.get(table_name, table_name),
                "rows": row_count,
            }
            for table_name, row_count in row_counts.items()
        ],
        use_container_width=True,
        hide_index=True,
    )

    if any(row_count == 0 for row_count in row_counts.values()):
        st.warning("One or more input tables are empty for this dataset.")

    render_database_table_views(engine, project_id, dataset_name)

    st.subheader("Run")
    run_clicked = st.button("Run Calculation", type="primary")
    if not run_clicked:
        return

    try:
        results_df, report_text = run_calculation_from_db(
            engine,
            project_id,
            dataset_name,
            project_name,
        )
    except ValueError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Database calculation failed: {exc}")
        return

    render_results(results_df, report_text)


def render_create_dataset_toggle(engine, project_id, datasets):
    if st.sidebar.button("+ Create Dataset / Scenario", key=f"show-create-dataset-{project_id}"):
        st.session_state[f"create-dataset-visible-{project_id}"] = True
    render_create_dataset_panel(engine, project_id, datasets)


def render_create_dataset_panel(engine, project_id, datasets, force_visible=False):
    toggle_key = f"create-dataset-visible-{project_id}"
    if not force_visible and not st.session_state.get(toggle_key, False):
        return

    dataset_names = [dataset["name"] for dataset in datasets]
    with st.sidebar.container(border=True):
        st.markdown("**Create Dataset / Scenario**")
        st.caption(
            "A dataset is a named version of a facility's inputs, such as "
            "`actual`, `testing`, or `scenario_1`."
        )
        with st.form(f"create-dataset-{project_id}"):
            dataset_name = st.text_input("Name", placeholder="testing")
            start_from = st.radio(
                "Start from",
                options=[START_WITH_CONTRACT_VALUES, COPY_EXISTING_DATASET],
                help=(
                    "New scenarios start with the facility's contract values so "
                    "the Contract values table is populated immediately."
                ),
            )
            base_dataset_name = None
            if start_from == COPY_EXISTING_DATASET:
                if not dataset_names:
                    st.warning("No existing datasets are available to copy.")
                else:
                    base_dataset_name = st.selectbox(
                        "Base dataset",
                        options=dataset_names,
                    )
            submitted = st.form_submit_button("Create")

        if not submitted:
            return

        if start_from == COPY_EXISTING_DATASET and not base_dataset_name:
            st.error("Choose a base dataset before creating a copy.")
            return

        try:
            created_name = create_dataset_config(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                description=(
                    f"Created from {base_dataset_name}" if base_dataset_name else ""
                ),
                copy_from_dataset_name=base_dataset_name,
            )
            row_counts = get_dataset_row_counts(engine, project_id, created_name)
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not create dataset / scenario: {exc}")
        else:
            contract_value_count = row_counts.get("contract_values", 0)
            st.success(
                f"Created dataset / scenario `{created_name}` with "
                f"{contract_value_count} contract value rows."
            )
            st.session_state[f"selected-dataset-{project_id}"] = created_name
            st.rerun()


def load_available_projects():
    if PROJECTS_CSV.exists():
        return load_projects(PROJECTS_CSV)

    return {
        "salinas": {
            "project_id": "salinas",
            "project_name": "Salinas BESS",
            "data_folder": "data/salinas",
        },
        "jobos": {
            "project_id": "jobos",
            "project_name": "Jobos BESS",
            "data_folder": "data/jobos",
        },
    }


def run_calculation_from_db(engine, project_id, dataset_name, project_name):
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

    return run_calculation_from_inputs(
        contract_values,
        yearly_inputs,
        monthly_inputs,
        performance_tests,
        monthly_performance_guarantee_inputs,
        project_name,
    )


def run_calculation_from_inputs(
    contract_values,
    yearly_inputs,
    monthly_inputs,
    performance_tests,
    monthly_performance_guarantee_inputs,
    project_name,
):
    monthly_results = calculate_monthly_results(
        contract_values,
        yearly_inputs,
        monthly_inputs,
        performance_tests,
        monthly_performance_guarantee_inputs,
    )
    results_df = monthly_results_to_dataframe(monthly_results)
    with TemporaryDirectory() as temp_dir:
        report_path = Path(temp_dir) / "report.txt"
        report_text = generate_bess_invoice_support_report(
            results_df,
            report_path,
            project_name=project_name,
        )
    return results_df, report_text


if __name__ == "__main__":
    main()
