# User Request And Plan

> not bad! It would be slightly better if the banner was closer to the edges

## Plan

Make the banner slightly wider without returning to viewport breakout sizing.

- Keep the banner inside the main content layout.
- Let the banner bleed into part of the main content padding using small negative side margins.
- Preserve current banner height, crop, and top spacing.
- Avoid changing dashboard, input tables, database behavior, or calculations.
- Verify `app/streamlit_app.py` compiles.

---

# Feature Changes

- The banner now sits closer to the page edges while staying tied to the main content layout.
- Current banner height, crop, and top spacing are unchanged.

---

# Files Changed

- `app/streamlit_app.py`
  - Changed `.app-banner` width from `100%` to `calc(100% + 2rem)`.
  - Changed `.app-banner` margin to bleed `1rem` into the main content padding on both sides.

---

# Summary And Concerns

This is a visual-only banner spacing adjustment. It avoids the earlier viewport-width breakout pattern that could create horizontal page scroll, while making the banner feel less inset.

Verification completed:

- `python -m py_compile app/streamlit_app.py`

Concern:

- If a horizontal scrollbar returns on refresh, reduce the side bleed from `1rem` to `0.5rem`.
