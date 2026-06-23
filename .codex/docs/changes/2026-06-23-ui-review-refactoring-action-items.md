# Original Request And Plan

> "I have a list of technical action items from our recent Streamlit App UI Review and Code Refactoring Session. Please add these to our project's persistent tracking document (e.g., /docs/features.md or /docs/changes.md) so we can work through them systematically.
> Please categorize them by 'UI/UX Improvements', 'Refactoring & Architecture', and 'Documentation/Process'.
> Here are the items:
> - Add input guidelines or descriptions to data column headers or cells for clarity
> - Remove the toggle and dead code from the current implementation
> - Keep 'edit reason' field only for contract values; replace source/editor fields with notes for other input types
> - Add run history display (latest run, previous runs, easy download) at the top of the page
> - Build a dashboard section at the top of the page showing facility/dataset/scenario, most recent run stats, and recent activity
> - Move the project selector to a modal/popup instead of the sidebar
> - Change calculation output to show only the current/most recent month
> - Add CSV export for calculation outputs and save to [min.io](http://min.io/) or equivalent storage
> - Add a separate analytics/graphs page
> - Extract SQLAlchemy insert logic from table editor into its own module (e.g., writers.py)
> - Refactor long function parameter blocks and extract column constants to a separate file
> - Add docstrings and comments throughout the codebase
> - User identity tracking can be handled automatically via database metadata
> - Add a join table of users and projects
> Once you have documented these, please propose a step-by-step plan for how we should tackle the 'Refactoring & Architecture' items first."

---

## Overview

This task is documentation and planning only. The goal is to capture the review/refactoring action items in a persistent project tracker, grouped by category, then propose a practical sequence for addressing the architecture/refactoring work first.

## Plan

1. Review existing `.codex/docs/features/` documentation for related feature context.
2. Create or update a project-facing persistent tracker under `docs/`.
3. Categorize every supplied action item under:
   - UI/UX Improvements
   - Refactoring & Architecture
   - Documentation/Process
4. Mark items that are already partially completed so future work does not duplicate recent refactors.
5. Add a concise step-by-step plan for tackling Refactoring & Architecture first.
6. Update `.codex/docs/features/` with a feature/process note if the tracker introduces a significant project workflow artifact.

---

# Feature Changes

## Persistent Action-Item Tracker

Added a project-facing action-item tracker at `docs/action_items.md`.

The tracker categorizes review items into:

- UI/UX Improvements
- Refactoring & Architecture
- Documentation/Process

It also records status labels so future sessions can tell whether each item is not started, partially complete, or already handled.

## Refactoring-First Plan

Added a step-by-step plan for addressing the Refactoring & Architecture items before larger UI work. The plan prioritizes boundary cleanup, dead-code removal, table/editor constant extraction, parameter simplification, and deferred identity/access decisions.

---

# Files Changed

## `docs/action_items.md`

- Added categorized action items from the Streamlit App UI Review and Code Refactoring session.
- Added a refactoring-first implementation plan.
- Marked already-completed and partially-completed items based on current project state.

## `.codex/docs/features/project-action-tracking.md`

- Documented the new persistent tracking process and where future sessions should update action-item status.

## `.codex/docs/changes/2026-06-23-ui-review-refactoring-action-items.md`

- Recorded the original request, plan, feature summary, file summary, and implementation notes for this documentation-only task.

---

# Overall Summary And Concerns

The requested action items are now captured in a persistent project tracker and grouped by the requested categories. The tracker also includes a practical ordering for tackling Refactoring & Architecture first.

Concerns:

- Some items intentionally remain marked `Partial` because recent refactors have already moved the code in that direction but have not fully closed the underlying concern.
- User/project access modeling remains deferred until real access requirements are known.
- MinIO-backed CSV/export storage remains future-facing; the tracker notes it as a planned artifact-storage feature, not current runtime behavior.
