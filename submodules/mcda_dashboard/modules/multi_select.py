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


# dropdown and select all button for categories and models
def create_multiselect(container, checkbox, options, key, preselect:slice=None):
    with container:
        select_all = st.checkbox(checkbox, key=key)
        if select_all:
            # use checkbox.replace("Select all","") to get the correct name out of string
            selected = container.multiselect(checkbox.split()[1], options, options)
        else:
            if preselect:
                default_options = options[preselect]
            selected = st.multiselect(
                checkbox.split()[1], options, default=default_options
            )
    return selected
