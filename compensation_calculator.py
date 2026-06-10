from calculations import (
    calculate_FA,
    calculate_FAA,
    calculate_actual_efficiency,
    calculate_annual_mcc,
    calculate_availability_liquidated_damages,
    calculate_capability_liquidated_damages_per_day,
    calculate_capabability_payment_price,
    calculate_degraded_duration_energy,
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
        _validate_yearly_dde_matches_contract(contract, yearly)

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
            tested_result = derive_tested_result(
                monthly_input.agreement_year,
                contract_values,
                yearly_inputs,
                performance_tests,
            )
            mcc = calculate_annual_mcc(yearly.dde, contract.ddd, tested_result)
        else:
            mcc = calculate_performance_test_mcc(
                yearly.dde,
                contract.ddd,
                applicable_test.tde,
            )
        included_pohrs = calculate_included_POHRS(
            monthly_input.pohrs,
            prior_pohrs,
            contract.scheduled_maintenance_allowance_hours,
        )
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
        cld = calculate_monthly_capability_liquidated_damages(
            monthly_input.timestamp_month,
            monthly_input.agreement_year,
            performance_tests,
            yearly.dde,
            contract.rer,
            cpp,
            contract.cld_uses_dde_multiplier,
            yearly.gc,
        )
        pra = calculate_risk_adjustment_with_waiting_periods(
            monthly_input.bphrs,
            monthly_input.gse,
            monthly_input.pfm,
            monthly_input.ip,
            prior_gsehrs,
            prior_pfmhrs,
            contract.grid_system_waiting_period_hours,
            contract.force_majeure_waiting_period_hours,
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
                contract.eld_uses_ce_times_ge,
            )
        adj_total = monthly_input.adj + ald + cld + eld
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
                cld=cld,
                actual_efficiency=actual_efficiency,
                eld=eld,
            )
        )

    return results


def _validate_yearly_dde_matches_contract(contract, yearly):
    # Source: DDE definition plus Appendix J duration-energy degradation rate.
    # Current Salinas/Jobos Appendix J states 0% annual Duration Energy
    # degradation, so Yearly DDE should equal Design Duration Energy unless
    # a contract-supported upgrade/test override is documented separately.
    expected_dde = calculate_degraded_duration_energy(
        contract.design_duration_energy,
        contract.annual_duration_energy_degradation_rate,
        yearly.agreement_year,
    )
    tolerance = 0.01

    if abs(yearly.dde - expected_dde) > tolerance:
        raise ValueError(
            "Yearly DDE does not match contract-derived DDE for agreement "
            f"year {yearly.agreement_year}: input DDE={yearly.dde:.2f}, "
            f"derived DDE={expected_dde:.2f}. If this is due to a qualifying "
            "upgrade/test adjustment, document it before overriding the input."
        )


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
    #
    # Cross-year design: tests are filtered to the current agreement_year
    # because annual MCC uses a year-start Tested Result derived from prior
    # Performance Test history.
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


def derive_tested_result(
    agreement_year,
    contract_values,
    yearly_inputs,
    performance_tests,
):
    # Source: Appendix F Section 3(b). TR is the Tested Result used in the
    # annual MCC formula. Derive it from approved prior-year test history
    # instead of treating it as an independent yearly input.
    derived_results = {}
    for year in sorted(year for year in yearly_inputs if year <= agreement_year):
        contract = _get_agreement_year_values(contract_values, year, "contract values")
        if year == 1:
            derived_results[year] = contract.design_dmax
            continue

        prior_year = year - 1
        prior_tests = [
            performance_test
            for performance_test in performance_tests
            if performance_test.agreement_year == prior_year
            and performance_test.prepa_approved
        ]
        if not prior_tests:
            derived_results[year] = derived_results.get(
                prior_year,
                contract.design_dmax,
            )
            continue

        prior_contract = _get_agreement_year_values(
            contract_values,
            prior_year,
            "contract values",
        )
        prior_yearly = _get_agreement_year_values(
            yearly_inputs,
            prior_year,
            "yearly inputs",
        )
        last_test = max(
            prior_tests,
            key=lambda performance_test: _parse_date(performance_test.test_date),
        )
        derived_results[year] = calculate_performance_test_mcc(
            prior_yearly.dde,
            prior_contract.ddd,
            last_test.tde,
        )

    return derived_results[agreement_year]


def calculate_monthly_capability_liquidated_damages(
    timestamp_month,
    agreement_year,
    performance_tests,
    dde,
    rer,
    cpp,
    cld_uses_dde_multiplier=False,
    gc=None,
):
    # Source: Appendix P Section 2(b), Capability Liquidated Damages.
    # Salinas visual source:
    # docs/screenshots/CLD_06_Amend_(C-2-E)AES_Salinas_2023-0005_pg_230_220.png.
    # Jobos visual source provided in chat confirms no DDE multiplier.
    # Current allocation rule: count failed-test days that overlap the Billing
    # Period for approved tests, starting on the failed test date. The end date
    # is the next approved passing test date, then explicit cure/retest date if
    # provided, otherwise the end of the current Billing Period.
    billing_period_start = _parse_month_start(timestamp_month)
    billing_period_end = _next_month_start(timestamp_month)
    guaranteed_capability = dde if gc is None else gc
    monthly_cld = 0.0

    for performance_test in performance_tests:
        if performance_test.agreement_year != agreement_year:
            continue

        if not performance_test.prepa_approved:
            continue

        if performance_test.tde >= guaranteed_capability:
            continue

        test_date = _parse_date(performance_test.test_date)
        cld_end_date = _get_cld_end_date(
            performance_test,
            performance_tests,
            guaranteed_capability,
            billing_period_end,
        )
        # Day-boundary interpretation (Appendix P Section 2(b)):
        # "for each Day from the failed Performance Test until Resource Provider
        #  demonstrates TDE at or above DDE."
        # The failed test date is the first accrual day. The passing test/cure
        # date is the first resolved day and is excluded from CLD.
        # Example: failed test 2025-12-28, passing test 2026-01-05 means
        # Dec 28-31 and Jan 1-4 are charged.
        overlap_start = max(test_date, billing_period_start)
        overlap_end = min(cld_end_date, billing_period_end)
        cld_days = max((overlap_end - overlap_start).days, 0)

        if cld_days == 0:
            continue

        cld_per_day = calculate_capability_liquidated_damages_per_day(
            guaranteed_capability,
            performance_test.tde,
            rer,
            cpp,
            DDE=dde if cld_uses_dde_multiplier else None,
        )
        monthly_cld += cld_per_day * cld_days

    return monthly_cld


def _get_cld_end_date(
    failed_test,
    performance_tests,
    guaranteed_capability,
    billing_period_end,
):
    # Source: Appendix P Section 2(b). CLD applies from the failed test date
    # until Resource Provider demonstrates TDE at or above the guaranteed
    # capability. Prefer the next approved passing test row, then explicit
    # cure/retest date, then accrue through the current Billing Period end for
    # open-ended failures.
    passing_test_date = _get_next_passing_performance_test_date(
        failed_test,
        performance_tests,
        guaranteed_capability,
    )
    if passing_test_date is not None:
        return passing_test_date

    if failed_test.cure_or_retest_date:
        return _parse_date(failed_test.cure_or_retest_date)

    return billing_period_end


def _get_next_passing_performance_test_date(
    failed_test,
    performance_tests,
    guaranteed_capability,
):
    failed_test_date = _parse_date(failed_test.test_date)
    passing_test_dates = [
        _parse_date(performance_test.test_date)
        for performance_test in performance_tests
        if performance_test.agreement_year == failed_test.agreement_year
        and performance_test.prepa_approved
        and performance_test.tde >= guaranteed_capability
        and _parse_date(performance_test.test_date) > failed_test_date
        and _is_cure_test_for_failure(performance_test, failed_test)
    ]

    if not passing_test_dates:
        return None

    return min(passing_test_dates)


def _is_cure_test_for_failure(performance_test, failed_test):
    if performance_test.replaces_test_id:
        return performance_test.replaces_test_id == failed_test.test_id

    return True


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
