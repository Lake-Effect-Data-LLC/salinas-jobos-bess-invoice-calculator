# User Request And Plan

> maybe just size the banner right?

## Plan

Use normal content-width sizing for the banner instead of viewport breakout math.

- Remove the `left: 50%` / `-50vw` banner breakout pattern.
- Set the banner to `width: 100%` inside the full-width Streamlit content container.
- Keep the current banner height, crop, and top spacing.
- Preserve the main content `box-sizing` fix.
- Avoid changing dashboard, input tables, database, or calculation behavior.
- Verify `app/streamlit_app.py` compiles.

---

# Feature Changes

- The banner now sizes to the Streamlit main content area instead of using viewport breakout math.
- Current banner height, crop, and top spacing are preserved.
- The horizontal overflow fix remains local to layout CSS.

---

# Files Changed

- `app/streamlit_app.py`
  - Removed `left: 50%` from `.app-banner`.
  - Changed `.app-banner` width to `100%`.
  - Changed `.app-banner` margin to remove the `-50vw` left breakout.
  - Fixed indentation on the main container `box-sizing` rule.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Updated the banner behavior description from viewport breakout to main-content full-width sizing.

---

# Summary And Concerns

This replaces the fragile viewport-width banner layout with normal content-width sizing. It should eliminate banner-driven horizontal page overflow while preserving the current overall look and responsive main content behavior.

Verification completed:

- `python -m py_compile app/streamlit_app.py`

Concern:

- The banner will now align with the main content gutters rather than breaking all the way to the viewport edge. If the app still shows horizontal scroll, the next likely source is a Streamlit dataframe/editor min-width.
