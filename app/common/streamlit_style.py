"""Utilities to apply a consistent and accessible style across the app."""
from __future__ import annotations

import streamlit as st


def hide_streamlit_style() -> None:
    """Inject custom CSS focused on accessibility enhancements.

    The styles below improve colour contrast, ensure focus states are visible for
    keyboard users and provide clearer affordances for interactive components.
    """

    hide_st_style = """
        <style>
            .reportview-container {
                margin-top: 0;
            }
            #MainMenu {visibility: hidden;}
            .stDeployButton {display:none;}
            footer {visibility: hidden;}
            #stDecoration {display:none;}

            :root {
                color-scheme: light;
            }

            body,
            [data-testid="stAppViewContainer"] {
                background-color: #f5f7fa;
                color: #1b1b1d;
            }

            a {
                color: #0b5fff;
                text-decoration-thickness: 0.15em;
            }

            a:focus-visible,
            button:focus-visible,
            [role="button"]:focus-visible,
            textarea:focus-visible,
            input:focus-visible,
            select:focus-visible {
                outline: 3px solid #ffbf47 !important;
                outline-offset: 2px !important;
                box-shadow: none !important;
            }

            [data-testid="stSidebar"] {
                background-color: #0b1f33;
                color: #ffffff;
            }

            [data-testid="stSidebar"] * {
                color: #ffffff !important;
            }

            [data-testid="stSidebar"] a {
                color: #9ec9ff !important;
            }

            button,
            [role="button"],
            textarea,
            input,
            select {
                border-radius: 0.5rem !important;
                border: 2px solid #1f3a5f !important;
                background-color: #ffffff;
                color: #1b1b1d;
            }

            .stButton button {
                background-color: #0b5fff;
                border-color: #0842a0 !important;
                color: #ffffff !important;
                font-weight: 600;
            }

            .stButton button:hover,
            .stButton button:focus-visible {
                background-color: #0842a0 !important;
                color: #ffffff !important;
            }

            input[type="checkbox"] {
                width: 1.15rem;
                height: 1.15rem;
                accent-color: #0b5fff;
            }

            input[type="checkbox"]:focus-visible {
                outline: 3px solid #ffbf47 !important;
                outline-offset: 2px !important;
            }

            [data-testid="stFileUploader"] section [data-testid="stFileUploaderDropzone"] {
                border: 2px dashed #1f3a5f;
                border-radius: 0.75rem;
                background-color: #ffffff;
            }

            [data-testid="stFileUploader"] section [data-testid="stFileUploaderDropzone"]:focus-within {
                border-color: #ffbf47;
                box-shadow: 0 0 0 3px rgba(255, 191, 71, 0.4);
            }

            [data-testid="stChatMessage"] {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 0.75rem;
                padding: 1rem;
            }

            [data-testid="stChatMessage"] p,
            [data-testid="stChatMessage"] li {
                color: #1b1b1d;
            }

            [data-testid="stChatMessage"] strong {
                color: #0b1f33;
            }

            [data-testid="stChatInput"] textarea {
                border-radius: 0.75rem !important;
                min-height: 100px;
                background-color: #ffffff;
            }

            [data-testid="stChatInput"] textarea::placeholder {
                color: #475569;
            }

            [data-testid="stDataFrame"] table {
                border: 1px solid #1f3a5f;
            }

            [data-testid="stDataFrame"] thead tr {
                background-color: #0b1f33;
                color: #ffffff;
            }
        </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)
