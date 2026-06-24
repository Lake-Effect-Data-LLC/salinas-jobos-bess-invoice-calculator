# User Request And Plan

> whoops, when I said 3/4 thinner, I guess I meant 3/4 of the size lol :o

## Plan

This corrects the previous banner-height interpretation:

- Set the banner to 75% of the original `11rem` height, which is `8.25rem`.
- Keep the closer-to-top placement.
- Avoid changing dashboard, sidebar, database, or calculation behavior.
- Verify `app/streamlit_app.py` compiles.

---

# Feature Changes

- The banner is now 75% of its original height instead of one quarter of its original height.
- The closer-to-top placement from the prior banner adjustment remains in place.

---

# Files Changed

- `app/streamlit_app.py`
  - Changed `.app-banner` height from `2.75rem` to `8.25rem`.

---

# Summary And Concerns

This corrects the banner sizing interpretation while leaving the rest of the layout behavior unchanged. The original banner was `11rem`; the new banner height is `8.25rem`.

Verification completed:

- `python -m py_compile app/streamlit_app.py`

Concern:

- No browser screenshot verification was performed in this session, so the final spacing should be visually checked in Streamlit.
