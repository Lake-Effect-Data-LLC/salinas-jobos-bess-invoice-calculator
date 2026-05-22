from calculations import (
    calculate_FA,
    calculate_FAA,
    calculate_annual_mcc,
    calculate_capabability_payment_price,
    calculate_included_POHRS,
    calculate_monthly_fixed_payment,
    calculate_monthly_payment,
    calculate_risk_adjustment_with_waiting_periods,
)
from classes import BessMonthlyResult


def calculate_monthly_results(contract_values, yearly_inputs, monthly_inputs):
    results = []
    prior_pohrs_by_year = {}
    prior_gsehrs_by_year = {}
    prior_pfmhrs_by_year = {}

    for monthly_input in sorted(
        monthly_inputs,
        key=lambda monthly_input: (
            monthly_input.agreement_year,
            monthly_input.timestamp_month,
        ),
    ):
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

        agreement_year = monthly_input.agreement_year
        prior_pohrs = prior_pohrs_by_year.get(agreement_year, 0.0)
        prior_gsehrs = prior_gsehrs_by_year.get(agreement_year, 0.0)
        prior_pfmhrs = prior_pfmhrs_by_year.get(agreement_year, 0.0)

        cpp = calculate_capabability_payment_price(contract.cppf, contract.cpppif)
        mcc = calculate_annual_mcc(yearly.dde, contract.ddd, yearly.tr)
        included_pohrs = calculate_included_POHRS(monthly_input.pohrs, prior_pohrs)
        excess_pohrs = monthly_input.pohrs - included_pohrs
        unavhrs = monthly_input.unavhrs + excess_pohrs
        fa = calculate_FA(
            monthly_input.bphrs,
            included_pohrs,
            unavhrs,
            monthly_input.unavprodhrs,
        )
        faa = calculate_FAA(fa)
        pra = calculate_risk_adjustment_with_waiting_periods(
            monthly_input.bphrs,
            monthly_input.gse,
            monthly_input.pfm,
            monthly_input.ip,
            prior_gsehrs,
            prior_pfmhrs,
        )
        mfp = calculate_monthly_fixed_payment(cpp, mcc, faa, pra)
        mp = calculate_monthly_payment(mfp, monthly_input.adj)

        prior_pohrs_by_year[agreement_year] = prior_pohrs + monthly_input.pohrs
        prior_gsehrs_by_year[agreement_year] = prior_gsehrs + monthly_input.gse
        prior_pfmhrs_by_year[agreement_year] = prior_pfmhrs + monthly_input.pfm

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
