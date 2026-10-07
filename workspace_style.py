from __future__ import annotations

from pathlib import Path

import streamlit as st


def inject_workspace_style() -> None:
    """Load the single shared stylesheet for the redesigned workspace."""
    css = Path(__file__).with_name("workspace.css").read_text(encoding="utf-8")
    st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)
