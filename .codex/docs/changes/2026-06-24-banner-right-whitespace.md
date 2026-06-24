# User Request And Plan

> Thanks CODEX, can you add just the thinnest bit of whitespace on the banner to match the look of the other side?

## Plan

Make a small visual-only banner spacing adjustment.

- Keep the current banner height, crop, and top placement.
- Add a thin right-side inset so the banner does not run flush to the browser edge.
- Avoid changing dashboard, sidebar, database, or calculation behavior.
- Verify `app/streamlit_app.py` compiles.

---

# Feature Changes

- The banner now leaves a very small right-side whitespace inset instead of running flush to the browser edge.
- Existing banner height, crop, and top placement are unchanged.

---

# Files Changed

- `app/streamlit_app.py`
  - Changed `.app-banner` width from `100vw` to `calc(100vw - 0.5rem)`.

---

# Summary And Concerns

This is a visual-only polish pass to make the banner edge feel balanced against the surrounding page spacing. It does not change sidebar behavior, dashboard layout, database access, or calculations.

Verification completed:

- `python -m py_compile app/streamlit_app.py`

Concern:

- The exact perceived whitespace depends on viewport width and Streamlit chrome, so this may need a small adjustment after visual refresh.
