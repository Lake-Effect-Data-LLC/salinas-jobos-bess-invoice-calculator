# BESS Input Data Starting Point

This repo should move from solar/PPOA inputs to BESS compensation inputs before the calculation functions are rewritten.

The current source of truth for input design is the "All Data Required to Make Calculations" inventory from Appendix F:

- contract-defined values: `CPPF`, `CPPPIF`, and Design Dmax Duration (`DDD`)
- yearly collected values: Degraded Duration Energy (`DDE`) and most recent Tested Result (`TR`)
- monthly collected values: invoice month, adjustment amount (`ADJ`), Facility Availability (`FA`) variables, and PREPA Risk Availability (`PRA`) variables

The useful split is:

1. Contract-defined tables and constants: values copied from the contract, keyed by agreement year where needed.
2. Yearly operating inputs: tested/degraded capability values collected once per year or when a new test result is available.
3. Monthly billing inputs: period dates, adjustments, and monthly availability hour totals.
4. Optional support data: event detail or interval-level files only if we later need to audit how monthly hour totals were produced.

The first pass should calculate from the aggregate contract variables directly. Raw interval data can come later if needed.

## Proposed Monthly Files

| File | Purpose |
| --- | --- |
| `bess_contract_values_template.csv` | Contract-defined constants and agreement-year factors |
| `bess_yearly_inputs_template.csv` | Yearly `DDE` and `TR` values |
| `bess_monthly_inputs_template.csv` | Monthly `ADJ`, `FA`, and `PRA` variables |
| `bess_event_support_template.csv` | Optional event detail used to justify monthly hour totals |

## First Implementation Target

The first code milestone should be a BESS data reader that loads these templates into dataclasses and validates:

- required columns exist
- timestamps parse
- agreement year exists in the contract-value table
- billing period dates and `BP` are consistent
- `DDE`, `TR`, `BP`, `PO`, `UNAV`, `UNAVPROD`, `GSE`, `PFM`, `IP`, and `ADJ` are numeric
- monthly hour totals are non-negative
- monthly outage/risk hours do not exceed `BP` unless the contract explicitly allows overlapping categories
- adjustment rows include a reason and source reference when `ADJ` is non-zero

## Assumptions To Confirm

- `BP`, `PO`, `UNAV`, `UNAVPROD`, `GSE`, `PFM`, and `IP` are monthly aggregate hours supplied by operations or derived upstream.
- `ADJ` is a single net monthly adjustment unless Appendix F requires separate credits and charges.
- `CPPF` and `CPPPIF` are keyed by agreement year from the tables on pages 109-110.
- `DDD` is fixed at 4 hours unless an amendment changes it.
