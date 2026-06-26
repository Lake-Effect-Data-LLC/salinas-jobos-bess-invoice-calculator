import csv
from io import StringIO

import pandas as pd
import streamlit as st

from data_writer import BESS_MONTHLY_RESULT_COLUMNS


def render_results(results_df, report_text):
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


def build_run_snapshot_data(results_df, report_text, inputs=None):
    if results_df.empty:
        raise ValueError("Cannot create a run snapshot from empty calculation results.")

    sorted_results = results_df.sort_values("timestamp_month")
    latest_row = sorted_results.iloc[-1].to_dict()
    snapshot = {
        "latest_month_summary": _json_ready_record(latest_row),
        "report_text": report_text,
    }
    if inputs is not None:
        snapshot["inputs"] = inputs
    snapshot["csv_text"] = build_run_csv_text(results_df, inputs=inputs)
    return snapshot


def build_run_csv_text(results_df, inputs=None):
    output = StringIO()
    _write_section(output, "monthly_results", results_df)

    if inputs:
        _write_input_sections(output, inputs)

    return output.getvalue()


def build_inputs_csv_text(inputs, change_context=None):
    output = StringIO()
    if change_context:
        _write_change_summary_section(output, change_context)
    _write_input_sections(output, inputs)
    return output.getvalue()


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


def _json_ready_record(record):
    return {
        key: _json_ready_value(value)
        for key, value in record.items()
    }


def _json_ready_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _write_section(output, section_name, records):
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["SECTION", section_name])

    df = _records_to_dataframe(records)
    if df.empty:
        writer.writerow(["NO ROWS"])
        writer.writerow([])
        return

    df.to_csv(output, index=False, lineterminator="\n")
    writer.writerow([])


def _records_to_dataframe(records):
    if isinstance(records, pd.DataFrame):
        return records
    return pd.DataFrame(records)


def _write_input_sections(output, inputs):
    for section_name in (
        "contract_values",
        "yearly_inputs",
        "monthly_inputs",
        "monthly_performance_guarantee",
        "performance_tests",
    ):
        _write_section(output, section_name, inputs.get(section_name, []))


def _write_change_summary_section(output, change_context):
    result = change_context.get("change_result") or {}
    rows = [
        {"field": "audit_event_id", "value": change_context.get("audit_event_id", "")},
        {"field": "table_name", "value": change_context.get("table_name", "")},
        {"field": "inserted", "value": result.get("inserted", 0)},
        {"field": "updated", "value": result.get("updated", 0)},
        {"field": "deleted", "value": result.get("deleted", 0)},
        {"field": "edit_reason", "value": change_context.get("edit_reason") or ""},
    ]
    _write_section(output, "change_summary", rows)
