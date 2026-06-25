# Fix link_button key argument

---

## Original Request

> TypeError: ButtonMixin.link_button() got an unexpected keyword argument 'key'

---

## Plan

`st.link_button` in Streamlit 1.52.1 does not accept a `key` parameter. Remove it from the call in `_render_downloads`. Unlike `st.download_button`, `st.link_button` renders as an anchor tag and does not need a key for widget deduplication.

---

## Changes

### `app/components/run_dashboard.py`
- Removed `key=f"{key_prefix}-csv-download"` from `st.link_button` call

---

## Summary

One-line bug introduced in the MinIO integration PR. `st.link_button` has a different signature than `st.download_button` and does not support `key`.
