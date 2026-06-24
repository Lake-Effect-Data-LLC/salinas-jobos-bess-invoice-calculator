# User Request And Plan

> Can we make these scrollable past three previous runs? Does that make sense?

## Plan

Yes. The app already fetches up to 12 previous monthly runs, but the cards expand the page vertically.

- Keep Latest Run fixed in the left dashboard column.
- Wrap the Previous Runs cards in a fixed-height scroll container.
- Keep the existing 12-month history limit, card contents, and download behavior.
- Avoid changing run persistence, database queries, MinIO behavior, or calculations.
- Verify `app/components/run_dashboard.py` compiles.

---

# Feature Changes

- Previous Runs now renders inside a fixed-height scroll container.
- The dashboard still fetches and displays up to 12 prior monthly runs.
- Latest Run remains outside the scroll area and stays visually prominent.

---

# Files Changed

- `app/components/run_dashboard.py`
  - Wrapped the previous-run card loop in `st.container(height=420)`.
  - Left previous-run card content, metrics, and download buttons unchanged.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the scrollable Previous Runs card list.

---

# Summary And Concerns

The prior card list could push the input tables down as more monthly runs accumulated. This keeps the dashboard compact while still making the existing 12-month history accessible by scrolling within the Previous Runs area.

Verification completed:

- `python -m py_compile app/components/run_dashboard.py`
- Confirmed the installed Streamlit `st.container` API supports `height`.

Concern:

- The `420px` height is a visual tuning value. If it feels too short or tall after refresh, adjust it in `app/components/run_dashboard.py`.
