import streamlit as st

def switch_page(page_name: str):
    """
    Simple wrapper around Streamlit's built-in st.switch_page.

    Usage in your app:
        switch_page("Resume Screen")
    expects the target file to be: pages/Resume_Screen.py
    """
    # Map human-readable names to actual script paths
    mapping = {
        "Resume Screen": "pages/Resume Screen.py",
    }

    if page_name not in mapping:
        raise ValueError(f"Unknown page: {page_name}. Known pages: {list(mapping.keys())}")

    st.switch_page(mapping[page_name])