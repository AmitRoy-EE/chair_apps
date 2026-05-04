"""
    MCDA-tool - supports making decisions for energy-intensive technologies 
    Copyright (C) 2020-2023 David Huckebrink, Katharina Esser, Behnaz Goshayeshi

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import streamlit as st


def aligned_st_component(st_component, value, alignment, no_columns=3):
    col1, col2, col3 = st.columns(no_columns)
    with col1:
        if alignment == "left":
            st_component(value)
        else:
            st.write(" ")
    with col2:
        if alignment == "center":
            st_component(value)
        else:
            st.write(" ")
    with col3:
        if alignment == "right":
            st_component(value)
        else:
            st.write(" ")
    with col2:
        st.write(" ")
    return col1, col2, col3
