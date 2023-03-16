import streamlit as st

st.set_page_config(
    page_title="Home 🌍",
    page_icon="⚡"
)

st.write("# Home page of EE apps! 👋")

st.sidebar.success("Select an app.")

st.markdown(
    """
    This is a collection of tools we use for energy system analysis or to visualise their results.
    
    **⬅️ Select one from the sidebar!**
""")

