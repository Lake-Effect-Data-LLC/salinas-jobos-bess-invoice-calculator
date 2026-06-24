# User Request And Plan

> This is looking beautiful, could you make the banner 3/4 thinner and closer to the top? of the page?

## Plan

This is a focused visual spacing update:

- Reduce the banner height to roughly one quarter of its previous height.
- Pull the banner closer to the top of the Streamlit page.
- Keep the viewport-width banner behavior and responsive sidebar behavior intact.
- Avoid changing run history, database, dashboard, or calculation behavior.
- Verify `app/streamlit_app.py` compiles.

---

# Feature Changes

- The top banner is now approximately one quarter of its previous height.
- The banner is pulled closer to the top of the page while preserving its full-width responsive behavior.

---

# Files Changed

- `app/streamlit_app.py`
  - Changed `.app-banner` height from `11rem` to `2.75rem`.
  - Changed `.app-banner` top margin from `-1.25rem` to `-3rem`.

---

# Summary And Concerns

This is a visual-only spacing adjustment. It keeps the full-width banner and sidebar responsive behavior intact, but makes the image band much thinner and moves it closer to the top of the page.

Verification completed:

- `python -m py_compile app/streamlit_app.py`

Concern:

- The exact top spacing is Streamlit-theme dependent, so the running page should be visually checked after refresh.
