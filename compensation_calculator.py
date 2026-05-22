from calculations import (
    calculate_FA,
    calculate_FAA,
    calculate_capabability_payment_price,
    calculate_monthly_contract_capability,
    calculate_monthly_fixed_payment,
    calculate_monthly_payment,
    simple_calculate_risk_adjustment,
)
from classes import BessMonthlyResult


def calculate_monthly_results(contract_values, yearly_inputs, monthly_inputs):
    results = []

    for monthly_input in monthly_inputs:
        contract = _get_agreement_year_values(
            contract_values,
            monthly_input.agreement_year,
            "contract values",
        )
        yearly = _get_agreement_year_values(
            yearly_inputs,
            monthly_input.agreement_year,
            "yearly inputs",
        )

        cpp = calculate_capabability_payment_price(contract.cppf, contract.cpppif)
        mcc = calculate_monthly_contract_capability(yearly.dde, contract.ddd, yearly.tr)
        fa = calculate_FA(
            monthly_input.bphrs,
            monthly_input.pohrs,
            monthly_input.unavhrs,
            monthly_input.unavprodhrs,
        )
        faa = calculate_FAA(fa)
        pra = simple_calculate_risk_adjustment(
            monthly_input.bphrs,
            monthly_input.gse,
            monthly_input.pfm,
            monthly_input.ip,
        )
        mfp = calculate_monthly_fixed_payment(cpp, mcc, faa, pra)
        mp = calculate_monthly_payment(mfp, monthly_input.adj)

        results.append(
            BessMonthlyResult(
                timestamp_month=monthly_input.timestamp_month,
                agreement_year=monthly_input.agreement_year,
                cpp=cpp,
                mcc=mcc,
                fa=fa,
                faa=faa,
                pra=pra,
                mfp=mfp,
                adj=monthly_input.adj,
                mp=mp,
            )
        )

    return results


def _get_agreement_year_values(values_by_year, agreement_year, value_name):
    try:
        return values_by_year[agreement_year]
    except KeyError as exc:
        raise ValueError(
            f"Missing {value_name} for agreement year {agreement_year}."
        ) from exc
