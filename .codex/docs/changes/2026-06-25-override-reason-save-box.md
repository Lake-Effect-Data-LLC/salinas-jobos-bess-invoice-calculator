# Request

"We want to make the 'Override edit reason' visually distinct so users understand it's a critical action, but we must stick to native Streamlit components and avoid custom CSS hacks.
Please update the UI directly above the Save button to include the following when Override Mode is ON:
1. Use st.container(border=True) to group the edit reason and the Save button together in a visually distinct box.
2. Inside that container, place an st.warning(' Please provide a detailed reason for modifying historical reference data.') right above the st.text_area. This will provide a tasteful splash of yellow/orange caution color.
3. Place the st.text_area immediately below the warning, followed by the Save button.
Please update the code to reflect this grouped, native warning layout."

---

## Plan

1. Keep the `Override Mode` toggle in the sidebar.
2. Keep the main-view override warning and override editor identity field.
3. Move the override edit reason into a native `st.container(border=True)` next to each table's save action.
4. Use `st.warning(...)`, then `st.text_area(...)`, then the Save button inside that container when Override Mode is active.
5. Preserve normal-mode save buttons without the extra critical-action box.
6. Run focused compile/tests.

---

## Feature Changes

- In Override Mode, table save actions now appear inside a native `st.container(border=True)`.
- The override edit reason is now a `st.text_area` placed directly above the Save button.
- A native `st.warning(...)` appears inside the bordered container to make the action visually distinct without custom CSS.

---

## Files Changed

- `app/components/db_tables.py`
  - Added `_render_save_controls(...)` to centralize normal vs override save UI.
  - Moved the override edit reason from the shared top area into each table's save action area.
  - Kept the override editor identity field in the main view above the tabs.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the bordered override save-action layout.

---

## Summary And Concerns

Override saves now use a native Streamlit warning box and text area directly above the Save button. Normal-mode save buttons stay lightweight.

Verification:

- `.\.venv\Scripts\python.exe -m py_compile app\components\db_tables.py`
- `.\.venv\Scripts\python.exe -m unittest tests.test_table_editor_normalization`

No backend behavior changed.
