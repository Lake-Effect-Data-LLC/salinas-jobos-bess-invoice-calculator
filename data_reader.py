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
            ta=_optional_float(row, "TA", 0.70),
            rer=_optional_float(row, "RER", 170.00),
            ge=_optional_float(row, "GE", 0.97),
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
            tr=float(row.TR),
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
            adj=float(row.ADJ),
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
            source_reference=_optional_text(row, "source_reference"),
            notes=_optional_text(row, "notes"),
        )
        for row in df.itertuples(index=False)
    ]


def _optional_text(row, field_name):
    if not hasattr(row, field_name):
        return ""

    value = getattr(row, field_name)
    if pd.isna(value):
        return ""

    return str(value)


def _optional_bool(row, field_name):
    if not hasattr(row, field_name):
        return False

    value = getattr(row, field_name)
    if pd.isna(value):
        return False

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"true", "t", "yes", "y", "1"}


def _optional_float(row, field_name, default):
    if not hasattr(row, field_name):
        return default

    value = getattr(row, field_name)
    if pd.isna(value):
        return default

    return float(value)
