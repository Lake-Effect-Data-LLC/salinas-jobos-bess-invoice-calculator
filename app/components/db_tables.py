import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.components.column_tooltips import INPUT_COLUMN_TOOLTIPS
from app.db import get_dataset_config_id
from app.services.table_editor import (
    save_monthly_inputs_edits,
    save_monthly_performance_guarantee_edits,
    save_performance_tests_edits,
    save_yearly_inputs_edits,
)


TABLE_CONFIGS = {
    "contract_values": {
        "label": "Contract values",
        "guidance": "Rarely changed. Treat as contract/reference data and include a source when editing later.",
        "order_by": "agreement_year",
        "columns": [
            "agreement_year",
            "cppf",
            "cpppif",
            "ddd",
            "ta",
            "rer",
            "ge",
            "design_dmax",
            "design_duration_energy",
            "annual_duration_energy_degradation_rate",
            "design_charge_energy",
            "grid_system_waiting_period_hours",
            "force_majeure_waiting_period_hours",
            "scheduled_maintenance_allowance_hours",
            "source_reference",
            "notes",
        ],
    },
    "yearly_inputs": {
        "label": "Yearly inputs",
        "guidance": "Expected once per agreement year. These values should line up with contract-year assumptions.",
        "order_by": "agreement_year",
        "columns": [
            "agreement_year",
            "dde",
            "tr",
            "gc",
            "source_reference",
            "notes",
        ],
    },
    "monthly_inputs": {
        "label": "Monthly inputs",
        "guidance": "Main recurring monthly input table. Each dataset should have one row per billing month.",
        "order_by": "agreement_year, timestamp_month",
        "columns": [
            "timestamp_month",
            "agreement_year",
            "other_adj",
            "bphrs",
            "pohrs",
            "unavhrs",
            "unavprodhrs",
            "gse",
            "pfm",
            "ip",
            "source_reference",
            "notes",
        ],
    },
    "monthly_performance_guarantee": {
        "label": "Monthly performance guarantee",
        "guidance": "Monthly metered performance data. Months should align with monthly inputs.",
        "order_by": "agreement_year, timestamp_month",
        "columns": [
            "timestamp_month",
            "agreement_year",
            "ce",
            "de",
            "ae_beg",
            "ae_end",
            "source_reference",
            "notes",
        ],
    },
    "performance_tests": {
        "label": "Performance tests",
        "guidance": "Event-based table. Add rows only when a performance test occurs.",
        "order_by": "agreement_year, test_date, test_id",
        "columns": [
            "test_id",
            "agreement_year",
            "test_type",
            "test_date",
            "requested_by",
            "tde",
            "measured_ramp_rate",
            "certified_by",
            "prepa_approved",
            "approval_date",
            "cure_or_retest_date",
            "replaces_test_id",
            "ramp_failure_caused_outage",
            "outage_start",
            "outage_end",
            "outage_equivalent_unavhrs",
            "source_reference",
            "notes",
        ],
    },
}


def render_database_table_views(engine, project_id, dataset_name):
    table_names = list(TABLE_CONFIGS)
    tabs = st.tabs([TABLE_CONFIGS[table_name]["label"] for table_name in table_names])
    for tab, table_name in zip(tabs, table_names):
        with tab:
            config = TABLE_CONFIGS[table_name]
            st.caption(config["guidance"])
            table = load_database_table(engine, project_id, dataset_name, table_name)
            if table_name == "monthly_inputs":
                render_monthly_inputs_editor(engine, project_id, dataset_name, table)
            elif table_name == "yearly_inputs":
                render_yearly_inputs_editor(engine, project_id, dataset_name, table)
            elif table_name == "monthly_performance_guarantee":
                render_monthly_performance_guarantee_editor(
                    engine,
                    project_id,
                    dataset_name,
                    table,
                )
            elif table_name == "performance_tests":
                render_performance_tests_editor(engine, project_id, dataset_name, table)
            else:
                st.dataframe(
                    table,
                    use_container_width=True,
                    hide_index=True,
                    column_config=_base_column_config(table_name),
                )


def render_monthly_inputs_editor(engine, project_id, dataset_name, table):
    st.caption("Edit existing rows or add a new row at the bottom. Deleting rows is not enabled yet.")
    _render_column_guide("monthly_inputs")
    editable_table = table.copy()
    if "id" in editable_table:
        editable_table["id"] = editable_table["id"].astype(str)

    edited_table = st.data_editor(
        editable_table,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=["id"],
        key=f"monthly-inputs-editor-{project_id}-{dataset_name}",
        column_config=_with_column_tooltips("monthly_inputs", {
            "id": None,
            "timestamp_month": st.column_config.DateColumn(
                "timestamp_month",
                format="YYYY-MM-DD",
                required=True,
                help=_column_help("monthly_inputs", "timestamp_month"),
            ),
            "agreement_year": st.column_config.NumberColumn(
                "agreement_year",
                min_value=1,
                step=1,
                required=True,
                help=_column_help("monthly_inputs", "agreement_year"),
            ),
        }),
    )
    if st.button(
        "Save monthly inputs",
        type="primary",
        key=f"monthly-inputs-save-{project_id}-{dataset_name}",
    ):
        try:
            result = save_monthly_inputs_edits(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                original_df=table,
                edited_df=edited_table,
                edit_reason=None,
                source=None,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(
                "Saved monthly inputs: "
                f"{result['inserted']} inserted, {result['updated']} updated."
            )
            st.rerun()


def render_yearly_inputs_editor(engine, project_id, dataset_name, table):
    st.caption("Edit existing rows or add a new agreement year at the bottom. Deleting rows is not enabled yet.")
    _render_column_guide("yearly_inputs")
    editable_table = table.copy()
    if "id" in editable_table:
        editable_table["id"] = editable_table["id"].astype(str)

    edited_table = st.data_editor(
        editable_table,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=["id"],
        key=f"yearly-inputs-editor-{project_id}-{dataset_name}",
        column_config=_with_column_tooltips("yearly_inputs", {
            "id": None,
            "agreement_year": st.column_config.NumberColumn(
                "agreement_year",
                min_value=1,
                step=1,
                required=True,
                help=_column_help("yearly_inputs", "agreement_year"),
            ),
            "dde": st.column_config.NumberColumn(
                "dde",
                required=True,
                help=_column_help("yearly_inputs", "dde"),
            ),
            "tr": st.column_config.NumberColumn(
                "tr",
                required=True,
                help=_column_help("yearly_inputs", "tr"),
            ),
            "gc": st.column_config.NumberColumn(
                "gc",
                help=_column_help("yearly_inputs", "gc"),
            ),
        }),
    )
    if st.button(
        "Save yearly inputs",
        type="primary",
        key=f"yearly-inputs-save-{project_id}-{dataset_name}",
    ):
        try:
            result = save_yearly_inputs_edits(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                original_df=table,
                edited_df=edited_table,
                edit_reason=None,
                source=None,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(
                "Saved yearly inputs: "
                f"{result['inserted']} inserted, {result['updated']} updated."
            )
            st.rerun()


def render_performance_tests_editor(engine, project_id, dataset_name, table):
    st.caption("Edit existing performance test events or add a new event at the bottom. Deleting rows is not enabled yet.")
    _render_column_guide("performance_tests")
    editable_table = table.copy()
    if "id" in editable_table:
        editable_table["id"] = editable_table["id"].astype(str)

    edited_table = st.data_editor(
        editable_table,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=["id"],
        key=f"performance-tests-editor-{project_id}-{dataset_name}",
        column_config=_with_column_tooltips("performance_tests", {
            "id": None,
            "agreement_year": st.column_config.NumberColumn(
                "agreement_year",
                min_value=1,
                step=1,
                required=True,
                help=_column_help("performance_tests", "agreement_year"),
            ),
            "test_date": st.column_config.DateColumn(
                "test_date",
                format="YYYY-MM-DD",
                required=True,
                help=_column_help("performance_tests", "test_date"),
            ),
            "approval_date": st.column_config.DateColumn(
                "approval_date",
                format="YYYY-MM-DD",
                help=_column_help("performance_tests", "approval_date"),
            ),
            "cure_or_retest_date": st.column_config.DateColumn(
                "cure_or_retest_date",
                format="YYYY-MM-DD",
                help=_column_help("performance_tests", "cure_or_retest_date"),
            ),
            "prepa_approved": st.column_config.CheckboxColumn(
                "prepa_approved",
                help=_column_help("performance_tests", "prepa_approved"),
            ),
            "ramp_failure_caused_outage": st.column_config.CheckboxColumn(
                "ramp_failure_caused_outage",
                help=_column_help("performance_tests", "ramp_failure_caused_outage"),
            ),
            "tde": st.column_config.NumberColumn(
                "tde",
                required=True,
                help=_column_help("performance_tests", "tde"),
            ),
            "measured_ramp_rate": st.column_config.NumberColumn(
                "measured_ramp_rate",
                help=_column_help("performance_tests", "measured_ramp_rate"),
            ),
            "outage_equivalent_unavhrs": st.column_config.NumberColumn(
                "outage_equivalent_unavhrs",
                help=_column_help("performance_tests", "outage_equivalent_unavhrs"),
            ),
        }),
    )
    if st.button(
        "Save performance tests",
        type="primary",
        key=f"performance-tests-save-{project_id}-{dataset_name}",
    ):
        try:
            result = save_performance_tests_edits(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                original_df=table,
                edited_df=edited_table,
                edit_reason=None,
                source=None,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(
                "Saved performance tests: "
                f"{result['inserted']} inserted, {result['updated']} updated."
            )
            st.rerun()


def render_monthly_performance_guarantee_editor(engine, project_id, dataset_name, table):
    st.caption("Edit existing monthly performance guarantee rows or add a new month at the bottom. Deleting rows is not enabled yet.")
    _render_column_guide("monthly_performance_guarantee")
    editable_table = table.copy()
    if "id" in editable_table:
        editable_table["id"] = editable_table["id"].astype(str)

    edited_table = st.data_editor(
        editable_table,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=["id"],
        key=f"monthly-performance-editor-{project_id}-{dataset_name}",
        column_config=_with_column_tooltips("monthly_performance_guarantee", {
            "id": None,
            "timestamp_month": st.column_config.DateColumn(
                "timestamp_month",
                format="YYYY-MM-DD",
                required=True,
                help=_column_help("monthly_performance_guarantee", "timestamp_month"),
            ),
            "agreement_year": st.column_config.NumberColumn(
                "agreement_year",
                min_value=1,
                step=1,
                required=True,
                help=_column_help("monthly_performance_guarantee", "agreement_year"),
            ),
            "ce": st.column_config.NumberColumn(
                "ce",
                required=True,
                help=_column_help("monthly_performance_guarantee", "ce"),
            ),
            "de": st.column_config.NumberColumn(
                "de",
                required=True,
                help=_column_help("monthly_performance_guarantee", "de"),
            ),
            "ae_beg": st.column_config.NumberColumn(
                "ae_beg",
                required=True,
                help=_column_help("monthly_performance_guarantee", "ae_beg"),
            ),
            "ae_end": st.column_config.NumberColumn(
                "ae_end",
                required=True,
                help=_column_help("monthly_performance_guarantee", "ae_end"),
            ),
        }),
    )
    if st.button(
        "Save monthly performance guarantee",
        type="primary",
        key=f"monthly-performance-save-{project_id}-{dataset_name}",
    ):
        try:
            result = save_monthly_performance_guarantee_edits(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                original_df=table,
                edited_df=edited_table,
                edit_reason=None,
                source=None,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(
                "Saved monthly performance guarantee: "
                f"{result['inserted']} inserted, {result['updated']} updated."
            )
            st.rerun()


def _base_column_config(table_name):
    return {
        column_name: st.column_config.Column(column_name, help=help_text)
        for column_name, help_text in INPUT_COLUMN_TOOLTIPS.get(table_name, {}).items()
    }


def _with_column_tooltips(table_name, overrides):
    column_config = _base_column_config(table_name)
    column_config.update(overrides)
    return column_config


def _column_help(table_name, column_name):
    return INPUT_COLUMN_TOOLTIPS.get(table_name, {}).get(column_name)


def _render_column_guide(table_name):
    tooltips = INPUT_COLUMN_TOOLTIPS.get(table_name, {})
    if not tooltips:
        return

    with st.expander("Column Guide", expanded=False):
        for column_name, description in tooltips.items():
            st.markdown(f"- `{column_name}`: {description}")


def load_database_table(engine, project_id, dataset_name, table_name):
    if table_name not in TABLE_CONFIGS:
        raise ValueError(f"Unsupported table '{table_name}'.")

    config = TABLE_CONFIGS[table_name]
    editable_tables = {
        "monthly_inputs",
        "yearly_inputs",
        "monthly_performance_guarantee",
        "performance_tests",
    }
    columns = ["id", *config["columns"]] if table_name in editable_tables else config["columns"]
    selected_columns = ", ".join(columns)
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        df = pd.read_sql_query(
            text(
                f"""
                SELECT {selected_columns}
                FROM {table_name}
                WHERE dataset_config_id = :dataset_config_id
                ORDER BY {config["order_by"]}
                """
            ),
            connection,
            params={"dataset_config_id": dataset_config_id},
        )

    return df
