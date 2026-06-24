# User Request And Plan

> Okay, can we be more strategic about what part of the banner is showing though? I can't see any of the bottom half where there's hills and stuff

## Plan

This is a focused banner-crop adjustment:

- Keep the current banner height and full-width responsive behavior.
- Shift the image crop downward so the hills/lower landscape are visible.
- Avoid changing dashboard, sidebar, database, or calculation behavior.
- Verify `app/streamlit_app.py` compiles.

---

# Feature Changes

- The banner image crop now prioritizes the lower landscape area so the hills are more visible.
- Banner height and responsive full-width behavior are unchanged.

---

# Files Changed

- `app/streamlit_app.py`
  - Changed `.app-banner img` `object-position` from `center 44%` to `center 68%`.

---

# Summary And Concerns

The prior crop favored the upper part of the image, which made the banner show mostly sky/clouds and cut off the hills. This shifts the image focal point downward while keeping the same banner size and layout.

Verification completed:

- `python -m py_compile app/streamlit_app.py`

Concern:

- Exact crop quality depends on viewport width, so this may need one more visual adjustment after checking the running app.
