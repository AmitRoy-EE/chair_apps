import streamlit as st

st.set_page_config(
    page_title="Home 🌍",
    page_icon="⚡"
)

st.write("# Home page of EE apps! 👋")

st.sidebar.success("Select an app.")

st.markdown(
    """
    This is a collection of tools for energy system analysis or a visualisation of results.
    
    **⬅️ Select one from the sidebar!**
    
    If you want to contribute, checkout [the repository](https://gitlab.ruhr-uni-bochum.de/ee/chair_apps).
""")

