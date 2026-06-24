# User Request And Plan

> yeah!, try that!

Context: Make the banner and main page respond naturally when the Streamlit sidebar is collapsed.

## Plan

This is a focused CSS layout change:

- Break the banner out of Streamlit's centered content container.
- Remove Streamlit's max-width cap from the main block container.
- Keep the compact sidebar width rules.
- Make the banner span the full viewport width.
- Avoid depending on Streamlit's internal collapsed-sidebar DOM state.
- Avoid changing dashboard, persistence, MinIO, or run-history behavior.

## Verification Plan

- Run Python compilation for `app/streamlit_app.py`.
- Check the local Streamlit endpoint is responding.

---

# Feature Changes

- The banner now breaks out of Streamlit's centered content container and spans the full viewport width.
- The banner no longer depends on detecting whether the sidebar is open or collapsed.
- The main content block now uses the available page width instead of Streamlit's centered max-width layout.

---

# Files Changed

- `app/streamlit_app.py`
  - Sets `[data-testid="stMainBlockContainer"]` to full width with stable side padding.
  - Uses `width: 100vw` and `margin-left: -50vw` for a full-viewport banner breakout.
  - Removed the attempted collapsed-sidebar selector.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the responsive main-content banner behavior.

---

# Summary And Concerns

The first `width: 100%` attempt only filled Streamlit's content container, so it did not visibly expand the banner. The second attempt depended on a Streamlit collapsed-sidebar selector that did not match the rendered app. This update uses a simple full-viewport banner breakout rule and removes the main content container's max-width cap so the rest of the page can expand too.

Verification completed:

- `python -m py_compile app/streamlit_app.py`
- `Invoke-WebRequest http://localhost:8503` returned HTTP 200.

Concern:

- Visual browser verification was not available through the in-app browser in this session, so final spacing should be checked in the running Streamlit page.
