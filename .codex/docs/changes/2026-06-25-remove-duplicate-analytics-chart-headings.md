# User Request And Plan

> Bit of a display bug here...

## Plan

Fix the duplicate headings in the bottom analytics charts.

- Keep the visible Streamlit section headings: `Financial Trend` and `Generation Trend`.
- Remove the duplicate Altair chart titles for those two trend charts.
- Keep axis labels, legends, tooltips, and chart data unchanged.
- Do not change database, calculation, run-history, or snapshot behavior.
- Verify `app/components/analytics.py` compiles and analytics tests pass.

---

# Feature Changes

- Bottom analytics charts no longer display duplicate headings.
- `Financial Trend` and `Generation Trend` remain as the visible section labels.
- Axis labels, legends, tooltips, and chart data are unchanged.

---

# Files Changed

- `app/components/analytics.py`
  - Removed the `title` argument from bottom trend chart calls.
  - Updated `_trend_line_chart(...)` so it does not set an Altair chart title.

---

# Summary And Concerns

The duplicate labels came from rendering both a Streamlit markdown heading and an Altair chart title with the same text. This keeps the Streamlit heading and removes only the chart-level duplicate title.

Verification completed:

- `python -m py_compile app/components/analytics.py`
- `python -m unittest tests.test_analytics`

Concern:

- No browser screenshot verification was performed; visually confirm after refresh.
