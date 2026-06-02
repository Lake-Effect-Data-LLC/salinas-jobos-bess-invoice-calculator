from calculations import (
    calculate_FA,
    calculate_FAA,
    calculate_actual_efficiency,
    calculate_annual_mcc,
    calculate_availability_liquidated_damages,
    calculate_capabability_payment_price,
    calculate_efficiency_liquidated_damages,
    calculate_included_POHRS,
    calculate_monthly_fixed_payment,
    calculate_monthly_payment,
    calculate_performance_test_mcc,
    calculate_risk_adjustment_with_waiting_periods,
)
from classes import BessMonthlyResult
from datetime import date


def calculate_monthly_results(
    contract_values,
    yearly_inputs,
    monthly_inputs,
    performance_tests=None,
    monthly_performance_guarantee_inputs=None,
):
    performance_tests = performance_tests or []
    performance_inputs_by_month = _map_monthly_performance_guarantee_inputs(
        monthly_performance_guarantee_inputs or []
    )
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
        applicable_test = get_applicable_performance_test(
            monthly_input.timestamp_month,
            monthly_input.agreement_year,
            performance_tests,
        )
        if applicable_test is None:
            mcc = calculate_annual_mcc(yearly.dde, contract.ddd, yearly.tr)
        else:
            mcc = calculate_performance_test_mcc(
                yearly.dde,
                contract.ddd,
                applicable_test.tde,
            )
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
        ald = calculate_availability_liquidated_damages(
            contract.ta,
            fa,
            yearly.dde,
            contract.rer,
            cpp,
        )
        pra = calculate_risk_adjustment_with_waiting_periods(
            monthly_input.bphrs,
            monthly_input.gse,
            monthly_input.pfm,
            monthly_input.ip,
            prior_gsehrs,
            prior_pfmhrs,
        )
        monthly_performance_input = performance_inputs_by_month.get(
            (monthly_input.agreement_year, monthly_input.timestamp_month)
        )
        actual_efficiency = None
        eld = 0.0
        if monthly_performance_input is not None:
            actual_efficiency = calculate_actual_efficiency(
                monthly_performance_input.de,
                monthly_performance_input.ce,
                monthly_performance_input.ae_beg,
                monthly_performance_input.ae_end,
            )
            eld = calculate_efficiency_liquidated_damages(
                contract.rer,
                cpp,
                monthly_performance_input.ce,
                contract.ge,
                monthly_performance_input.de,
                actual_efficiency,
            )
        adj_total = monthly_input.adj + ald + eld
        mfp = calculate_monthly_fixed_payment(cpp, mcc, faa, pra)
        mp = calculate_monthly_payment(mfp, adj_total)

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
                other_adj=monthly_input.adj,
                adj_total=adj_total,
                mp=mp,
                ald=ald,
                actual_efficiency=actual_efficiency,
                eld=eld,
            )
        )

    return results


def _map_monthly_performance_guarantee_inputs(monthly_performance_guarantee_inputs):
    return {
        (
            monthly_performance_input.agreement_year,
            monthly_performance_input.timestamp_month,
        ): monthly_performance_input
        for monthly_performance_input in monthly_performance_guarantee_inputs
    }


def get_applicable_performance_test(
    timestamp_month,
    agreement_year,
    performance_tests,
):
    # Source: Appendix F Section 3(c). MCC test adjustments take effect on the
    # first day of the Billing Period after the Billing Period containing the test.
    billing_period_start = _parse_month_start(timestamp_month)
    applicable_tests = [
        performance_test
        for performance_test in performance_tests
        if performance_test.agreement_year == agreement_year
        and performance_test.prepa_approved
        and _next_month_start(performance_test.test_date) <= billing_period_start
    ]

    if not applicable_tests:
        return None

    return max(
        applicable_tests,
        key=lambda performance_test: _parse_date(performance_test.test_date),
    )


def _get_agreement_year_values(values_by_year, agreement_year, value_name):
    try:
        return values_by_year[agreement_year]
    except KeyError as exc:
        raise ValueError(
            f"Missing {value_name} for agreement year {agreement_year}."
        ) from exc


def _next_month_start(value):
    current_month_start = _parse_month_start(value)
    if current_month_start.month == 12:
        return date(current_month_start.year + 1, 1, 1)

    return date(current_month_start.year, current_month_start.month + 1, 1)


def _parse_month_start(value):
    parsed_date = _parse_date(value)
    return date(parsed_date.year, parsed_date.month, 1)


def _parse_date(value):
    text_value = str(value)
    if len(text_value) == 7:
        text_value = f"{text_value}-01"

    try:
        return date.fromisoformat(text_value[:10])
    except ValueError as exc:
        raise ValueError(f"Invalid date value: {value}") from exc
