import streamlit as st

st.set_page_config(
    page_title="Home 🌍",
    page_icon="⚡"
)

st.write("# Home page of EE apps! 👋")

st.sidebar.success("Select an app.")

st.markdown(
    """
    This is the starting point for discovering the tools we use for energy system analysis.
    
    **⬅️ Select one from the sidebar!**
""")

