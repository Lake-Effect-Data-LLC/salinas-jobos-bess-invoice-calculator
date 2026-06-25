import math
from datetime import date, datetime
from decimal import Decimal

import pandas as pd
from sqlalchemy import text

from app.db import get_dataset_config_id
from classes import (
    BessContractValues,
    BessMonthlyInputs,
    BessMonthlyPerformanceGuaranteeInputs,
    BessPerformanceTest,
    BessYearlyInputs,
)


def load_bess_inputs_from_db(engine, project_id, dataset_name="actual"):
    contract_values = load_contract_values_from_db(engine, project_id, dataset_name)
    yearly_inputs = load_yearly_inputs_from_db(engine, project_id, dataset_name)
    monthly_inputs = load_monthly_inputs_from_db(engine, project_id, dataset_name)

    return contract_values, yearly_inputs, monthly_inputs


def load_contract_values_from_db(engine, project_id, dataset_name="actual"):
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        df = pd.read_sql_query(
            text(
                """
                SELECT *
                FROM contract_values
                WHERE dataset_config_id = :dataset_config_id
                ORDER BY agreement_year
                """
            ),
            connection,
            params={"dataset_config_id": dataset_config_id},
        )

    return {
        int(row.agreement_year): BessContractValues(
            agreement_year=int(row.agreement_year),
            cppf=float(row.cppf),
            cpppif=float(row.cpppif),
            ddd=float(row.ddd),
            ta=float(row.ta),
            rer=float(row.rer),
            ge=float(row.ge),
            design_dmax=float(row.design_dmax),
            design_duration_energy=float(row.design_duration_energy),
            annual_duration_energy_degradation_rate=float(
                row.annual_duration_energy_degradation_rate
            ),
            design_charge_energy=float(row.design_charge_energy),
            grid_system_waiting_period_hours=float(row.grid_system_waiting_period_hours),
            force_majeure_waiting_period_hours=float(
                row.force_majeure_waiting_period_hours
            ),
            scheduled_maintenance_allowance_hours=float(
                row.scheduled_maintenance_allowance_hours
            ),
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    }


def load_yearly_inputs_from_db(engine, project_id, dataset_name="actual"):
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        df = pd.read_sql_query(
            text(
                """
                SELECT *
                FROM yearly_inputs
                WHERE dataset_config_id = :dataset_config_id
                ORDER BY agreement_year
                """
            ),
            connection,
            params={"dataset_config_id": dataset_config_id},
        )

    return {
        int(row.agreement_year): BessYearlyInputs(
            agreement_year=int(row.agreement_year),
            dde=float(row.dde),
            tr=_optional_float(row, "tr"),
            gc=_optional_float(row, "gc"),
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    }


def load_monthly_inputs_from_db(engine, project_id, dataset_name="actual"):
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        df = pd.read_sql_query(
            text(
                """
                SELECT *
                FROM monthly_inputs
                WHERE dataset_config_id = :dataset_config_id
                ORDER BY agreement_year, timestamp_month
                """
            ),
            connection,
            params={"dataset_config_id": dataset_config_id},
        )

    return [
        BessMonthlyInputs(
            timestamp_month=_format_month(row.timestamp_month),
            agreement_year=int(row.agreement_year),
            adj=float(row.other_adj),
            bphrs=float(row.bphrs),
            pohrs=float(row.pohrs),
            unavhrs=float(row.unavhrs),
            unavprodhrs=float(row.unavprodhrs),
            gse=float(row.gse),
            pfm=float(row.pfm),
            ip=float(row.ip),
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    ]


def load_monthly_performance_guarantee_inputs_from_db(
    engine,
    project_id,
    dataset_name="actual",
):
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        df = pd.read_sql_query(
            text(
                """
                SELECT *
                FROM monthly_performance_guarantee
                WHERE dataset_config_id = :dataset_config_id
                ORDER BY agreement_year, timestamp_month
                """
            ),
            connection,
            params={"dataset_config_id": dataset_config_id},
        )

    return [
        BessMonthlyPerformanceGuaranteeInputs(
            timestamp_month=_format_month(row.timestamp_month),
            agreement_year=int(row.agreement_year),
            ce=float(row.ce),
            de=float(row.de),
            ae_beg=float(row.ae_beg),
            ae_end=float(row.ae_end),
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    ]


def load_performance_tests_from_db(engine, project_id, dataset_name="actual"):
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)
        df = pd.read_sql_query(
            text(
                """
                SELECT *
                FROM performance_tests
                WHERE dataset_config_id = :dataset_config_id
                ORDER BY agreement_year, test_date, test_id
                """
            ),
            connection,
            params={"dataset_config_id": dataset_config_id},
        )

    return [
        BessPerformanceTest(
            test_id=str(row.test_id),
            agreement_year=int(row.agreement_year),
            test_type=str(row.test_type),
            test_date=_format_date(row.test_date),
            requested_by=_optional_text(row, "requested_by"),
            tde=float(row.tde),
            measured_ramp_rate=_optional_float(row, "measured_ramp_rate", 0.0),
            certified_by=_optional_text(row, "certified_by"),
            prepa_approved=bool(row.prepa_approved),
            approval_date=_format_optional_date(row.approval_date),
            cure_or_retest_date=_format_optional_date(row.cure_or_retest_date),
            replaces_test_id=_optional_text(row, "replaces_test_id"),
            ramp_failure_caused_outage=bool(row.ramp_failure_caused_outage),
            outage_start=_format_optional_datetime(row.outage_start),
            outage_end=_format_optional_datetime(row.outage_end),
            outage_equivalent_unavhrs=_optional_float(
                row,
                "outage_equivalent_unavhrs",
                0.0,
            ),
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    ]


def load_inputs_snapshot(engine, project_id, dataset_name):
    with engine.connect() as connection:
        dataset_config_id = get_dataset_config_id(connection, project_id, dataset_name)

        def load(table, order_by):
            df = pd.read_sql_query(
                text(
                    f"""
                    SELECT *
                    FROM {table}
                    WHERE dataset_config_id = :dataset_config_id
                    ORDER BY {order_by}
                    """
                ),
                connection,
                params={"dataset_config_id": dataset_config_id},
            )
            return _df_to_records(df)

        return {
            "contract_values": load("contract_values", "agreement_year"),
            "yearly_inputs": load("yearly_inputs", "agreement_year"),
            "monthly_inputs": load("monthly_inputs", "agreement_year, timestamp_month"),
            "monthly_performance_guarantee": load(
                "monthly_performance_guarantee", "agreement_year, timestamp_month"
            ),
            "performance_tests": load(
                "performance_tests", "agreement_year, test_date, test_id"
            ),
        }


def _df_to_records(df):
    return [
        {col: _json_safe_value(val) for col, val in row.items()}
        for row in df.to_dict(orient="records")
    ]


def _json_safe_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _optional_text(row, field_name):
    if not hasattr(row, field_name):
        return ""
    value = getattr(row, field_name)
    if pd.isna(value):
        return ""
    return str(value)


def _optional_float(row, field_name, default=None):
    if not hasattr(row, field_name):
        return default
    value = getattr(row, field_name)
    if pd.isna(value):
        return default
    return float(value)


def _format_month(value):
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m")
    return str(value)[:7]


def _format_date(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _format_optional_date(value):
    if pd.isna(value):
        return ""
    return _format_date(value)


def _format_optional_datetime(value):
    if pd.isna(value):
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
