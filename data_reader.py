import pandas as pd

from classes import (
    BessContractValues,
    BessMonthlyInputs,
    BessMonthlyPerformanceGuaranteeInputs,
    BessPerformanceTest,
    BessYearlyInputs,
)


def load_bess_inputs(
    contract_values_csv,
    yearly_inputs_csv,
    monthly_inputs_csv,
):
    contract_values = load_contract_values(contract_values_csv)
    yearly_inputs = load_yearly_inputs(yearly_inputs_csv)
    monthly_inputs = load_monthly_inputs(monthly_inputs_csv)

    return contract_values, yearly_inputs, monthly_inputs


def load_contract_values(csv_file_path):
    df = pd.read_csv(csv_file_path)

    return {
        int(row.agreement_year): BessContractValues(
            agreement_year=int(row.agreement_year),
            cppf=float(row.cppf),
            cpppif=float(row.cpppif),
            ddd=float(row.DDD),
            ta=_required_float(row, "TA"),
            rer=_required_float(row, "RER"),
            ge=_required_float(row, "GE"),
            design_dmax=_required_float(row, "design_dmax"),
            design_duration_energy=_required_float(row, "design_duration_energy"),
            annual_duration_energy_degradation_rate=_required_float(
                row,
                "annual_duration_energy_degradation_rate",
            ),
            design_charge_energy=_required_float(row, "design_charge_energy"),
            grid_system_waiting_period_hours=_required_float(
                row,
                "grid_system_waiting_period_hours",
            ),
            force_majeure_waiting_period_hours=_required_float(
                row,
                "force_majeure_waiting_period_hours",
            ),
            scheduled_maintenance_allowance_hours=_required_float(
                row,
                "scheduled_maintenance_allowance_hours",
            ),
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    }


def load_yearly_inputs(csv_file_path):
    df = pd.read_csv(csv_file_path)

    return {
        int(row.agreement_year): BessYearlyInputs(
            agreement_year=int(row.agreement_year),
            dde=float(row.DDE),
            gc=_optional_float(row, "GC", None),
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    }


def load_monthly_inputs(csv_file_path):
    df = pd.read_csv(csv_file_path)

    return [
        BessMonthlyInputs(
            timestamp_month=str(row.timestamp_month),
            agreement_year=int(row.agreement_year),
            adj=float(row.Other_ADJ),
            bphrs=float(row.BPHRS),
            pohrs=float(row.POHRS),
            unavhrs=float(row.UNAVHRS),
            unavprodhrs=float(row.UNAVPRODHRS),
            gse=float(row.GSE),
            pfm=float(row.PFM),
            ip=float(row.IP),
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    ]


def load_monthly_performance_guarantee_inputs(csv_file_path):
    df = pd.read_csv(csv_file_path)

    return [
        BessMonthlyPerformanceGuaranteeInputs(
            timestamp_month=str(row.timestamp_month),
            agreement_year=int(row.agreement_year),
            ce=float(row.CE),
            de=float(row.DE),
            ae_beg=float(row.AE_beg),
            ae_end=float(row.AE_end),
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    ]


def load_performance_tests(csv_file_path):
    # Source: Section 6.9, Supply Period Performance Tests.
    df = pd.read_csv(csv_file_path)

    return [
        BessPerformanceTest(
            test_id=str(row.test_id),
            agreement_year=int(row.agreement_year),
            test_type=str(row.test_type),
            test_date=str(row.test_date),
            requested_by=str(row.requested_by),
            tde=float(row.TDE),
            measured_ramp_rate=float(row.measured_ramp_rate),
            certified_by=_optional_text(row, "certified_by"),
            prepa_approved=_optional_bool(row, "prepa_approved"),
            approval_date=_optional_text(row, "approval_date"),
            cure_or_retest_date=_optional_text(row, "cure_or_retest_date"),
            replaces_test_id=_optional_text(row, "replaces_test_id"),
            ramp_failure_caused_outage=_optional_bool(
                row,
                "ramp_failure_caused_outage",
            ),
            outage_start=_optional_text(row, "outage_start"),
            outage_end=_optional_text(row, "outage_end"),
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


def _required_float(row, field_name):
    if not hasattr(row, field_name):
        raise ValueError(f"Required column '{field_name}' is missing from the CSV.")

    value = getattr(row, field_name)
    if pd.isna(value) or str(value).strip() == "":
        raise ValueError(
            f"Required field '{field_name}' is blank; a value must be provided."
        )

    return float(value)


def _optional_text(row, field_name):
    if not hasattr(row, field_name):
        return ""

    value = getattr(row, field_name)
    if pd.isna(value):
        return ""

    return str(value)


def _optional_bool(row, field_name, default=False):
    if not hasattr(row, field_name):
        return default

    value = getattr(row, field_name)
    if pd.isna(value) or str(value).strip() == "":
        return default

    if isinstance(value, bool):
        return value

    return _parse_bool_value(value, field_name)


def _parse_bool_value(value, field_name):
    text_value = str(value).strip().lower()
    if text_value in {"true", "t", "yes", "y", "1"}:
        return True
    if text_value in {"false", "f", "no", "n", "0"}:
        return False

    raise ValueError(
        f"Boolean field '{field_name}' has invalid value '{value}'. "
        "Use TRUE/FALSE, YES/NO, or 1/0."
    )


def _optional_float(row, field_name, default):
    if not hasattr(row, field_name):
        return default

    value = getattr(row, field_name)
    if pd.isna(value):
        return default

    return float(value)
