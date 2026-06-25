import altair as alt
import pandas as pd
import streamlit as st

from app.db import list_latest_calculation_runs_by_month


ANALYTICS_RUN_LIMIT = 12
SUMMARY_METRICS = {
    "MP": {
        "field": "MP",
        "label": "Monthly Payment",
        "axis_title": "Dollars",
        "format": "$,.2f",
        "value_kind": "currency",
    },
    "MFP": {
        "field": "MFP",
        "label": "Monthly Fixed Payment",
        "axis_title": "Dollars",
        "format": "$,.2f",
        "value_kind": "currency",
    },
    "MCC": {
        "field": "MCC",
        "label": "Monthly Contract Capability",
        "axis_title": "MW",
        "format": ",.4f",
        "value_kind": "number",
    },
    "FAA %": {
        "field": "FAA",
        "label": "Facility Availability Adjustment",
        "axis_title": "Percent",
        "format": ",.2f",
        "value_kind": "percent",
    },
    "PRA %": {
        "field": "PRA",
        "label": "PREPA Risk Adjustment",
        "axis_title": "Percent",
        "format": ",.2f",
        "value_kind": "percent",
    },
}


def render_summary_comparison(engine, project_id, dataset_name):
    try:
        runs = list_latest_calculation_runs_by_month(
            engine,
            project_id=project_id,
            dataset_name=dataset_name,
            limit=ANALYTICS_RUN_LIMIT,
        )
    except Exception as exc:
        st.warning(f"Could not load summary comparison: {exc}")
        return

    if not runs:
        return

    render_summary_comparison_from_runs(runs, project_id, dataset_name)


def render_summary_comparison_from_runs(runs, project_id, dataset_name):
    with st.expander("Summary Comparison", expanded=True):
        metric_key = st.selectbox(
            "Metric",
            options=list(SUMMARY_METRICS),
            key=f"summary-comparison-metric-{project_id}-{dataset_name}",
        )
        comparison_df = build_summary_comparison_frame(runs, metric_key)
        if comparison_df.empty:
            st.caption("No comparison data yet.")
            return

        delta_text = build_summary_delta_text(comparison_df, metric_key)
        if delta_text:
            st.caption(delta_text)

        st.altair_chart(
            _comparison_bar_chart(comparison_df, metric_key),
            use_container_width=True,
        )
        if "Previous Runs Average" not in set(comparison_df["Comparison"]):
            st.caption("No previous runs yet for average comparison.")


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
                st.altair_chart(
                    _trend_line_chart(
                        financial_df,
                        y_axis_title="Dollars",
                        y_format="$,.2f",
                    ),
                    use_container_width=True,
                )

        with generation_col:
            st.markdown("**Generation Trend**")
            if generation_df.empty:
                st.caption("No generation trend data yet.")
            else:
                st.altair_chart(
                    _trend_line_chart(
                        generation_df,
                        y_axis_title="Metric value",
                        y_format=",.2f",
                    ),
                    use_container_width=True,
                )


def build_summary_comparison_frame(runs, metric_key):
    metric_config = SUMMARY_METRICS[metric_key]
    latest_summary = _summary(runs[0])
    latest_value = _metric_value(latest_summary, metric_key)

    rows = []
    if latest_value is not None:
        rows.append({"Comparison": "Latest Run", "Value": latest_value})

    previous_values = [
        value
        for value in (_metric_value(_summary(run), metric_key) for run in runs[1:])
        if value is not None
    ]
    if previous_values:
        rows.append(
            {
                "Comparison": "Previous Runs Average",
                "Value": sum(previous_values) / len(previous_values),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["Metric"] = metric_config["label"]
        df["ChartLabel"] = df["Comparison"].replace(
            {"Previous Runs Average": "Previous Avg"}
        )
    return df


def build_summary_delta_text(comparison_df, metric_key):
    if comparison_df.empty:
        return ""

    values_by_comparison = {
        row["Comparison"]: row["Value"]
        for row in comparison_df.to_dict("records")
    }
    latest_value = values_by_comparison.get("Latest Run")
    previous_average = values_by_comparison.get("Previous Runs Average")
    if latest_value is None or previous_average in (None, 0):
        return ""

    metric_config = SUMMARY_METRICS[metric_key]
    delta = latest_value - previous_average
    direction = "higher than" if delta >= 0 else "lower than"
    percent_delta = (delta / abs(previous_average)) * 100
    delta_value = _format_delta_value(abs(delta), metric_config)
    return (
        f"Latest is {delta_value} {direction} previous runs average "
        f"({percent_delta:+.1f}%)."
    )


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


def _comparison_bar_chart(df, metric_key):
    metric_config = SUMMARY_METRICS[metric_key]

    base = alt.Chart(df).encode(
        x=alt.X(
            "ChartLabel:N",
            title="Comparison",
            sort=None,
            axis=alt.Axis(labelAngle=0, labelLimit=180),
            scale=alt.Scale(paddingInner=0.45, paddingOuter=0.45),
        ),
        y=alt.Y(
            "Value:Q",
            title=metric_config["axis_title"],
            axis=alt.Axis(format=metric_config["format"]),
        ),
    )
    bars = (
        base.mark_bar(size=96)
        .encode(
            color=alt.Color("Comparison:N", legend=None),
            tooltip=[
                alt.Tooltip("Comparison:N", title="Comparison"),
                alt.Tooltip(
                    "Value:Q",
                    title=metric_config["label"],
                    format=metric_config["format"],
                ),
            ],
        )
    )
    labels = base.mark_text(dy=-8, fontSize=12).encode(
        text=alt.Text("Value:Q", format=metric_config["format"]),
    )

    return (bars + labels).properties(
        title=f"{metric_config['label']}: Latest Run vs Previous Runs Average",
        height=260,
    )


def _trend_line_chart(df, y_axis_title, y_format):
    chart_df = df.reset_index().melt(
        id_vars="Month",
        var_name="Metric",
        value_name="Value",
    )
    return (
        alt.Chart(chart_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month:T", title="Billing Month"),
            y=alt.Y("Value:Q", title=y_axis_title, axis=alt.Axis(format=y_format)),
            color=alt.Color("Metric:N", title="Metric"),
            tooltip=[
                alt.Tooltip("Month:T", title="Billing Month"),
                alt.Tooltip("Metric:N", title="Metric"),
                alt.Tooltip("Value:Q", title=y_axis_title, format=y_format),
            ],
        )
        .properties(height=280)
    )


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


def _metric_value(summary, metric_key):
    field_name = SUMMARY_METRICS[metric_key]["field"]
    value = summary.get(field_name)
    if metric_key.endswith("%"):
        return _percent_value(value)
    return _float_or_none(value)


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


def _format_delta_value(value, metric_config):
    value_kind = metric_config["value_kind"]
    if value_kind == "currency":
        return f"${value:,.0f}"
    if value_kind == "percent":
        return f"{value:.2f} percentage points"
    return f"{value:,.4f}"
