# User Request And Plan

> Can it just be the last one open? If I want to reload the page, I don't want it to switch projects

## Plan

Persist the open facility and scenario selection across browser reloads without adding new storage.

- Use Streamlit URL query params for `project` and `dataset`.
- Read `project` before rendering the Facility radio and use it as the default when valid.
- Read `dataset` before rendering the Scenario selectbox and use it as the default when valid.
- Keep the existing newly-created-dataset override, but have it update the query params too.
- Do not change database schema, calculations, dashboard behavior, or run-history persistence.
- Verify `app/streamlit_app.py` compiles.

---

# Feature Changes

- Facility selection is now synchronized to the `project` URL query parameter.
- Scenario selection is now synchronized to the `dataset` URL query parameter.
- Reloading the same URL keeps the last selected facility/scenario when those values still exist.
- Newly created scenarios still become the selected scenario and now also flow into the URL-backed selection behavior.

---

# Files Changed

- `app/streamlit_app.py`
  - Reads `project` from `st.query_params` when choosing the Facility radio default.
  - Reads `dataset` from `st.query_params` when choosing the Scenario selectbox default.
  - Writes selected facility/scenario back to `st.query_params`.
  - Added small helper functions for query-param reads, writes, and option index lookup.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented URL-backed selection preservation.

---

# Summary And Concerns

The previous behavior defaulted back to the database default scenario, usually `actual`, whenever no one-time session override was present. This change makes the current facility/scenario part of the URL, so browser reloads of the same page keep the same project and dataset instead of snapping back to defaults.

Verification completed:

- `python -m py_compile app/streamlit_app.py`

Concern:

- This preserves selections through the URL. If a user opens a bare URL with no `project` or `dataset` query params, the app still falls back to the default project and default dataset.
