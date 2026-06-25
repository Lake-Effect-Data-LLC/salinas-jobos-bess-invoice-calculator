# Request

Would you be able to swap the color of the top ribbon to 'Invoice Calculator' to look like the color of the the 'Salinas BESS'

---

## Plan

1. Review the existing Streamlit runtime feature documentation for relevant UI conventions.
2. Find the top ribbon/header style that renders `Invoice Calculator`.
3. Replace the hard-coded bright green with Streamlit's active text color so it matches the main page title styling.
4. Run a focused syntax check.

---

## Feature Changes

- Updated the top app ribbon title color so `Invoice Calculator` matches the main page heading color instead of using bright green.
- Kept the existing ribbon text, placement, size, and banner behavior unchanged.

---

## Files Changed

- `app/streamlit_app.py`
  - Changed the injected header title CSS from hard-coded `#00CC00` to `var(--text-color)`.
- `.codex/docs/changes/2026-06-25-top-ribbon-title-color.md`
  - Added the plan and implementation summary for this UI polish request.

---

## Summary And Concerns

The top ribbon now follows Streamlit's active text color, so it should visually match the dark `Salinas BESS` page title and stay consistent if the app theme changes.

Verification:
- `python -m py_compile app/streamlit_app.py` passed.

Concern:
- This assumes Streamlit's `--text-color` CSS variable remains available in the app shell, which is the normal Streamlit theme behavior.
