# User Request And Plan

> We can make those buttons fit there, also, juast a little bigger for the Latest Run

## Plan

Tune run-dashboard spacing only.

- Give Latest Run slightly more horizontal space.
- Widen the left area inside Previous Run cards so CSV/Report buttons fit without wrapping.
- Keep the scrollable Previous Runs container, metrics, downloads, queries, and persistence unchanged.
- Verify `app/components/run_dashboard.py` compiles.

---

# Feature Changes

- Latest Run now receives slightly more horizontal space in the dashboard.
- Previous Run cards now allocate more room to the month/download area so `Report` should not wrap.

---

# Files Changed

- `app/components/run_dashboard.py`
  - Changed the top-level dashboard column ratio from `[2.4, 3]` to `[2.6, 3]`.
  - Changed each previous-run card column ratio from `[1.25, 5]` to `[1.6, 5]`.

---

# Summary And Concerns

This is a visual-only spacing adjustment. It keeps the scrollable Previous Runs list, metrics, download buttons, run-history query behavior, and persistence unchanged.

Verification completed:

- `python -m py_compile app/components/run_dashboard.py`

Concern:

- The exact button wrapping depends on viewport width. If `Report` still wraps on narrower screens, the next move is to render CSV/Report vertically or use shorter icon-style labels.
