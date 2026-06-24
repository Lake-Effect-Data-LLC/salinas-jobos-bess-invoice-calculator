# User Request And Plan

> That was wayt too big of a difference... We also need to make the CSV and Re[prt buttons smaller because they fwere getting contorted

## Plan

Tune the dashboard back toward balance while preventing cramped Previous Runs buttons.

- Reduce the Latest Run width increase from the prior change.
- Keep Latest Run slightly wider than before, but not dominant.
- Use shorter labels for Previous Runs download buttons so they fit in the smaller card area.
- Keep Latest Run download labels unchanged.
- Preserve run-history data, downloads, scroll behavior, and persistence.
- Verify `app/components/run_dashboard.py` compiles.

---

# Feature Changes

- The Run History split is now more balanced than the prior oversized Latest Run layout.
- Previous Runs report download buttons use the shorter `TXT` label to avoid wrapping/contortion.
- Latest Run keeps the full `Report` label.

---

# Files Changed

- `app/components/run_dashboard.py`
  - Changed the top-level dashboard column ratio from `[3.4, 2]` to `[3, 2.4]`.
  - Added optional labels to `_render_downloads(...)`.
  - Passed `report_label="TXT"` for Previous Runs only.

---

# Summary And Concerns

This is a visual-only dashboard tuning change. It backs off the large Latest Run width shift while keeping more room than the original layout, and it prevents Previous Runs download buttons from wrapping in narrower cards.

Verification completed:

- `python -m py_compile app/components/run_dashboard.py`

Concern:

- If the previous-run button area is still cramped on small screens, use vertical stacked buttons or icon-only labels next.
