import base64
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import streamlit as st

from compensation_calculator import calculate_monthly_results
from data_reader import (
    load_bess_inputs,
    load_monthly_performance_guarantee_inputs,
    load_performance_tests,
)
from data_writer import BESS_MONTHLY_RESULT_COLUMNS
from error_checks import input_validation
from main import load_projects
from report import generate_bess_invoice_support_report


PROJECTS_CSV = Path("data") / "projects.csv"
BANNER_IMAGE = Path("assets") / "puerto_rico_flag_banner.png"

INPUT_FILES = {
    "Contract values": "bess_contract_values_template.csv",
    "Yearly inputs": "bess_yearly_inputs_template.csv",
    "Monthly inputs": "bess_monthly_inputs_template.csv",
    "Monthly performance guarantee": "Monthly_Performance_Guarantee.csv",
    "Performance tests": "Performance_Tests.csv",
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
    render_banner()
    st.title("BESS Invoice Calculator")

    projects = load_available_projects()
    project_id = st.sidebar.radio(
        "Project",
        options=list(projects),
        format_func=lambda value: projects[value]["project_name"],
    )
    project = projects[project_id]
    project_name = project["project_name"]
    project_data_dir = Path(project.get("data_folder", ""))

    if project_data_dir:
        st.sidebar.caption(f"Default data folder: `{project_data_dir}`")
    st.sidebar.caption("Uploaded CSVs override local defaults for this run.")

    local_sources = {
        label: project_data_dir / filename
        for label, filename in INPUT_FILES.items()
    }
    uploaded_files = collect_uploaded_files(project_id)
    input_sources = build_input_sources(local_sources, uploaded_files)

    st.subheader("Input Files")
    input_summary_df = build_input_summary(input_sources)
    st.dataframe(input_summary_df, use_container_width=True, hide_index=True)

    missing_required = [
        label
        for label, source in input_sources.items()
        if not source["available"]
    ]
    if missing_required:
        st.warning(
            "Upload the missing CSV file(s) before validating or running: "
            + ", ".join(missing_required)
        )

    input_tables = read_input_tables(input_sources)
    tabs = st.tabs(list(input_tables))
    for tab, (label, table) in zip(tabs, input_tables.items()):
        with tab:
            if table.empty:
                st.info("No local default or uploaded file is available.")
            else:
                st.dataframe(table, use_container_width=True, hide_index=True)

    st.subheader("Run")
    validate_clicked = st.button("Validate Inputs", type="secondary")
    run_clicked = st.button("Run Calculation", type="primary")

    if validate_clicked:
        try:
            with materialized_input_paths(input_sources) as paths:
                validate_inputs(paths)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.success("Input files passed validation.")

    if run_clicked:
        try:
            with materialized_input_paths(input_sources) as paths:
                validate_inputs(paths)
                results_df, report_text = run_calculation(paths, project_name)
        except ValueError as exc:
            st.error(str(exc))
            return

        st.success("Calculation complete.")
        st.subheader("Monthly Results")
        st.dataframe(results_df, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download monthly results CSV",
                data=results_df.to_csv(index=False).encode("utf-8"),
                file_name="bess_monthly_results.csv",
                mime="text/csv",
            )
        with col2:
            st.download_button(
                "Download invoice support report",
                data=report_text.encode("utf-8"),
                file_name="report.txt",
                mime="text/plain",
            )


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


def render_banner():
    if not BANNER_IMAGE.exists():
        return

    encoded_image = base64.b64encode(BANNER_IMAGE.read_bytes()).decode("ascii")
    st.markdown(
        f"""
        <div class="app-banner">
            <img src="data:image/png;base64,{encoded_image}" alt="Puerto Rico landscape and flag">
        </div>
        """,
        unsafe_allow_html=True,
    )


def collect_uploaded_files(project_id):
    uploaded_files = {}
    with st.sidebar.expander("Drag and drop CSV inputs", expanded=True):
        st.caption(
            "Upload any CSV to override the local default. In Snowflake, upload "
            "all required CSVs if local defaults are not bundled with the app."
        )
        for label, filename in INPUT_FILES.items():
            uploaded_file = st.file_uploader(
                label,
                type="csv",
                key=f"{project_id}-{filename}",
            )
            if uploaded_file is not None:
                uploaded_files[label] = uploaded_file
    return uploaded_files


def build_input_sources(local_sources, uploaded_files):
    sources = {}
    for label, local_path in local_sources.items():
        uploaded_file = uploaded_files.get(label)
        if uploaded_file is not None:
            sources[label] = {
                "source": "uploaded CSV",
                "available": True,
                "filename": INPUT_FILES[label],
                "path": None,
                "uploaded_file": uploaded_file,
            }
        elif local_path.exists():
            sources[label] = {
                "source": "local default",
                "available": True,
                "filename": INPUT_FILES[label],
                "path": local_path,
                "uploaded_file": None,
            }
        else:
            sources[label] = {
                "source": "missing",
                "available": False,
                "filename": INPUT_FILES[label],
                "path": local_path,
                "uploaded_file": None,
            }
    return sources


def build_input_summary(input_sources):
    rows = []
    for label, source in input_sources.items():
        table = read_input_table(source)
        rows.append(
            {
                "input": label,
                "required file": source["filename"],
                "source": source["source"],
                "available": source["available"],
                "rows": len(table) if source["available"] else None,
            }
        )
    return pd.DataFrame(rows)


def read_input_tables(input_sources):
    return {
        label: read_input_table(source)
        for label, source in input_sources.items()
    }


def read_input_table(source):
    if not source["available"]:
        return pd.DataFrame()
    if source["uploaded_file"] is not None:
        return pd.read_csv(BytesIO(source["uploaded_file"].getvalue()))
    return pd.read_csv(source["path"])


class materialized_input_paths:
    def __init__(self, input_sources):
        self.input_sources = input_sources
        self.temp_dir = None

    def __enter__(self):
        missing = [
            source["filename"]
            for source in self.input_sources.values()
            if not source["available"]
        ]
        if missing:
            formatted = "\n".join(f"- {filename}" for filename in missing)
            raise ValueError(f"Required input file(s) missing:\n{formatted}")

        self.temp_dir = TemporaryDirectory()
        temp_path = Path(self.temp_dir.name)
        paths = {}
        for label, source in self.input_sources.items():
            if source["uploaded_file"] is None:
                paths[label] = source["path"]
                continue

            staged_path = temp_path / source["filename"]
            staged_path.write_bytes(source["uploaded_file"].getvalue())
            paths[label] = staged_path
        return paths

    def __exit__(self, exc_type, exc_value, traceback):
        if self.temp_dir is not None:
            self.temp_dir.cleanup()


def validate_inputs(paths):
    input_validation(*paths.values())


def run_calculation(paths, project_name):
    contract_values, yearly_inputs, monthly_inputs = load_bess_inputs(
        paths["Contract values"],
        paths["Yearly inputs"],
        paths["Monthly inputs"],
    )
    monthly_performance_guarantee_inputs = load_monthly_performance_guarantee_inputs(
        paths["Monthly performance guarantee"]
    )
    performance_tests = load_performance_tests(paths["Performance tests"])

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


def monthly_results_to_dataframe(monthly_results):
    rows = []
    for result in monthly_results:
        rows.append(
            {
                "timestamp_month": result.timestamp_month,
                "agreement_year": result.agreement_year,
                "CPP": result.cpp,
                "MCC": result.mcc,
                "FA": result.fa,
                "FAA": result.faa,
                "PRA": result.pra,
                "MFP": result.mfp,
                "Other_ADJ": result.other_adj,
                "ALD": result.ald,
                "CLD": result.cld,
                "Actual_Efficiency": result.actual_efficiency,
                "ELD": result.eld,
                "ADJ_Total": result.adj_total,
                "MP": result.mp,
            }
        )
    return pd.DataFrame(rows, columns=BESS_MONTHLY_RESULT_COLUMNS)


if __name__ == "__main__":
    main()



    
