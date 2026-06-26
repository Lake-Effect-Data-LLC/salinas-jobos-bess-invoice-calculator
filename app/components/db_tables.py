import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.components.column_tooltips import INPUT_COLUMN_TOOLTIPS
from app.db import get_dataset_config_id
from app.services.table_editor import (
    generate_audit_event_id,
    save_contract_value_deletes,
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


def render_database_table_views(
    engine,
    project_id,
    dataset_name,
    override_mode=False,
    on_saved=None,
):
    override_source = None
    if override_mode:
        st.warning(
            "Override Mode is on. Existing rows can be edited or deleted, "
            "and an edit reason is required before saving."
        )
    table_names = list(TABLE_CONFIGS)
    tabs = st.tabs([TABLE_CONFIGS[table_name]["label"] for table_name in table_names])
    for tab, table_name in zip(tabs, table_names):
        with tab:
            config = TABLE_CONFIGS[table_name]
            st.caption(config["guidance"])
            table = load_database_table(engine, project_id, dataset_name, table_name)
            if table_name == "contract_values":
                render_contract_values_editor(
                    engine,
                    project_id,
                    dataset_name,
                    table,
                    override_mode,
                    override_source,
                    on_saved,
                )
            elif table_name == "monthly_inputs":
                render_monthly_inputs_editor(
                    engine,
                    project_id,
                    dataset_name,
                    table,
                    override_mode,
                    override_source,
                    on_saved,
                )
            elif table_name == "yearly_inputs":
                render_yearly_inputs_editor(
                    engine,
                    project_id,
                    dataset_name,
                    table,
                    override_mode,
                    override_source,
                    on_saved,
                )
            elif table_name == "monthly_performance_guarantee":
                render_monthly_performance_guarantee_editor(
                    engine,
                    project_id,
                    dataset_name,
                    table,
                    override_mode,
                    override_source,
                    on_saved,
                )
            elif table_name == "performance_tests":
                render_performance_tests_editor(
                    engine,
                    project_id,
                    dataset_name,
                    table,
                    override_mode,
                    override_source,
                    on_saved,
                )


def render_contract_values_editor(
    engine,
    project_id,
    dataset_name,
    table,
    override_mode=False,
    override_source=None,
    on_saved=None,
):
    st.caption(
        "Contract values are reference data. They are read-only unless Override Mode "
        "is on, and Override Mode only allows audited deletes."
    )
    _render_column_guide("contract_values")
    editable_table = _prepare_editable_table(table)
    column_config = _with_column_tooltips("contract_values", {"id": None})

    if not override_mode:
        st.dataframe(
            editable_table,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
        )
        return

    edited_table = st.data_editor(
        editable_table,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=list(editable_table.columns),
        key=f"contract-values-override-editor-{project_id}-{dataset_name}",
        column_config=column_config,
    )
    edit_reason, save_clicked = _render_save_controls(
        "Save contract value edits or deletes",
        key=f"contract-values-save-{project_id}-{dataset_name}",
        override_mode=override_mode,
    )
    if save_clicked:
        audit_event_id = generate_audit_event_id()
        try:
            result = save_contract_value_deletes(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                original_df=table,
                edited_df=edited_table,
                edit_reason=edit_reason,
                source=override_source,
                allow_existing_row_changes=override_mode,
                audit_event_id=audit_event_id,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(f"Saved contract values: {result['deleted']} deleted.")
            _run_on_saved(on_saved, "contract_values", result, edit_reason)
            st.rerun()


def render_monthly_inputs_editor(
    engine,
    project_id,
    dataset_name,
    table,
    override_mode=False,
    override_source=None,
    on_saved=None,
):
    st.caption(_guarded_editor_guidance())
    _render_column_guide("monthly_inputs")
    editable_table = _prepare_editable_table(table)
    column_config = _with_column_tooltips(
        "monthly_inputs",
        {
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
        },
    )
    edited_table = _render_guarded_editor(
        editable_table,
        table_name="monthly_inputs",
        project_id=project_id,
        dataset_name=dataset_name,
        override_mode=override_mode,
        column_config=column_config,
    )
    edit_reason, save_clicked = _render_save_controls(
        "Save monthly inputs",
        key=f"monthly-inputs-save-{project_id}-{dataset_name}",
        override_mode=override_mode,
    )
    if save_clicked:
        audit_event_id = generate_audit_event_id()
        try:
            result = save_monthly_inputs_edits(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                original_df=table,
                edited_df=edited_table,
                edit_reason=edit_reason,
                source=override_source,
                allow_existing_row_changes=override_mode,
                audit_event_id=audit_event_id,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(_save_message("monthly inputs", result))
            _run_on_saved(on_saved, "monthly_inputs", result, edit_reason)
            st.rerun()


def render_yearly_inputs_editor(
    engine,
    project_id,
    dataset_name,
    table,
    override_mode=False,
    override_source=None,
    on_saved=None,
):
    st.caption(_guarded_editor_guidance())
    _render_column_guide("yearly_inputs")
    editable_table = _prepare_editable_table(table)
    column_config = _with_column_tooltips(
        "yearly_inputs",
        {
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
        },
    )
    edited_table = _render_guarded_editor(
        editable_table,
        table_name="yearly_inputs",
        project_id=project_id,
        dataset_name=dataset_name,
        override_mode=override_mode,
        column_config=column_config,
    )
    edit_reason, save_clicked = _render_save_controls(
        "Save yearly inputs",
        key=f"yearly-inputs-save-{project_id}-{dataset_name}",
        override_mode=override_mode,
    )
    if save_clicked:
        audit_event_id = generate_audit_event_id()
        try:
            result = save_yearly_inputs_edits(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                original_df=table,
                edited_df=edited_table,
                edit_reason=edit_reason,
                source=override_source,
                allow_existing_row_changes=override_mode,
                audit_event_id=audit_event_id,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(_save_message("yearly inputs", result))
            _run_on_saved(on_saved, "yearly_inputs", result, edit_reason)
            st.rerun()


def render_performance_tests_editor(
    engine,
    project_id,
    dataset_name,
    table,
    override_mode=False,
    override_source=None,
    on_saved=None,
):
    st.caption(_guarded_editor_guidance())
    _render_column_guide("performance_tests")
    editable_table = _prepare_editable_table(table)
    column_config = _with_column_tooltips(
        "performance_tests",
        {
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
        },
    )
    edited_table = _render_guarded_editor(
        editable_table,
        table_name="performance_tests",
        project_id=project_id,
        dataset_name=dataset_name,
        override_mode=override_mode,
        column_config=column_config,
    )
    edit_reason, save_clicked = _render_save_controls(
        "Save performance tests",
        key=f"performance-tests-save-{project_id}-{dataset_name}",
        override_mode=override_mode,
    )
    if save_clicked:
        audit_event_id = generate_audit_event_id()
        try:
            result = save_performance_tests_edits(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                original_df=table,
                edited_df=edited_table,
                edit_reason=edit_reason,
                source=override_source,
                allow_existing_row_changes=override_mode,
                audit_event_id=audit_event_id,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(_save_message("performance tests", result))
            _run_on_saved(on_saved, "performance_tests", result, edit_reason)
            st.rerun()


def render_monthly_performance_guarantee_editor(
    engine,
    project_id,
    dataset_name,
    table,
    override_mode=False,
    override_source=None,
    on_saved=None,
):
    st.caption(_guarded_editor_guidance())
    _render_column_guide("monthly_performance_guarantee")
    editable_table = _prepare_editable_table(table)
    column_config = _with_column_tooltips(
        "monthly_performance_guarantee",
        {
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
        },
    )
    edited_table = _render_guarded_editor(
        editable_table,
        table_name="monthly_performance_guarantee",
        project_id=project_id,
        dataset_name=dataset_name,
        override_mode=override_mode,
        column_config=column_config,
    )
    edit_reason, save_clicked = _render_save_controls(
        "Save monthly performance guarantee",
        key=f"monthly-performance-save-{project_id}-{dataset_name}",
        override_mode=override_mode,
    )
    if save_clicked:
        audit_event_id = generate_audit_event_id()
        try:
            result = save_monthly_performance_guarantee_edits(
                engine=engine,
                project_id=project_id,
                dataset_name=dataset_name,
                original_df=table,
                edited_df=edited_table,
                edit_reason=edit_reason,
                source=override_source,
                allow_existing_row_changes=override_mode,
                audit_event_id=audit_event_id,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(_save_message("monthly performance guarantee", result))
            _run_on_saved(
                on_saved,
                "monthly_performance_guarantee",
                result,
                edit_reason,
            )
            st.rerun()


def _render_guarded_editor(
    editable_table,
    table_name,
    project_id,
    dataset_name,
    override_mode,
    column_config,
):
    if override_mode:
        return st.data_editor(
            editable_table,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            disabled=["id"],
            key=f"{table_name}-override-editor-{project_id}-{dataset_name}",
            column_config=column_config,
        )

    st.caption(
        "Add new rows at the bottom. Existing row changes require Override Mode to save."
    )
    return st.data_editor(
        editable_table,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=["id"],
        key=f"{table_name}-normal-editor-{project_id}-{dataset_name}",
        column_config=column_config,
    )


def _render_save_controls(label, key, override_mode):
    if not override_mode:
        return None, st.button(label, type="primary", key=key)

    with st.container(border=True):
        st.warning(" Please provide a detailed reason for modifying historical reference data.")
        edit_reason = st.text_area(
            "Override edit reason",
            key=f"{key}-override-reason",
            placeholder="Describe what changed and why this historical/reference data is being modified.",
        )
        save_clicked = st.button(label, type="primary", key=key)

    return edit_reason, save_clicked


def _run_on_saved(on_saved, table_name, result, edit_reason):
    if on_saved is not None and _has_saved_changes(result):
        on_saved(
            {
                "audit_event_id": result.get("audit_event_id"),
                "table_name": table_name,
                "change_result": {
                    "inserted": result.get("inserted", 0),
                    "updated": result.get("updated", 0),
                    "deleted": result.get("deleted", 0),
                },
                "edit_reason": edit_reason,
            }
        )


def _has_saved_changes(result):
    return any(result.get(key, 0) for key in ("inserted", "updated", "deleted"))


def _prepare_editable_table(table):
    editable_table = table.copy()
    if "id" in editable_table:
        editable_table["id"] = editable_table["id"].astype(str)
    return editable_table


def _guarded_editor_guidance():
    return (
        "Normal mode lets you add rows in the table. "
        "Existing row changes require Override Mode to save."
    )


def _save_message(label, result):
    return (
        f"Saved {label}: {result['inserted']} inserted, "
        f"{result['updated']} updated, {result['deleted']} deleted."
    )


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
        st.caption("You can also hover over the table headers for quick tooltips.")
        for column_name, description in tooltips.items():
            st.markdown(f"- `{column_name}`: {description}")


def load_database_table(engine, project_id, dataset_name, table_name):
    if table_name not in TABLE_CONFIGS:
        raise ValueError(f"Unsupported table '{table_name}'.")

    config = TABLE_CONFIGS[table_name]
    editable_tables = {
        "contract_values",
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
