import streamlit as st
# st.write(locals())
import sys
from pathlib import Path

st.write(Path(__file__).parent.as_posix())
sys.path.insert(0,Path(__file__).parent.as_posix())

from submodules.comfort_moo.lit import run

run()