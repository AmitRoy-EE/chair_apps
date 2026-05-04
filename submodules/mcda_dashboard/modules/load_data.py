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
from pathlib import Path

repo_root = Path(__file__).parents[1]


def select_df(selected_radio, final_energy_demand=None):
    # selects and loads the correct data frames (for general data)
    # if selected_model != [] and selected_category != []: #prevent the function from call before assignment
    db_conn = sqlite3.connect(f"{repo_root}/database.db")
    cur = db_conn.cursor()

    if selected_radio == "Heizung":
        df = pd.read_sql("SELECT * FROM Heating", db_conn)
        df = df.set_index("Anlagentyp")
        if not pd.isna(final_energy_demand):
            df["Energiebedarf [kWh]"] = final_energy_demand / (
                df["Wirkungsgrad [%]"] / 100
            )
            df["Energiebedarf [kWh]"] = df["Energiebedarf [kWh]"].round(2)
        else:
            df["Energiebedarf [kWh]"] = 0
    if selected_radio == "Fahrzeug":
        df = pd.read_sql("SELECT * FROM Cars", db_conn)
        # remove the hybrid cars from car database
        df = df.drop(df[df['Kraftstoffart'] == 'Hybrid'].index)
        df = df.set_index("Modell")

    return df


def select_dir_df(
    selected_radio,
):  # select and load the correct data frame for macda direction
    db_conn = sqlite3.connect(f"{repo_root}/database.db")
    cur = db_conn.cursor()
    if selected_radio == "Heizung":
        dir_mcda_heating = pd.read_sql("SELECT * FROM MCDA_Direction_Heating", db_conn)
        dir_df = dir_mcda_heating.set_index("Category")

    if selected_radio == "Fahrzeug":
        dir_mcda_cars = pd.read_sql("SELECT * FROM MCDA_Direction_Cars", db_conn)
        dir_df = dir_mcda_cars.set_index("Category")

    return dir_df
