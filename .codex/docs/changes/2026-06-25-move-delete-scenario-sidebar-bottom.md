# Request

Would you be able to move that button down to the bottom of the left panel and make it red?

---

## Plan

1. Move the `Delete Scenario` button lower in the sidebar flow, after the Scenario selector and Override Mode toggle.
2. Use Streamlit's native `type="primary"` button styling so it appears red under the current app theme.
3. Keep the existing confirmation dialog and database deletion behavior unchanged.
4. Run focused compile checks.

---

## Feature Changes

- Moved the destructive scenario deletion action lower in the sidebar control flow, below the normal Facility/Scenario selection and Override Mode controls.
- Changed the delete action to Streamlit's native primary button style so it appears red under the app theme.
- Kept the existing confirmation dialog and scenario deletion behavior unchanged.

---

## Files Changed

- `app/streamlit_app.py`
  - Moved `Delete Current Scenario` below the sidebar Override Mode toggle.
  - Added a sidebar divider before the destructive action.
  - Set the button to `type="primary"` for native red/destructive styling.
- `.codex/docs/changes/2026-06-25-move-delete-scenario-sidebar-bottom.md`
  - Added the plan and implementation summary for this UI polish request.

---

## Summary And Concerns

The scenario delete button is now visually separated from the main selection controls and styled as a red primary action. This addresses the request without changing the database deletion flow, confirmation dialog, or scenario selection behavior.

Verification:
- `python -m py_compile app/streamlit_app.py` passed.

Concern:
- This places the button at the bottom of the current sidebar content stack. A true viewport-pinned bottom button would require custom CSS or layout hacks, which this change avoids.
