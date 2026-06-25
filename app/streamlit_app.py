from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.components.banner import render_banner
from app.components.analytics import render_analytics_summary
from app.components.db_tables import render_database_table_views
from app.components.results import (
    build_run_snapshot_data,
    monthly_results_to_dataframe,
    render_results,
)
from app.components.run_dashboard import render_run_history_dashboard
from app.db import (
    check_connection,
    create_dataset_config,
    delete_dataset_config,
    generate_calculation_snapshot_name,
    get_dataset_row_counts,
    get_engine,
    list_dataset_configs,
    record_calculation_run,
)
from app.db.readers import (
    load_bess_inputs_from_db,
    load_inputs_snapshot,
    load_monthly_performance_guarantee_inputs_from_db,
    load_performance_tests_from_db,
)
from app.settings import load_settings
from app.storage import (
    build_run_artifact_key,
    get_storage_client_from_settings,
    upload_bytes,
)
from compensation_calculator import calculate_monthly_results
from main import load_projects
from report import generate_bess_invoice_support_report


PROJECTS_CSV = ROOT_DIR / "data" / "projects.csv"
BANNER_IMAGE = ROOT_DIR / "assets" / "puerto_rico_flag_banner.png"
CREATE_DATASET_OPTION = "+ Create Scenario"
LAST_RUN_OUTPUT_KEY = "last-run-output"
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
    :root {
        --app-sidebar-width: 16rem;
    }

    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: var(--app-sidebar-width);
        width: var(--app-sidebar-width);
    }

    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        min-width: var(--app-sidebar-width);
        width: var(--app-sidebar-width);
    }

    [data-testid="stMainBlockContainer"] {
        box-sizing: border-box;
        max-width: none;
        width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    .app-banner {
        position: relative;
        width: calc(100% + 2rem);
        max-width: none;
        height: 8.25rem;
        margin: -3rem -1rem 1.75rem -1rem;
        overflow: hidden;
        border-radius: 0;
    }

    .app-banner img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center 68%;
        display: block;
    }

    .project-heading {
        color: #00CC00;
    }

    @media (max-width: 900px) {
        [data-testid="stMainBlockContainer"] {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .app-banner {
            width: 100%;
            margin-left: 0;
            margin-right: 0;
        }

        [data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }

        [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():

    st.html("""
        <style>
            header.stAppHeader::before {
                content: "Invoice Calculator";
                position: absolute;
                left: 50%;
                transform: translateX(-50%);
                top: 8px;
                font-weight: bold;
                color: var(--text-color);
                font-size: 35px;
                z-index: 999999;
                pointer-events: none;
            }
        </style>
    """)

    render_banner(BANNER_IMAGE)

    projects = load_available_projects()
    project_ids = list(projects)
    project_index = _option_index(project_ids, _query_param_value("project"), 0)
    project_id = st.sidebar.radio(
        "Facility",
        options=project_ids,
        index=project_index,
        format_func=lambda value: projects[value]["project_name"],
        key="facility-selector",
    )
    _set_query_param("project", project_id)
    project = projects[project_id]
    project_name = project["project_name"]
    render_database_flow(project_id, project_name)
    


def render_database_flow(project_id, project_name):

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

    created_dataset_name = st.session_state.pop(
        f"selected-dataset-{project_id}",
        None,
    )
    preferred_dataset_name = created_dataset_name or _query_param_value("dataset")
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
        " Scenario",
        options=[*dataset_names, CREATE_DATASET_OPTION],
        index=default_index,
        key=f"dataset-selector-{project_id}",
    )
    if selected_dataset_option == CREATE_DATASET_OPTION:
        render_create_dataset_panel(engine, project_id, datasets, force_visible=True)
        return

    dataset_name = selected_dataset_option
    override_mode = st.sidebar.toggle(
        "Override Mode",
        value=False,
        help=(
            "Unlock existing rows for audited edits/deletes. "
            "Leave this off for normal new-row entry."
        ),
        key=f"override-mode-{project_id}-{dataset_name}",
    )
    st.sidebar.divider()
    if st.sidebar.button(
        "Delete Current Scenario",
        type="primary",
        key=f"delete-scenario-button-{project_id}-{dataset_name}",
    ):
        render_delete_scenario_dialog(engine, project_id, dataset_name)

    _set_query_param("dataset", dataset_name)
    st.markdown(f'<h1 class="project-heading">{project_name}</h1>', unsafe_allow_html=True)

    try:
        row_counts = get_dataset_row_counts(engine, project_id, dataset_name)
    except Exception as exc:
        st.error(f"Could not read dataset status: {exc}")
        return

    render_run_history_dashboard(engine, project_id, dataset_name, settings=settings)

    st.subheader("Input Tables")
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

    render_database_table_views(engine, project_id, dataset_name, override_mode)

    st.subheader("Run")
    run_clicked = st.button("Run Calculation", type="primary")
    if not run_clicked:
        _render_saved_run_output(engine, project_id, dataset_name)
        return

    try:
        results_df, report_text = run_calculation_from_db(
            engine,
            project_id,
            dataset_name,
            project_name,
        )
        inputs = load_inputs_snapshot(engine, project_id, dataset_name)
        snapshot_data = build_run_snapshot_data(results_df, report_text, inputs=inputs)
        snapshot_month = snapshot_data["latest_month_summary"]["timestamp_month"]
        snapshot_name = generate_calculation_snapshot_name()
        csv_artifact = _upload_run_csv(
            settings,
            project_id,
            dataset_name,
            snapshot_month,
            snapshot_name,
            snapshot_data,
        )
        record_calculation_run(
            engine=engine,
            project_id=project_id,
            dataset_name=dataset_name,
            snapshot_month=snapshot_month,
            snapshot_data=snapshot_data,
            snapshot_name=snapshot_name,
            csv_artifact=csv_artifact,
        )
        _save_run_output(project_id, dataset_name, results_df, report_text)
    except ValueError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Database calculation failed: {exc}")
        return

    st.rerun()


def _save_run_output(project_id, dataset_name, results_df, report_text):
    st.session_state[LAST_RUN_OUTPUT_KEY] = {
        "project_id": project_id,
        "dataset_name": dataset_name,
        "results_df": results_df,
        "report_text": report_text,
    }


def _upload_run_csv(settings, project_id, dataset_name, snapshot_month, snapshot_name, snapshot_data):
    try:
        client = get_storage_client_from_settings(settings)
        bucket = settings.object_storage.bucket
        key = build_run_artifact_key(
            project_id, dataset_name, snapshot_month, snapshot_name, "csv"
        )
        csv_text = snapshot_data.get("csv_text", "")
        meta = upload_bytes(client, bucket, key, csv_text, content_type="text/csv")
        month_slug = (snapshot_month or "unknown")[:7].replace("-", "")
        return {
            "original_filename": f"bess_results_{month_slug}.csv",
            **meta,
        }
    except Exception:
        return None


def _render_saved_run_output(engine, project_id, dataset_name):
    saved_output = st.session_state.get(LAST_RUN_OUTPUT_KEY)
    if not saved_output:
        return
    if saved_output["project_id"] != project_id:
        return
    if saved_output["dataset_name"] != dataset_name:
        return

    render_results(saved_output["results_df"], saved_output["report_text"])
    render_analytics_summary(engine, project_id, dataset_name)


def _query_param_value(name):
    value = st.query_params.get(name)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _set_query_param(name, value):
    if _query_param_value(name) == value:
        return
    st.query_params[name] = value


def _option_index(options, preferred_value, fallback_index):
    if preferred_value in options:
        return options.index(preferred_value)
    return fallback_index


def render_create_dataset_toggle(engine, project_id, datasets):
    if st.sidebar.button(
        "+ Create Scenario",
        key=f"show-create-dataset-{project_id}",
    ):
        st.session_state[f"create-dataset-visible-{project_id}"] = True
    render_create_dataset_panel(engine, project_id, datasets)


def render_create_dataset_panel(engine, project_id, datasets, force_visible=False):
    toggle_key = f"create-dataset-visible-{project_id}"
    if not force_visible and not st.session_state.get(toggle_key, False):
        return

    dataset_names = [dataset["name"] for dataset in datasets]
    with st.sidebar.container(border=True):
        st.markdown("**Create Scenario**")
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
            st.error(f"Could not create scenario: {exc}")
        else:
            contract_value_count = row_counts.get("contract_values", 0)
            st.success(
                f"Created scenario `{created_name}` with "
                f"{contract_value_count} contract value rows."
            )
            st.session_state[f"selected-dataset-{project_id}"] = created_name
            st.rerun()


@st.dialog("Delete Scenario")
def render_delete_scenario_dialog(engine, project_id, dataset_name):
    st.warning(
        "Are you sure? This will permanently delete the entire scenario and all "
        "of its associated inputs and past runs from the database."
    )
    st.caption(f"Scenario: `{dataset_name}`")

    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button(
            "Delete permanently",
            type="primary",
            key=f"confirm-delete-scenario-{project_id}-{dataset_name}",
        ):
            try:
                next_dataset_name = delete_dataset_config(
                    engine,
                    project_id,
                    dataset_name,
                )
            except Exception as exc:
                st.error(f"Could not delete scenario: {exc}")
                return

            if next_dataset_name:
                st.session_state[f"selected-dataset-{project_id}"] = next_dataset_name
                st.query_params["dataset"] = next_dataset_name
            else:
                st.session_state.pop(f"selected-dataset-{project_id}", None)
                if "dataset" in st.query_params:
                    del st.query_params["dataset"]
            st.rerun()

    with cancel_col:
        if st.button(
            "Cancel",
            key=f"cancel-delete-scenario-{project_id}-{dataset_name}",
        ):
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
