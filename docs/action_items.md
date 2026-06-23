# Streamlit App UI Review And Refactoring Action Items

This tracker captures follow-up work from the Streamlit App UI Review and Code Refactoring session.

Status labels:

- `Todo`: not started.
- `Partial`: some groundwork exists, but the item is not complete.
- `Done`: implemented enough to close unless new requirements appear.

---

## UI/UX Improvements

| Status | Item | Notes |
| --- | --- | --- |
| Todo | Add input guidelines or descriptions to data column headers or cells for clarity | Useful for contract/data-entry fields where abbreviations are not obvious. |
| Done | Keep `edit reason` field only for contract values; replace source/editor fields with notes for other input types | Non-contract input editors no longer show form-level edit reason/source fields. Operators should use row-level notes for context. Contract values remain read-only for now; when made editable, they should be the only table using required edit provenance fields. |
| Todo | Add run history display at the top of the page | Should show latest run, previous runs, and easy report/download access. |
| Todo | Build a dashboard section at the top of the page | Should show facility, dataset/scenario, most recent run stats, and recent activity. |
| Done | Make the project/dataset sidebar less large | Keep selector controls in the sidebar for now, but use a slimmer panel so the input tables have more room. Revisit modal/popup only if sidebar selection still gets in the way. |
| Todo | Change calculation output to show only the current/most recent month | Current output is broader than the main invoice-review workflow needs. |
| Todo | Add CSV export for calculation outputs and save to MinIO or equivalent storage | MinIO remains future artifact storage, not source-of-truth data storage. |
| Todo | Add a separate analytics/graphs page | Keep operational invoice workflow separate from exploratory reporting. |

---

## Refactoring & Architecture

| Status | Item | Notes |
| --- | --- | --- |
| Done | Extract SQLAlchemy insert logic from table editor into its own module | Implemented as `app/db/writers.py`. |
| Done | Remove the toggle and dead code from the current implementation | Removed the Streamlit CSV/database runtime toggle and deleted the unused CSV input component. CSV remains available through import/verification tooling. |
| Partial | Refactor long function parameter blocks and extract column constants to a separate file | Table editor still has long wrappers and local column constants. Good candidate for `app/services/table_specs.py` or `app/components/table_configs.py`. |
| Todo | User identity tracking can be handled automatically via database metadata | Current conservative model keeps `app_user` and nullable attribution hooks. Need to decide whether database/session metadata should populate `created_by` / `edited_by`. |
| Todo | Add a join table of users and projects | Deferred until project-specific access is confirmed. If needed, likely `project_user(project_id, user_id, role, created_at)`. |

---

## Documentation/Process

| Status | Item | Notes |
| --- | --- | --- |
| Partial | Add docstrings and comments throughout the codebase | Do this selectively for complex utilities and service boundaries. Avoid noisy comments on obvious code. |
| Done | Maintain persistent change and feature docs for significant work | Current workflow uses `.codex/docs/changes/` and `.codex/docs/features/`. |

---

## Refactoring & Architecture Plan

1. **Confirm current boundaries**
   - Treat `app/components/` as Streamlit UI.
   - Treat `app/services/` as workflow/application logic.
   - Treat `app/db/` as persistence and SQL access.

2. **Remove dead compatibility paths**
   - Completed: removed the Streamlit CSV/database runtime toggle.
   - Completed: removed unused CSV runtime helper functions and the unused CSV input component.
   - Kept: CSV import/roundtrip tooling remains outside the runtime app.

3. **Extract table/editor constants**
   - Move table column lists and numeric-column lists out of `app/services/table_editor.py`.
   - Prefer a small table-spec module over a deep class hierarchy.
   - Keep table-specific normalization functions readable and separate.

4. **Shorten long function parameter blocks**
   - Introduce small specs or context objects only where they reduce repeated call signatures.
   - Avoid hiding important values like `project_id`, `dataset_name`, and `engine` too early.

5. **Clarify identity metadata**
   - Keep `app_user` as identity/attribution only for now.
   - Decide later whether edit attribution comes from app login, database session metadata, or deployment-level auth.

6. **Defer project-user membership until access requirements are real**
   - Do not add `project_user` until users actually need project-scoped permissions.
   - If added, keep it minimal: project, user, role, created timestamp.

7. **Add focused tests around each refactor**
   - Table specs should preserve normalization behavior.
   - Dead-code removal should not break database flow or CSV import/roundtrip tooling.
   - Identity metadata changes should preserve nullable attribution behavior.
