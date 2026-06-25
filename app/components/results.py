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
        "csv_text": results_df.to_csv(index=False),
        "report_text": report_text,
    }
    if inputs is not None:
        snapshot["inputs"] = inputs
    return snapshot


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
