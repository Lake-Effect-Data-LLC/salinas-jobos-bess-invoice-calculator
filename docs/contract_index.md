# Contract Source Index

This index maps the invoice calculator to the contract sections that control
each calculation. Use it as a source map when checking Salinas and Jobos inputs,
formulas, reports, and remaining implementation gaps.

The extracted text files are generated from the PDFs and DOCX files in `docs/`.
Some formulas contain OCR/text-extraction artifacts, especially mathematical
symbols. When a formula looks inconsistent, confirm against the original PDF
page before changing code.

## Source Priority

Use this order when sources conflict:

1. Latest executed amendment with readable contract text.
2. Original ESSA, when the amendment does not replace or alter the section.
3. Monthly payment DOCX files as navigation/support notes only.

Current controlling readable sources:

| Project | Primary readable amendment | Base agreement | Support doc |
| --- | --- | --- | --- |
| Salinas | `docs/text/salinas/06_Amend_(C-2-E)AES_Salinas_2023-00053.txt` | `docs/text/salinas/ESSA_(C-2-E)AES_Salinas_2023-P00053.txt` | `docs/text/salinas/Salinas_BESS_Monthly_Payment_Calculation.txt` |
| Jobos | `docs/text/jobos/05_Amend_(A-2-E)AES_Jobos_2023-P00052.txt` | `docs/text/jobos/ESSA_(A-2-E)AES_Jobos_2023-P00052.txt` | `docs/text/jobos/Jobos_BESS_Monthly_Payment_Calculation.txt` |

Later amendments with weak extracted text should remain in the repo, but should
be visually reviewed or OCR'd before relying on them:

| Project | File | Extraction note |
| --- | --- | --- |
| Salinas | `docs/text/salinas/07_Amend_(C-2-E)AES_Salinas_2023-P00053G.txt` | Very short extracted text relative to PDF size |
| Jobos | `docs/text/jobos/06_Amend_(A-2-E)AES_Jobos_2023-P00052F.txt` | Very short extracted text relative to PDF size |

## Monthly Payment

Contract rule:

```text
MPn = MFPn - ADJn
```

`ADJn` is defined as other credits or amounts to which PREPA has a right under
the Agreement.

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Appendix F Section 1, extracted text around lines 4883-4890 |
| Jobos | 05 Amendment, Appendix E/A Section 1, extracted text around lines 4831-4838 |

Current implementation:

| Code | Status |
| --- | --- |
| `calculations.calculate_monthly_payment` | Implemented as `MFP - ADJ` |
| `compensation_calculator.calculate_monthly_results` | Uses `ADJ_Total` |
| `classes.BessMonthlyResult` | Stores `other_adj`, `ald`, `cld`, `eld`, `adj_total`, `mp` |

Open issue:

- `ALD`, `CLD`, and `ELD` are currently included in `ADJ_Total`. The monthly
  input column is named `Other_ADJ` to signal that operator-entered adjustments
  must exclude calculated LDs; however there is no programmatic check that a
  user has not entered an LD amount there. Confirm source inputs exclude
  calculated liquidated damages before submitting any invoice where both an LD
  was calculated and `Other_ADJ` is non-zero in the same billing period.

## Monthly Fixed Payment

Contract rule:

```text
MFPn = CPP x MCCn x FAAn x PRAn
CPP = CPPF + CPPPIF
```

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Appendix F Section 2, extracted text around lines 4895-4991 |
| Jobos | 05 Amendment, Appendix E/A Section 2, extracted text around lines 4843-4936 |

Current implementation:

| Code | Status |
| --- | --- |
| `calculations.calculate_capabability_payment_price` | Implemented as `CPPF + CPPPIF` |
| `calculations.calculate_monthly_fixed_payment` | Implemented as `CPP * MCC * FAA * PRA` |
| `classes.BessContractValues` | Loads design reference values and Appendix J degradation rate from the contract CSV |

Open issue:

- The amendment text includes possible project-specific CPPPIF downward
  adjustment language if estimated interconnection cost exceeds the referenced
  reimbursement/contracted amount. That adjustment is not separately modeled;
  current inputs assume the final applicable `CPPPIF` is provided.

## Monthly Contract Capability

Contract rules:

```text
At COD: MCC = Design Dmax

At year end:
MCCy = min(DDE / DDD, TR)

After Performance Tests:
If TDE < 99% of DDE: MCC = TDE / DDD
If TDE >= 99% of DDE: MCC = DDE / DDD
```

The Performance Test adjustment starts on the first day of the Billing Period
after the Billing Period in which the Performance Test occurred. It continues
until another Performance Test is completed or the annual adjustment is made.

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Appendix F Section 3, extracted text around lines 4992-5028 |
| Jobos | 05 Amendment, Appendix E/A Section 3, extracted text around lines 4937-4978 |
| Both | Section 6.9 Supply Period Performance Tests, extracted Salinas lines 2510-2538 and Jobos lines 2469-2497 |

Current implementation:

| Code | Status |
| --- | --- |
| `calculations.calculate_performance_test_mcc` | Implements the 99% `TDE` test |
| `calculations.calculate_annual_mcc` | Implements fallback `min(DDE / DDD, TR)` |
| `compensation_calculator.get_applicable_performance_test` | Selects latest approved test effective in the next billing month |

Open issues:

- Code currently requires `prepa_approved = TRUE`. Section 6.9 supports an
  approval process, but Appendix F says the adjustment continues until another
  Performance Test is completed. Confirm whether completion date, approval date,
  or approved report date controls the effective test.
- `DDE` is currently a yearly input, but it is validated against the contract
  values file using Design Duration Energy and Annual Duration Energy
  Degradation Rate.
- Cross-year MCC carry: `get_applicable_performance_test` filters tests to the
  current `agreement_year`. Tests from a prior agreement year do not carry
  forward automatically because the annual formula `MCCy = min(DDE/DDD, TR)`
  resets MCC at the year boundary. `TR` in `bess_yearly_inputs_template.csv`
  is the intended carry-forward mechanism. Data entry rule for `TR`:
  - Agreement Year 1 at COD, no prior tests: `TR = design_dmax` (MW).
  - Last Year N-1 test had `TDE < 0.99 × DDE_last`: `TR = TDE_last / DDD`.
  - Last Year N-1 test had `TDE >= 0.99 × DDE_last`: `TR = DDE_last / DDD`.
  - No approved tests in Year N-1: carry Year N-1 `TR` forward unchanged.
  Failing to update `TR` after a below-threshold year-end test will overstate
  MCC in the new agreement year. Input validation now warns when Year N `TR`
  exceeds `TDE_last / DDD` after the last approved Year N-1 test was below
  `0.99 × DDE_last`. See also the comment in
  `compensation_calculator.get_applicable_performance_test`.

## Degraded Duration Energy

Contract definition:

`DDE` means Design Duration Energy for each Agreement Year, adjusted downward by
the Energy Degradation Factor and adjusted upward by qualifying Performance
Tests after maintenance or technology upgrades, capped at Design Duration
Energy.

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment definitions, extracted text around lines 707-710 |
| Jobos | 05 Amendment definitions, extracted text around lines 657-660 |
| Jobos | Amended Appendix J Operating Characteristics: Design Dmax `100 MW`, Design Dmax Duration `4 hours`, Design Duration Energy `400 MWh`, Design Charge Energy `468 MWh`, Guaranteed Efficiency `85%`, ramp rates `6,000 MW/min` |

Current implementation:

| Code/Input | Status |
| --- | --- |
| `bess_yearly_inputs_template.csv` | Requires `DDE` as yearly input |
| `bess_contract_values_template.csv` | Provides `design_duration_energy` and `annual_duration_energy_degradation_rate` |
| `calculations.calculate_degraded_duration_energy` | Derives expected DDE from design energy and annual degradation |
| `compensation_calculator.calculate_monthly_results` | Validates yearly input DDE against derived DDE |

Open issue:

- Appendix J currently states Annual Duration Energy Degradation Rate is `0%`
  per Agreement Year, so current Salinas/Jobos DDE should equal Design Duration
  Energy. Qualifying upgrade/test upward adjustments are not automatically
  modeled; if one applies, document it before overriding the yearly DDE input.
- Jobos Appendix J values have been visually confirmed and match the current
  Jobos contract values file for `design_dmax`, `DDD`,
  `design_duration_energy`, `design_charge_energy`, and `GE`.

## Facility Availability And FAA

Contract rules:

```text
FA = (BPHRS - (POHRS + UNAVHRS + UNAVPRODHRS)) / (BPHRS - POHRS)

FAA:
FA >= 98%: 100%
70% < FA < 98%: 100% - ((98% - FA) x 2)
FA < 70%: 0%
```

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Appendix F Section 4, extracted text around lines 5029-5151 |
| Jobos | 05 Amendment, Appendix E/A Section 4, extracted text around lines 4979-5101 |

Current implementation:

| Code | Status |
| --- | --- |
| `calculations.calculate_FA` | Implemented |
| `calculations.calculate_FAA` | Implemented |
| `calculations.calculate_FA_with_included_POHRS` | Supports permitted-outage allowance handling and shifts excess POHRS into unavailable hours |
| `bess_contract_values_template.csv` | Provides `scheduled_maintenance_allowance_hours` |

Open issue:

- The FAA table has a boundary gap at exactly `70%`: middle band is greater than
  `70%`, zero band is less than `70%`. Current code treats exactly `70%` as the
  last non-zero point, producing `44%`; confirm contract-owner intent before
  relying on that boundary month.
- Ramp-rate failure places the Facility into a Non-Scheduled Outage under
  Appendix P Section 4, but code does not automatically convert failed ramp
  tests into `UNAVHRS`.

## PREPA Risk Adjustment

Contract rule:

```text
PRA = (BPHRS - (GSEHRS + PFMHRS + IPHRS)) / BPHRS
```

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Appendix F Section 5, extracted text around lines 5152-5190 |
| Jobos | 05 Amendment, Appendix E/A Section 5, extracted text around lines 5102-5139 |

Current implementation:

| Code | Status |
| --- | --- |
| `calculations.calculate_risk_adjustment_with_waiting_periods` | Implemented with contract-specific annual waiting-period caps |
| `bess_contract_values_template.csv` | Provides `grid_system_waiting_period_hours` and `force_majeure_waiting_period_hours` |

Open issue:

- Confirm whether any insurance-recovery event should be represented only in
  `IPHRS` or also itemized in `report.txt`.

## Availability Liquidated Damages

Contract rule:

```text
ALD = (TA - FA) x DDE x (RER - CPP / (30.33 x 24))
```

The damages apply if Facility Availability falls below Threshold Availability
during a Billing Period.

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Appendix P Section 1, extracted text around lines 8899-8917 |
| Jobos | 05 Amendment, Appendix P Section 1, extracted text around lines 8891-8910 |

Current implementation:

| Code | Status |
| --- | --- |
| `calculations.calculate_availability_liquidated_damages` | Implemented, returns zero unless `FA < TA` |
| `compensation_calculator.calculate_monthly_results` | Includes `ALD` in `ADJ_Total` |

Open issue:

- Contract wording says ALD is for each hour of such Billing Period, while the
  extracted formula uses Billing Period FA and yearly DDE. Current code returns
  the formula result once per Billing Period, not multiplied by every billing
  hour. Confirm intended invoice presentation against a worked example.

## Capability Liquidated Damages

Current working contract rules:

```text
Salinas CLD = (GC - TDE) x DDE x (RER - CPP / (30.33 x 24))
Jobos CLD = (GC - TDE) x (RER - CPP / (30.33 x 24))
```

CLD applies for each Day from the failed Performance Test until Resource
Provider demonstrates TDE at or above DDE.

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Appendix P Section 2, extracted text around lines 8931-8948 |
| Jobos | 05 Amendment, Appendix P Section 2, extracted text around lines 8924-8941 |

Current implementation:

| Code | Status |
| --- | --- |
| `calculations.calculate_capability_liquidated_damages_per_day` | Supports CLD with or without a `DDE` multiplier |
| `compensation_calculator.calculate_monthly_capability_liquidated_damages` | Allocates CLD across Billing Periods for approved failed tests until passing retest, explicit cure/retest date, or current Billing Period end |
| `data_writer.write_bess_monthly_results` | Writes `CLD` and includes it in `ADJ_Total` |
| `bess_contract_values_template.csv` | Uses `CLD_uses_DDE_multiplier` to select the project formula |
| `bess_yearly_inputs_template.csv` | Optional `GC` column can override the default `GC = DDE` assumption |

Open issues:

- Salinas contract text (06 Amendment Appendix P Section 2(b)) confirms the
  CLD formula includes a `DDE` multiplier:
  `CLD = (GC - TDE) x DDE x (RER - CPP / (30.33 x 24))`.
  Code path: `CLD_uses_DDE_multiplier = TRUE`.
- Jobos contract text (05 Amendment Appendix P Section 2(b)) confirms the CLD
  formula omits the `DDE` multiplier:
  `CLD = (GC - TDE) x (RER - CPP / (30.33 x 24))`.
  Code path: `CLD_uses_DDE_multiplier = FALSE`.
- Day-boundary interpretation: the contract says "for each Day from the failed
  Performance Test until Resource Provider demonstrates TDE at or above DDE."
  Current code treats the test date as the first accrual day (included) and the
  passing test/cure date as the day the shortfall is resolved (excluded). A
  failed test on Dec 28 with passing test on Jan 5 accrues 8 days: Dec 28-31
  and Jan 1-4. Confirm against a worked invoice example or counsel opinion
  before disputing an invoice where the cure-day boundary is contested.
- Open-ended approved failed tests accrue through the current Billing Period
  end. If a later approved passing test row exists, that test date ends the CLD
  period. If no passing row exists but `cure_or_retest_date` is populated, that
  explicit date is used as the end date.
- Current CLD allocation requires `prepa_approved = TRUE`, then accrues from the
  test date. Confirm whether LD accrual should instead begin on approval date.
- Current Salinas and Jobos inputs omit `GC`, so the calculator defaults
  Guaranteed Capability to `DDE`. Add yearly `GC` if a future contract defines
  Guaranteed Capability separately.

## Efficiency And ELD

Contract rules:

```text
Actual Efficiency = (DE + (AEend - AEbeg)) / CE

Salinas ELD = (RER - CPP / (30.33 x 24)) x ((CE - GE) - DE)
Jobos ELD = (RER - CPP / (30.33 x 24)) x ((CE x GE) - DE)
```

ELD applies if Actual Efficiency for the Billing Period falls below Guaranteed
Efficiency.

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Appendix P Section 3, extracted text around lines 8950-9004 |
| Jobos | 05 Amendment, Appendix P Section 3, extracted text around lines 8943-9001 |

Current implementation:

| Code | Status |
| --- | --- |
| `calculations.calculate_actual_efficiency` | Implemented |
| `calculations.calculate_efficiency_liquidated_damages` | Supports ELD with either `CE - GE` or `CE x GE` |
| `compensation_calculator.calculate_monthly_results` | Includes `ELD` in `ADJ_Total` |
| `bess_contract_values_template.csv` | Uses `ELD_uses_CE_times_GE` to select the project formula |

Open issue:

- Salinas contract text (06 Amendment Appendix P Section 3(c)) shows
  `((CE - GE) - DE)`. This is dimensionally inconsistent: `CE` and `DE` are
  in MWh but `GE` is a unitless decimal fraction. Current code follows the
  literal text with `ELD_uses_CE_times_GE = FALSE`.
- Jobos contract text (05 Amendment Appendix P Section 3(c)) shows
  `((CE x GE) - DE)`. Dimensionally consistent. Code: `ELD_uses_CE_times_GE = TRUE`.
- If counsel, a worked invoice example, or an official PREPA model treats the
  Salinas formula as a drafting error, change Salinas `ELD_uses_CE_times_GE`
  to `TRUE`.

## Ramp Rate

Contract rule:

Guaranteed Ramp Rate is ten percent of Facility DDE per minute. If the Facility
cannot demonstrate the Guaranteed Ramp Rate, it must enter a Non-Scheduled
Outage until resolved.

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Appendix P Section 4, extracted text around lines 9005-9011 |
| Jobos | 05 Amendment, Appendix P Section 4, extracted text around lines 9002-9008 |

Current implementation:

| Input/Code | Status |
| --- | --- |
| `Performance_Tests.csv` | Has `measured_ramp_rate`, `ramp_failure_caused_outage`, `outage_start`, `outage_end`, and `outage_equivalent_unavhrs` |
| `compensation_calculator.py` | Does not calculate outage hours from ramp failure |
| `error_checks.validate_input_files` | Requires outage detail fields when `ramp_failure_caused_outage = TRUE` |

Open issue:

- Current data model can capture ramp-failure outage detail, but those hours are
  not automatically added to monthly `UNAVHRS`. Until that is intentionally
  wired in, users must also reflect the availability impact in
  `bess_monthly_inputs_template.csv`.

## Invoice Report Requirements

Contract requirement:

Monthly invoices must include the Monthly Fixed Payment, Other Payment
Adjustments, Discharge Energy, Charge Energy, Ancillary Services, Green Credits,
Balance, information necessary to determine Facility performance, insurance
payments, credits or payments owing to PREPA, and an itemized statement of all
other charges under the Agreement.

Sources:

| Project | Source |
| --- | --- |
| Salinas | 06 Amendment, Section 10.1, extracted text around lines 2945-2955 |
| Jobos | 05 Amendment, Section 10.1, extracted text around lines 2905-2915 |

Current implementation:

| Code | Status |
| --- | --- |
| `report.generate_bess_invoice_support_report` | Generates project-specific `report.txt` from monthly results |
| `main.py` | Writes `output/<project_id>/report.txt` |

Open issue:

- The current report is a calculation support report, not yet a full contract
  invoice package with ancillary services, green credits, balance, supporting
  meter statements, or insurance detail.

