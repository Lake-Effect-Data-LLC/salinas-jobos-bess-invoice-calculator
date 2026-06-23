import base64
from pathlib import Path

import streamlit as st


def render_banner(image_path):
    image_path = Path(image_path)
    if not image_path.exists():
        return

    encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii")
    st.markdown(
        f"""
        <div class="app-banner">
            <img src="data:image/png;base64,{encoded_image}" alt="Puerto Rico landscape and flag">
        </div>
        """,
        unsafe_allow_html=True,
    )
