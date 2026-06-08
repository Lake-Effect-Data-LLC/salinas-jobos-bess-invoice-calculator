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
| `classes.BessMonthlyResult` | Stores `other_adj`, `ald`, `eld`, `adj_total`, `mp` |

Open issue:

- `ALD` and `ELD` are currently included in `ADJ_Total`. Confirm source `ADJ`
  inputs exclude calculated liquidated damages so the calculator does not
  double-count PREPA credits.
- `CLD` is not yet allocated into monthly `ADJ_Total`.

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
- Annual replacement is modeled by Agreement Year. If annual adjustment timing
  can occur mid-year, the input model needs an explicit annual-adjustment date.
- `DDE` is currently an input, not derived.

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

Current implementation:

| Code/Input | Status |
| --- | --- |
| `bess_yearly_inputs_template.csv` | Requires `DDE` as yearly input |
| `calculations.py` | Uses `DDE`, does not derive it |

Open issue:

- Add degradation-factor and qualifying-upgrade-test logic only after the exact
  annual degradation table and upgrade-test rules are confirmed.

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
| `calculations.calculate_FA_with_included_POHRS` | Supports permitted-outage allowance handling |

Open issue:

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
| `calculations.calculate_risk_adjustment_with_waiting_periods` | Implemented with annual waiting-period caps |

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

Contract rule, subject to visual formula confirmation:

```text
CLD = (GC - TDE) x (RER - CPP / (30.33 x 24))
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
| `calculations.calculate_capability_liquidated_damages_per_day` | Formula helper exists |

Open issues:

- Monthly CLD allocation is not implemented.
- Inputs need enough event timing to allocate CLD: failed test date, TDE,
  cure/retest date or deficiency days, and the applicable agreement year values.
- The Salinas extracted formula appears to include an extra `DDE` multiplier,
  while Jobos and prior contract text do not. Treat this as an extraction/PDF
  confirmation item before changing the formula.

## Efficiency And ELD

Contract rules:

```text
Actual Efficiency = (DE + (AEend - AEbeg)) / CE

ELD = (RER - CPP / (30.33 x 24)) x ((CE x GE) - DE)
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
| `calculations.calculate_efficiency_liquidated_damages` | Implemented |
| `compensation_calculator.calculate_monthly_results` | Includes `ELD` in `ADJ_Total` |

Open issue:

- Salinas extracted formula text shows `((CE - GE) - DE)`, which conflicts with
  the variable definition and Jobos extracted formula `((CE x GE) - DE)`. Treat
  the multiplication version as the current working interpretation, and confirm
  Salinas against the original PDF before final delivery.

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
| `Performance_Tests.csv` | Has `measured_ramp_rate` |
| `compensation_calculator.py` | Does not calculate outage hours from ramp failure |

Open issue:

- Decide whether ramp-rate failure is manually reflected in `UNAVHRS` or should
  be automatically derived from failed test/cure dates.

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
| `report.generate_bess_invoice_support_report` | Generates `report.txt` from monthly results |
| `main.py` | Writes `output/<project_id>/report.txt` |

Open issue:

- The current report is a calculation support report, not yet a full contract
  invoice package with ancillary services, green credits, balance, supporting
  meter statements, or insurance detail.
