"""Utilities to apply a consistent and accessible style across the app."""
from __future__ import annotations

import streamlit as st


def hide_streamlit_style() -> None:
    """Simple CSS to hide Streamlit elements."""

    hide_st_style = """
        <style>
            #MainMenu {visibility: hidden;}
            .stDeployButton {display:none;}
            footer {visibility: hidden;}
            #stDecoration {display:none;}
        </style>
    """
    st.markdown(f"<style>{hide_st_style}</style>")
