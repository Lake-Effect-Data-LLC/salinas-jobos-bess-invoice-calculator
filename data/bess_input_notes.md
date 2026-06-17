# BESS Input Data Starting Point

This repo should move from solar/PPOA inputs to BESS compensation inputs before the calculation functions are rewritten.

The current source of truth for input design is the "All Data Required to Make Calculations" inventory from Appendix F:

- contract-defined values: `CPPF`, `CPPPIF`, and Design Dmax Duration (`DDD`)
- yearly collected or derived values: Degraded Duration Energy (`DDE`), Tested Result (`TR`), and optional Guaranteed Capability (`GC`)
- monthly collected values: invoice month, adjustment amount (`ADJ`), Facility Availability (`FA`) variables, and PREPA Risk Availability (`PRA`) variables

The current working split is:

1. Contract-defined tables and constants: values copied from the contract, keyed by agreement year where needed.
   - Appendix P / Appendix J constants now tracked with contract values include `TA`, `RER`, `GE`, `design_dmax`, `design_duration_energy`, and `design_charge_energy`.
2. Yearly operating inputs: `DDE`, `TR`, and optional `GC`.
   - Current sample data assumes Design Dmax of 100 MW, Design Dmax Duration of 4 hours, Design Duration Energy of 400 MWh, and 0% annual duration energy degradation, so sample `DDE` is 400 MWh.
   - `DDE` is currently accepted as a sourced yearly input. Contractually, `DDE` means Design Duration Energy adjusted downward by the applicable Energy Degradation Factor and adjusted upward by qualifying Performance Tests after maintenance or technology upgrades, capped at Design Duration Energy. Future versions should derive `DDE` when degradation factors and qualifying upgrade/maintenance test data are available.
   - `TR` is accepted as an externally supplied yearly input for annual MCC. The calculator does not derive it from `TDE` or prior Performance Test history.
3. Monthly billing inputs: timestamp month, `ADJ`, Facility Availability variables, and PREPA Risk Availability variables.
4. Monthly performance guarantee inputs: monthly metered efficiency values `CE`, `DE`, `AE_beg`, and `AE_end`.
5. Performance test inputs: event-based test records containing `TDE`, measured ramp rate, test date, approval status/date, and any cure or retest date.
   - Source: Section 6.9 (Supply Period Performance Tests) defines PREPA and Resource Provider Performance Tests, certification/approval requirements, and use of Tested Duration Energy.
   - Source: Appendix F Section 3(c) defines the MCC adjustment formula and states that test adjustments take effect on the first Day of the Billing Period following the Billing Period in which the Performance Test occurred.
   - Source: Appendix P Sections 2 and 4 use Performance Tests for Capability and Ramp Rate guarantees.
6. Report / invoice presentation should follow Section 10.1, which requires the written invoice to include, as applicable, Monthly Fixed Payment, Other Payment Adjustments, Discharge Energy, Charge Energy, Ancillary Services, Green Credits, Balance, Facility performance support, insurance payments, credits or payments owing to PREPA, and an itemized statement of other charges.
   - Working assumption: Appendix F `ADJ` includes other credits or amounts to which PREPA has a right under the Agreement, so calculated Appendix P `ALD` and `ELD` are included in `ADJ_Total` and reduce `MP`.
   - Source `ADJ` inputs should exclude calculated LDs unless double-counting is intended and documented.

No calculation should be implemented until each input is tied to a cited source page, table, or user-provided source-of-truth note.

See `bess_data_dictionary.md` for the working input dictionary.

## Monthly Files

| File | Purpose |
| --- | --- |
| `bess_contract_values_template.csv` | Contract-defined constants and agreement-year factors |
| `bess_yearly_inputs_template.csv` | Yearly `DDE`, `TR`, and optional `GC` values |
| `bess_monthly_inputs_template.csv` | Monthly `ADJ`, `FA`, and `PRA` variables |
| `Monthly_Performance_Guarantee.csv` | Monthly metered values for Appendix P Efficiency Guarantee (`CE`, `DE`, `AE_beg`, `AE_end`) |
| `Performance_Tests.csv` | Event-based Appendix P / Section 6.9 performance test data (`TDE`, ramp rate, dates, approval) |
| `Monthly_Compensation.csv` | Friendly sample version of monthly compensation inputs |
| `Yearly.csv` | Friendly sample version of yearly inputs |

## Performance Guarantees

Guaranteed Efficiency = 97%
Full Duty Cycle Efficiency = 85.30%
Design Dmax = 100 MW
Design Dmax Duration = 4 hours
Design Storage Energy = 400 MWh
Design Duration Energy = 400 MWh
Design Charge Energy = 482 MWh
Design Charge Duration = 4.82 hours
Battery Power / Energy at Metering Location = 103,380 kW / 421,260 kWh


## Open Questions Before Implementation

- Does Appendix F treat `ADJ` as one net monthly adjustment, or as separate credits and deductions?
- Should `DDE` be derived from Energy Degradation Factors and qualifying Section 4.7 upgrade/maintenance tests, or continue as a sourced yearly input?
- Confirm whether Performance Test completion date, PREPA approval date, or certified report date controls year-start Tested Result derivation and MCC cure timing.
- Confirm that source `ADJ` inputs exclude calculated Appendix P liquidated damages now included in `ADJ_Total`.
- How should total `CLD` be allocated when a failed Performance Test spans multiple Billing Periods before cure/retest?
