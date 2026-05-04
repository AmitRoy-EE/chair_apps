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
import sqlite3

import pandas as pd

from modules.table import table
from modules.load_data import select_df

db_conn = sqlite3.connect("database.db")

df1 = pd.read_sql("SELECT * FROM Heating", db_conn)
df2 = pd.read_sql("SELECT * FROM Cars", db_conn)

all_options = {
    "Fahrzeug": df2["Modell"].tolist(),
    "Heizung": df1["Anlagentyp"].tolist(),
}

category = {
    "Fahrzeug": df2.columns[2:].tolist(),
    "Heizung": df1.columns[2:].tolist(),
}


"""
    test table callback function
    function: table(selected_radio, selected_model, selected_category, final_energy_demand=None)
"""


def test_table_model_category(
    product_type="Heizung",
    model="Gas-Heizung EcoTEC ",
    category="Nennwärmeleistung [kW]",
):
    # test one defined model
    df = select_df(product_type, final_energy_demand=None)
    d_table = table(product_type, model, category, df, 0)
    assert model in d_table.columns.values
    assert category in d_table.iloc[:, 0].values


def test_table_heating_model_loop():
    # test all models from heating
    for model_name in all_options["Heizung"]:
        test_table_model_category(model=model_name)


def test_table_model_category_loop():
    # test all models and categories in all products
    for product_name in all_options.keys():
        for model_name in all_options[product_name]:
            for category_name in category[product_name]:
                test_table_model_category(
                    model=model_name, category=category_name, product_type=product_name
                )
