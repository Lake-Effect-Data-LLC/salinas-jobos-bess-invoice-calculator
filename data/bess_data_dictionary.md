# BESS Data Dictionary

This file records only sourced or user-provided input definitions. Formula syntax must be copied exactly from the source before implementation.

## Status Values

| Status | Meaning |
| --- | --- |
| `source-cited` | Defined by contract text or a cited contract page |
| `user-provided` | Provided by the user as source-of-truth working text |
| `derived` | Calculated from sourced inputs using a cited formula |
| `unknown` | Not ready for implementation |

## Contract-Defined Values

| Field | Definition | Unit | Source | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `CPPF` | Capability Payment Price Factor | unknown | Appendix F p. 109 per user note | unknown | Exact table values still needed |
| `CPPPIF` | Capability Payment Price Performance Index Factor | unknown | Appendix F pp. 109-110 per user note | unknown | Exact table values still needed |
| `DDD` | Design Dmax Duration | hours | Appendix F p. 129 per user-provided image | source-cited | Image says 4 hours |

## Yearly Inputs

| Field | Definition | Unit | Source | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `DDE` | Degraded Duration Energy | unknown | Appendix F p. 111 per user-provided image | source-cited | Needed for Monthly Contract Capability calculation; exact unit still needed |
| `TR` | Most recent Tested Result | unknown | Appendix F p. 111 per user-provided image | source-cited | Needed for Monthly Contract Capability calculation; exact unit still needed |

## Monthly Inputs

| Field | Definition | Unit | Source | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `timestamp_month` | Billing month timestamp | month | Appendix F section 4.3 per user-provided image | source-cited | Used to identify billing month; agreement-year mapping still needs a sourced rule |
| `ADJ` | Other credits or amounts | USD | Appendix F p. 108 per user-provided image | source-cited | Need exact sign convention and whether credits/deductions are netted |
| `BPHRS` | Total number of hours for Billing Period `n` | hours | Appendix F pp. 112-114 per user-provided contract text | source-cited | Used in FA and PRA formulas |
| `POHRS` | Total number of Permitted Outage Hours where the Facility was unavailable to deliver Adjusted Duration Energy or unable to accept Charge Energy in the Billing Period | hours | Appendix F pp. 112-113 per user-provided contract text | source-cited | Includes equivalent partial-hour treatment for Scheduled Outages, Resource Provider-declared Force Majeure, and Scheduled Deratings as described in source text |
| `UNAVHRS` | Total number of hours the Facility was unavailable to deliver Adjusted Duration Energy or unable to accept Charge Energy due to non-scheduled outage/derating, unapproved schedule extension, or Resource Provider declaring unavailability for reasons other than `POHRS` events | hours | Appendix F pp. 113-114 per user-provided contract text | source-cited | Partial hours count as equivalent percentage of applicable hour; deratings count only to extent of unavailable performance |
| `UNAVPRODHRS` | Total number of hours the Facility was unable to provide Product other than Energy due to events affecting other Products but not Energy, loss of certification, or Resource Provider declaring inability to provide other Product for reasons other than `POHRS` events | hours | Appendix F pp. 113-114 per user-provided contract text | source-cited | Hours counted as `UNAVHRS` are not also counted as `UNAVPRODHRS` |
| `GSE` | Hours lost due to grid system events not caused by PREPA force majeure | hours | Appendix F pp. 114-115 per user-provided image | source-cited | Used in PRA formula |
| `PFM` | Hours lost due to PREPA Force Majeure events | hours | Appendix F pp. 114-115 per user-provided image | source-cited | Used in PRA formula |
| `IP` | Hours lost for events where the Resource Provider can recover insurance proceeds | hours | Appendix F pp. 114-115 per user-provided image | source-cited | Example shown: business interruption |

## Formulas Not Yet Implemented

| Formula | Source | Status | Notes |
| --- | --- | --- | --- |
| Facility Availability `FA_n` | Appendix F pp. 112-114 per user-provided contract text/image | source-cited | `FA_n = (BPHRS_n - (POHRS_n + UNAVHRS_n + UNAVPRODHRS_n)) / (BPHRS_n - POHRS_n)` |
| Facility Availability Adjustment `FAA` | Appendix F pp. 112-113 per user-provided image | source-cited | Tiered adjustment factor derived from `FA_n` |
| PREPA Risk Availability `PRA_n` | Appendix F pp. 114-115 per user-provided image | source-cited | `PRA_n = (BPHRS_n - (GSE_n + PFM_n + IP_n)) / BPHRS_n` |

## FA vs FAA

| Term | Meaning | Role |
| --- | --- | --- |
| `FA_n` | Facility Availability for Billing Period `n` | Measured availability ratio calculated from monthly hour inputs |
| `FAA` | Facility Availability Adjustment | Payment adjustment factor selected from the tier table using `FA_n` |

## Facility Availability Adjustment Table

| Condition | `FAA` |
| --- | --- |
| `FA >= 98%` | `100%` |
| `70% < FA < 98%` | `100% - ((98% - FA) * 2)` |
| `FA < 70%` | `0%` |
