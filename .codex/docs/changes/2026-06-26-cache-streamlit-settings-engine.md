# Request

There are some design points that should be fixed up before this project gets passed off. - [ ]  **2. Cache the database engine**
    - [ ]  In `app/streamlit_app.py`, `render_database_flow` calls `load_settings()` and `get_engine(settings.database.url)` on every Streamlit rerun, creating a new connection pool on every widget interaction. Wrap engine creation in a `@st.cache_resource` function so the engine is created once per process. Also consider caching `load_settings()` since it does file I/O on every render. Make sure `check_connection` still runs each render so connection errors surface promptly.

---

## Plan

1. Add cached helper functions in `app/streamlit_app.py` for settings loading and database engine creation.
2. Keep `check_connection(engine)` inside `render_database_flow` so it still runs on every Streamlit render.
3. Use the cached settings object everywhere the current render flow already uses settings.
4. Run focused compile/tests and update runtime docs.

---

## Feature Changes

- Streamlit now caches settings loading with `@st.cache_resource`.
- Streamlit now caches SQLAlchemy engine creation with `@st.cache_resource`, keyed by database URL.
- `check_connection(engine)` still runs inside `render_database_flow` on every render so broken database connectivity is surfaced immediately.

---

## Files Changed

- `app/streamlit_app.py`
  - Added `get_cached_settings()`.
  - Added `get_cached_engine(database_url)`.
  - Updated `render_database_flow()` to use the cached helpers before running `check_connection(engine)`.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented cached settings/engine behavior and per-render connection checking.
- `.codex/docs/changes/2026-06-26-cache-streamlit-settings-engine.md`
  - Added this implementation record.

---

## Summary And Concerns

The app no longer creates a new SQLAlchemy engine and connection pool on every Streamlit widget interaction. Settings and engine construction are cached once per process by Streamlit, while the live database check remains per-render.

Verification:
- `python -m py_compile app/streamlit_app.py` passed.
- `python -m unittest discover -s tests` passed: 71 tests.

Concern:
- Because settings are now cached per process, changing `.env.docker`, environment variables, or Streamlit secrets during a running app session requires a Streamlit process restart or cache clear to take effect. That is usually the right tradeoff for stable engine pooling.
