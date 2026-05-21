# Notion Template for LUMA Invoicing Projects

This document is a copy-ready starting point for the Notion workspace that will sit on top of:

- local/shared-drive documents in `X:\LUMA`
- project code in Git repos
- project notes and operating decisions

The goal is simple: keep Notion as the curated interpretation layer, not the raw archive.

## Workspace Structure

Create three databases:

1. `Projects`
2. `Documents`
3. `Implementation Map`

If you want to start smaller, build `Projects` first and add the other two later.

## Projects Database

### Recommended Properties

| Property | Type | Purpose |
| --- | --- | --- |
| Project Name | Title | Human-readable project name |
| Facility | Multi-select | Plant or facility names |
| Service Type | Multi-select | Example: `PPOA`, `BESS` |
| Counterparty | Text | Contracting entity or vendor |
| Status | Select | Example: `Active`, `Onboarding`, `Paused`, `Archived` |
| Drive Root | URL or Text | Root path in `X:\LUMA` |
| Contract Folder | Text | Legal document folder path |
| Invoicing Folder | Text | Operational calculation folder path |
| Repo | URL or Text | Repo URL or local repo name |
| Billing Frequency | Select | Example: `Monthly`, `Quarterly` |
| Required Inputs | Multi-select | Required recurring inputs |
| Outputs | Multi-select | Reports, invoices, state files |
| Key Rules | Text | Short summary of major calculation rules |
| Exceptions | Text | Project-specific exceptions or edge cases |
| Open Questions | Text | Unknowns to resolve |
| Last Reviewed | Date | Last time the project record was checked |
| Owner | Person | Primary internal owner |

### Suggested Project Page Template

When creating a new project page, use the following sections:

```md
# {Project Name}

## Snapshot
- Facility:
- Service Type:
- Counterparty:
- Status:
- Repo:
- Drive Root:

## Source of Truth
- Legal contract folder:
- Invoicing/calculation folder:
- Main calculation documents:
- Sample inputs:

## Business Rules
- Rule 1:
- Rule 2:
- Rule 3:

## Required Inputs
- Input 1:
- Input 2:
- Input 3:

## Outputs Produced
- Output 1:
- Output 2:

## Code Mapping
- Main repo:
- Main modules:
- Gaps between docs and code:

## Exceptions
- Exception 1:
- Exception 2:

## Open Questions
- Question 1:
- Question 2:
```

## Documents Database

Use this database to register important files, not every throwaway artifact.

### Recommended Properties

| Property | Type | Purpose |
| --- | --- | --- |
| Title | Title | Document title |
| Project | Relation | Link to `Projects` |
| Document Type | Select | Example values listed below |
| Source Level | Select | `Legal`, `Operational`, `Implementation`, `Reference` |
| Path | Text | Full path in `X:\LUMA` or repo path |
| Modified Date | Date | Last modified date |
| Summary | Text | Short description of what the doc covers |
| Key Rules | Text | Important business rules from the doc |
| Linked Code | Text | Modules or functions tied to the doc |
| Related Inputs | Multi-select | Input files or data sources referenced |
| Notes | Text | Free-form notes |

### Suggested Document Type Values

- `contract`
- `amendment`
- `calculation_doc`
- `required_data`
- `performance_guarantee`
- `sample_input`
- `invoice_example`
- `reference_data`
- `presentation`
- `report`

## Implementation Map Database

Use this to trace a business rule from source document to code.

### Recommended Properties

| Property | Type | Purpose |
| --- | --- | --- |
| Rule Name | Title | Name of the rule or formula |
| Project | Relation | Link to `Projects` |
| Source Document | Relation | Link to `Documents` |
| Source Section | Text | Section, slide, or page reference |
| Repo | Text | Repo or implementation location |
| Module / Function | Text | Code entry point |
| Status | Select | `Mapped`, `Partially Mapped`, `Unmapped` |
| Notes | Text | Clarifications or gaps |

## Starter Record for This Repo

Create a project record with these values:

| Property | Value |
| --- | --- |
| Project Name | `Salinas and Jobos` |
| Facility | `Salinas`, `Jobos` |
| Service Type | `PPOA`, `BESS` |
| Status | `Onboarding` |
| Drive Root | `X:\LUMA\Salinas and Jobos Invoicing` |
| Contract Folder | `X:\LUMA\Contracts\jobos_solar` and `X:\LUMA\Contracts\jobos_bess` |
| Invoicing Folder | `X:\LUMA\Salinas and Jobos Invoicing` |
| Repo | `salinas-and-jobos-invoice-calculator` |
| Billing Frequency | `Monthly` |

### Starter Document Records

Add these first:

- `Jobos_Monthly_Payment_Calculation.docx`
- `Jobos_Monthly_Payment_Calculation.pdf`
- `Salinas_Monthly_Payment_Calculation.docx`
- `Salinas_Monthly_Payment_Calculation.pdf`
- `Salinas_Jobos_Required_Data.pptx`
- `Salinas_Jobos_Performance_Guarantee.pptx`
- `BESS_Compensation_Calculation.docx`
- `BESS_Compensation_Calculation.pdf`
- `BESS_Required_Data.pptx`
- `BESS_Performance_Guarantee.pptx`
- all amendment PDFs in `Contracts\jobos_solar`
- all amendment PDFs in `Contracts\jobos_bess`

## Operating Rules

Use these as team conventions:

1. Raw source files stay on the drive.
2. Notion stores summaries, links, decisions, and mappings.
3. Code repos store executable logic and small fixtures only.
4. If a rule matters for billing, it should exist in both a source document and an implementation map entry.
