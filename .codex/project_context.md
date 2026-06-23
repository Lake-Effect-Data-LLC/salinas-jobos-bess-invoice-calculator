# Salinas/Jobos BESS Invoice Calculator Context

## Current Project

This repo calculates monthly compensation and Appendix P performance guarantee
items for Salinas and Jobos BESS contracts. The core calculator currently uses
five standardized CSV inputs per project and produces monthly results plus an
invoice support report.

Current Streamlit behavior:

- Select Salinas or Jobos.
- Preview the five required input files.
- Upload CSVs to override local defaults for the current run.
- Validate inputs.
- Run calculation.
- Download monthly results and report.

## Product Direction

Move the Streamlit app from a CSV-upload calculator to a database-first project
workspace. Puerto Rico users should maintain data in the app, not in Excel.

CSV/Excel should be import/export/audit tooling, not the steady-state source of
truth.

## Roadmap

### Phase 1: App Foundation

1. Project/config model
   - Define projects like `salinas`, `jobos`.
   - Define configs/datasets like `actual`, `testing`, `scenario_1`.

2. Authentication
   - Start simple: email-based login or restricted allowed-user list.
   - Full password/auth provider can come later.

3. Database schema for editable input tables
   - Store current five input files as real rows, not blobs:
     `contract_values`, `yearly_inputs`, `monthly_inputs`,
     `monthly_performance_guarantee`, `performance_tests`.

4. Extensive input validation
   - Required fields.
   - Data types.
   - Date formats.
   - Month/year consistency.
   - Positive/negative value rules.
   - Duplicate rows.
   - Missing monthly periods.
   - Project-specific contract constraints.
   - Cross-table checks.
   - Warning vs blocking error levels.

### Phase 2: User Workflow

5. Streamlit CRUD/editor screens
   - Users create/edit rows directly in the app.
   - CSV becomes optional.

6. Row-level edit history/audit trail
   - Record old data, new data, user, timestamp, and optional reason/source.

7. Monthly snapshots / versioned datasets
   - Preserve a snapshot of each month before new rows or edits are added.
   - Keep point-in-time history of what the app knew at invoice time.

### Phase 3: Interchange + Traceability

8. Import CSV into DB with validation
   - Bulk seed data, but not the main workflow.

9. Export current DB state
   - Generate the five CSVs plus calculation outputs/report for audit or
     compatibility.

10. Object storage
    - Store uploaded source files, exported calculation packages, generated
      reports, and monthly snapshot packages.
    - Use MinIO locally or Supabase/S3-compatible storage when hosted.

## Design Principle

The app/database is the system of record. CSV is an interchange format.
