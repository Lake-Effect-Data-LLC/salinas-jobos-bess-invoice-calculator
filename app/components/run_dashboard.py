from datetime import date, datetime

import streamlit as st

from app.db import list_latest_calculation_runs_by_month


PREVIOUS_RUN_LIMIT = 12
RUN_FETCH_LIMIT = PREVIOUS_RUN_LIMIT + 1


def render_run_history_dashboard(engine, project_id, dataset_name):
    st.subheader("Run History")
    try:
        runs = list_latest_calculation_runs_by_month(
            engine,
            project_id=project_id,
            dataset_name=dataset_name,
            limit=RUN_FETCH_LIMIT,
        )
    except Exception as exc:
        st.warning(f"Could not load run history: {exc}")
        return

    if not runs:
        st.info("No runs yet")
        return

    latest_run = runs[0]
    previous_runs = runs[1:]

    latest_col, previous_col = st.columns([2, 3])
    with latest_col:
        _render_latest_run(latest_run)
    with previous_col:
        _render_previous_runs(previous_runs)


def _render_latest_run(run):
    summary = _summary(run)
    st.markdown("**Latest Run**")
    st.caption(_month_label(run["snapshot_month"]))

    amount_col, mfp_col = st.columns(2)
    amount_col.metric("Amount Due", _currency(summary.get("MP")))
    mfp_col.metric("MFP", _currency(summary.get("MFP")))

    basis_cols = st.columns(4)
    basis_cols[0].metric("CPP", _currency(summary.get("CPP")))
    basis_cols[1].metric("MCC", _number(summary.get("MCC")))
    basis_cols[2].metric("FAA", _percent(summary.get("FAA")))
    basis_cols[3].metric("PRA", _percent(summary.get("PRA")))

    _render_downloads(run, "latest")


def _render_previous_runs(runs):
    st.markdown("**Previous Runs**")
    if not runs:
        st.caption("No previous monthly runs.")
        return

    for run in runs:
        summary = _summary(run)
        with st.container(border=True):
            month_col, metrics_col = st.columns([1.25, 5])
            with month_col:
                st.markdown(f"**{_month_label(run['snapshot_month'])}**")
                _render_downloads(run, f"previous-{run['snapshot_id']}")
            with metrics_col:
                primary_cols = st.columns(2)
                _render_metric_block(
                    primary_cols[0],
                    "MP",
                    _currency(summary.get("MP")),
                    primary=True,
                )
                _render_metric_block(
                    primary_cols[1],
                    "MFP",
                    _currency(summary.get("MFP")),
                    primary=True,
                )

                basis_cols = st.columns(4)
                _render_metric_block(basis_cols[0], "CPP", _currency(summary.get("CPP")))
                _render_metric_block(basis_cols[1], "MCC", _number(summary.get("MCC")))
                _render_metric_block(basis_cols[2], "FAA", _percent(summary.get("FAA")))
                _render_metric_block(basis_cols[3], "PRA", _percent(summary.get("PRA")))


def _render_metric_block(container, label, value, primary=False):
    size = "1.75rem" if primary else "1.2rem"
    weight = "500" if primary else "400"
    container.markdown(
        f"""
        <div style="min-width:0;">
            <div style="font-size:0.78rem; color:#6b7280; margin-bottom:0.15rem;">{label}</div>
            <div style="
                font-size:{size};
                font-weight:{weight};
                line-height:1.15;
                white-space:normal;
                overflow-wrap:anywhere;
            ">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_downloads(run, key_prefix):
    snapshot_data = run.get("snapshot_data") or {}
    csv_text = snapshot_data.get("csv_text")
    report_text = snapshot_data.get("report_text")
    month = _month_slug(run["snapshot_month"])
    col1, col2 = st.columns(2)
    with col1:
        if csv_text:
            st.download_button(
                "CSV",
                data=csv_text.encode("utf-8"),
                file_name=f"bess_results_{month}.csv",
                mime="text/csv",
                key=f"{key_prefix}-csv-download",
            )
    with col2:
        if report_text:
            st.download_button(
                "Report",
                data=report_text.encode("utf-8"),
                file_name=f"bess_report_{month}.txt",
                mime="text/plain",
                key=f"{key_prefix}-report-download",
            )


def _summary(run):
    snapshot_data = run.get("snapshot_data") or {}
    return snapshot_data.get("latest_month_summary") or {}


def _month_label(value):
    parsed = _parse_date(value)
    if parsed is None:
        return str(value)
    return parsed.strftime("%B %Y")


def _month_slug(value):
    parsed = _parse_date(value)
    if parsed is None:
        return str(value).replace(" ", "_").replace("/", "-")
    return parsed.strftime("%Y-%m")


def _parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def _currency(value):
    numeric_value = _float_or_none(value)
    if numeric_value is None:
        return "-"
    return f"${numeric_value:,.2f}"


def _number(value):
    numeric_value = _float_or_none(value)
    if numeric_value is None:
        return "-"
    return f"{numeric_value:,.4f}"


def _percent(value):
    numeric_value = _float_or_none(value)
    if numeric_value is None:
        return "-"
    if abs(numeric_value) <= 1:
        numeric_value *= 100
    return f"{numeric_value:,.2f}%"


def _float_or_none(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
