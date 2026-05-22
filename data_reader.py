import pandas as pd

from classes import BessContractValues, BessMonthlyInputs, BessYearlyInputs


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


def _optional_text(row, field_name):
    if not hasattr(row, field_name):
        return ""

    value = getattr(row, field_name)
    if pd.isna(value):
        return ""

    return str(value)
