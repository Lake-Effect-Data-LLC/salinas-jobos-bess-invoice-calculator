# Request

And then make the Salinas BESS green?

---

## Plan

1. Review the existing Streamlit runtime documentation for page-title behavior.
2. Replace the project title rendering with a classed heading so only the selected facility title is green.
3. Keep the top ribbon text dark from the prior change.
4. Run a focused syntax check.

---

## Feature Changes

- Changed the selected facility heading, such as `Salinas BESS`, to render in green.
- Kept the top ribbon `Invoice Calculator` using the normal dark theme text color.
- Scoped the green style to the project/facility heading only.

---

## Files Changed

- `app/streamlit_app.py`
  - Added a `.project-heading` CSS class.
  - Replaced `st.title(project_name)` with a classed H1 rendered through `st.markdown`.
- `.codex/docs/changes/2026-06-25-green-project-heading.md`
  - Added the plan and implementation summary for this UI polish request.

---

## Summary And Concerns

The visual emphasis is now swapped as requested: the top ribbon stays dark, while the selected facility title is green. The behavior remains dynamic, so `Jobos BESS` will also render green when that facility is selected.

Verification:
- `python -m py_compile app/streamlit_app.py` passed.

Concern:
- The green is currently the same bright green previously used by the top ribbon (`#00CC00`). If that feels too loud on the larger heading, it can be softened to a darker green.
