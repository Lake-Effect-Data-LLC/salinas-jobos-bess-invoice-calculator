# BESS Input Data Starting Point

This repo should move from solar/PPOA inputs to BESS compensation inputs before the calculation functions are rewritten.

The current source of truth for input design is the "All Data Required to Make Calculations" inventory from Appendix F:

- contract-defined values: `CPPF`, `CPPPIF`, and Design Dmax Duration (`DDD`)
- yearly collected values: Degraded Duration Energy (`DDE`) and most recent Tested Result (`TR`)
- monthly collected values: invoice month, adjustment amount (`ADJ`), Facility Availability (`FA`) variables, and PREPA Risk Availability (`PRA`) variables

The current working split is:

1. Contract-defined tables and constants: values copied from the contract, keyed by agreement year where needed.
2. Yearly operating inputs: `DDE` and `TR`.
3. Monthly billing inputs: timestamp month, `ADJ`, Facility Availability variables, and PREPA Risk Availability variables.

No calculation should be implemented until each input is tied to a cited source page, table, or user-provided source-of-truth note.

See `bess_data_dictionary.md` for the working input dictionary.

## Monthly Files

| File | Purpose |
| --- | --- |
| `bess_contract_values_template.csv` | Contract-defined constants and agreement-year factors |
| `bess_yearly_inputs_template.csv` | Yearly `DDE` and `TR` values |
| `bess_monthly_inputs_template.csv` | Monthly `ADJ`, `FA`, and `PRA` variables |

## First Implementation Target

The first code milestone should be a BESS data reader that loads these templates into dataclasses and validates only facts we have sourced:

- required columns exist
- timestamps parse
- agreement year can be determined from the monthly timestamp using a sourced rule
- `DDE`, `TR`, `BPHRS`, `POHRS`, `UNAVHRS`, `UNAVPRODHRS`, `GSE`, `PFM`, `IP`, and `ADJ` are numeric
- monthly hour totals are non-negative
- monthly outage/risk hours do not exceed `BPHRS` where the cited formula requires it
- adjustment rows include a reason and source reference when `ADJ` is non-zero

## Open Questions Before Implementation

- Does Appendix F treat `ADJ` as one net monthly adjustment, or as separate credits and deductions?
- What are the exact `CPPF` values by agreement year from page 109?
- What are the exact `CPPPIF` values by agreement year from pages 109-110?
- Does any amendment alter `DDD` from the 4-hour value noted on page 129?
- What sourced rule maps `timestamp_month` to `agreement_year`?
