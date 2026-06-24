import pandas as pd
import streamlit as st

from app.db import list_latest_calculation_runs_by_month


ANALYTICS_RUN_LIMIT = 12


def render_analytics_summary(engine, project_id, dataset_name):
    try:
        runs = list_latest_calculation_runs_by_month(
            engine,
            project_id=project_id,
            dataset_name=dataset_name,
            limit=ANALYTICS_RUN_LIMIT,
        )
    except Exception as exc:
        st.warning(f"Could not load analytics trends: {exc}")
        return

    financial_df, generation_df = build_analytics_trend_frames(runs)
    if financial_df.empty and generation_df.empty:
        return

    with st.expander("Analytics & Trends", expanded=True):
        financial_col, generation_col = st.columns(2)
        with financial_col:
            st.markdown("**Financial Trend**")
            if financial_df.empty:
                st.caption("No financial trend data yet.")
            else:
                st.line_chart(financial_df)

        with generation_col:
            st.markdown("**Generation Trend**")
            if generation_df.empty:
                st.caption("No generation trend data yet.")
            else:
                st.line_chart(generation_df)


def build_analytics_trend_frames(runs):
    financial_rows = []
    generation_rows = []

    for run in reversed(runs):
        summary = _summary(run)
        month = _month_value(run)
        financial_row = _row(
            month,
            {
                "MP": summary.get("MP"),
                "MFP": summary.get("MFP"),
            },
        )
        if financial_row:
            financial_rows.append(financial_row)

        generation_row = _row(
            month,
            {
                "MCC": summary.get("MCC"),
                "FAA %": _percent_value(summary.get("FAA")),
                "PRA %": _percent_value(summary.get("PRA")),
            },
        )
        if generation_row:
            generation_rows.append(generation_row)

    financial_df = _trend_frame(financial_rows)
    generation_df = _trend_frame(generation_rows)
    return financial_df, generation_df


def _trend_frame(rows):
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df.set_index("Month")


def _row(month, values):
    row = {"Month": month}
    has_value = False
    for column_name, value in values.items():
        numeric_value = _float_or_none(value)
        row[column_name] = numeric_value
        has_value = has_value or numeric_value is not None

    if not has_value:
        return None
    return row


def _summary(run):
    snapshot_data = run.get("snapshot_data") or {}
    return snapshot_data.get("latest_month_summary") or {}


def _month_value(run):
    summary = _summary(run)
    return summary.get("timestamp_month") or run.get("snapshot_month")


def _percent_value(value):
    numeric_value = _float_or_none(value)
    if numeric_value is None:
        return None
    if abs(numeric_value) <= 1:
        return numeric_value * 100
    return numeric_value


def _float_or_none(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
