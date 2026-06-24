# User Request And Plan

> Let's make the Previous Runs area only display two and a half run rectangles. Like make a new one that's 3/4 the size

## Plan

Tune the Previous Runs scroll window height only.

- Keep fetching up to 12 previous runs.
- Keep the cards and download behavior unchanged.
- Reduce the visible scroll container height from `420px` to `315px`, which is 75% of the current height.
- Verify `app/components/run_dashboard.py` compiles.

---

# Feature Changes

- The Previous Runs scroll window is now shorter, showing roughly two full cards plus part of another card.
- The list remains scrollable and still supports up to 12 previous monthly runs.

---

# Files Changed

- `app/components/run_dashboard.py`
  - Changed the Previous Runs scroll container height from `420` to `315`.

---

# Summary And Concerns

This is a visual-only dashboard tuning change. It preserves run-history data, card contents, download buttons, and the previous-run limit while reducing the amount of vertical page space used by the Previous Runs panel.

Verification completed:

- `python -m py_compile app/components/run_dashboard.py`

Concern:

- The exact number of visible card rectangles depends on viewport width and Streamlit spacing. If it shows too much or too little after refresh, adjust the height value in `app/components/run_dashboard.py`.
