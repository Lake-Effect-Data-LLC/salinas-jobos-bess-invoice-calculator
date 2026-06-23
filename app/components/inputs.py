from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import streamlit as st


INPUT_FILES = {
    "Contract values": "bess_contract_values_template.csv",
    "Yearly inputs": "bess_yearly_inputs_template.csv",
    "Monthly inputs": "bess_monthly_inputs_template.csv",
    "Monthly performance guarantee": "Monthly_Performance_Guarantee.csv",
    "Performance tests": "Performance_Tests.csv",
}


def render_csv_input_section(project_id, project_data_dir):
    local_sources = {
        label: Path(project_data_dir) / filename
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

    return input_sources


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
