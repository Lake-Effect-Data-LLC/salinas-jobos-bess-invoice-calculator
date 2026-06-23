# Project Action Tracking

## Overview

The project now keeps a persistent action-item tracker for review findings and planning items that should survive across LLM sessions.

Primary tracker:

- `docs/action_items.md`

## Feature Behavior

The tracker groups action items into:

- UI/UX Improvements
- Refactoring & Architecture
- Documentation/Process

Each item has a simple status:

- `Todo`
- `Partial`
- `Done`

The tracker also includes a step-by-step plan for working through Refactoring & Architecture items first.

## Technical Details

This is a documentation/process feature, not runtime app behavior.

When future sessions add or complete work from the tracker:

1. Update `docs/action_items.md`.
2. Add a change note in `.codex/docs/changes/`.
3. Update relevant `.codex/docs/features/` files when feature behavior changes.
