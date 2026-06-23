# User Request And Plan

> I don't want you to do this yest {> - Move the project selector to a modal/popup instead of the sidebar } Instead just make that side panel much less large, ya kjnow whawt I mean?

## Plan

The current Streamlit app intentionally widens the sidebar to `25rem`, which makes the project/dataset panel take up more horizontal space than the workflow needs. The user does not want the selector moved to a modal yet; the better immediate move is to keep the existing sidebar interaction and make the sidebar narrower.

This change will:

- Keep facility and dataset/scenario selection in the sidebar.
- Reduce the custom sidebar width.
- Adjust the banner width/margin math to match the slimmer sidebar.
- Update the persistent action tracker so the modal item becomes a slimmer-sidebar item instead.
- Update feature documentation to note the compact sidebar selector behavior.

## Verification Plan

- Run Python compilation for `app/streamlit_app.py`.

---

# Feature Changes

- Facility and dataset/scenario selection stays in the Streamlit sidebar.
- The custom sidebar width was reduced from `25rem` to `16rem`, giving the main input-table workspace more horizontal room.
- The app banner layout math now uses sidebar width variables so it stays aligned with the slimmer sidebar.
- The action tracker no longer points to moving the project selector to a modal/popup as the immediate UI task.

---

# Files Changed

- `app/streamlit_app.py`
  - Added CSS variables for sidebar width.
  - Reduced the fixed sidebar width.
  - Updated banner width and margin calculations to match the new sidebar width.

- `docs/action_items.md`
  - Replaced the modal/popup action item with a completed slimmer-sidebar item.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented that facility and dataset/scenario selection uses a compact sidebar.

---

# Summary And Concerns

This change keeps the current sidebar-based selector flow and makes the side panel materially less large. It answers the immediate UX concern without committing the app to a modal/popup pattern before the workflow needs it.

Verification completed:

- `python -m py_compile app/streamlit_app.py`
- `Invoke-WebRequest http://localhost:8501` returned HTTP 200.

Concern:

- Visual browser verification was attempted, but the in-app browser connector failed before opening the app because its sandbox metadata was malformed in this session. The fixed width is now much smaller, but the exact feel may still need tuning after looking at the running Streamlit app.
