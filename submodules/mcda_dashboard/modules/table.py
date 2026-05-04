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


def table(
    selected_radio, selected_models, selected_categories, df, final_energy_demand=None
):
    """[for all the models that are selected, a table with all the corresponding categories is created]

    Args:
        selected_radio ([value]): [description]
        selected_models ([value]): [description]

    Returns:
        [table]: [description]
    """

    df_table = df.reset_index()

    if type(selected_models) == str:
        selected_models = [selected_models]

    if type(selected_categories) == str:
        selected_categories = [selected_categories]

    # df_table is numbered by model-names
    if selected_radio == "Heizung":
        df_table = df_table.set_index("Anlagentyp")

    if selected_radio == "Fahrzeug":
        df_table = df_table.set_index("Modell")

    df_table = df_table.transpose()  # transpose table
    df_table["Minimum*"] = df_table.min(axis=1)
    df_table["Maximum*"] = df_table.max(axis=1)
    df_table.index = df_table.index.set_names(
        "Kategorie"
    )  # change name of Index[0] to 'Kategorie' instead of 'index'

    df_table = df_table.loc[
        selected_categories, selected_models + ["Minimum*", "Maximum*"]
    ].reset_index()

    return df_table
