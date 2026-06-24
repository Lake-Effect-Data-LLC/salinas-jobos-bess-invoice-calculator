# User Request And Plan

> Great, now let's just make Latest run take up a little more space horizontally on the screen.

## Plan

Make a small dashboard layout adjustment.

- Increase the horizontal share of the Latest Run column.
- Keep Previous Runs scrollable.
- Keep all metrics, downloads, database reads, and persistence behavior unchanged.
- Verify `app/components/run_dashboard.py` compiles.

---

# Feature Changes

- The Latest Run dashboard column now receives slightly more horizontal space.
- Previous Runs remains visible and scrollable with the same content and behavior.

---

# Files Changed

- `app/components/run_dashboard.py`
  - Changed the top-level dashboard column ratio from `[2, 3]` to `[2.4, 3]`.

---

# Summary And Concerns

This is a visual-only layout tuning change. It gives Latest Run more room for its large metrics while preserving the existing Previous Runs scroll list, downloads, and run-history data behavior.

Verification completed:

- `python -m py_compile app/components/run_dashboard.py`

Concern:

- The ratio is a tuning value. If Previous Runs feels too narrow or Latest Run still feels cramped after refresh, adjust the ratio in `render_run_history_dashboard`.
