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

import plotly.graph_objects as go
import pandas as pd
import plotly.express as px  # (version 4.7.0)


def empty_radar():
    empty_df = pd.DataFrame(dict(r=[1], theta=[""]))
    empty_radar = px.line_polar(
        empty_df,
        r="r",
        theta="theta",
    )
    return empty_radar


def create_radar_chart(scores, final_energy_demand=None):
    """
    this functions plots a radar chart based on the calculated scores
    scores is a dataframe which the rows correspond to categories and columns to models

    """
    # check if more than one category is selected. Only then a radar chart can be generated
    if len(scores.index.tolist()) >= 2:
        radar_chart = go.Figure()
        # in line below: dataframe is transformed into a dict, where keys are the models and values are values of the dataframe corresponding to each model
        for model, score_list in scores.to_dict(orient="list").items():
            # add trace for every model in the dictionary = for every model selected a new radar chart area is created
            radar_chart.add_trace(
                go.Scatterpolar(
                    r=score_list,
                    theta=scores.index.tolist(),
                    fill="toself",
                    name=model,
                )
            )

        radar_chart.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                )
            ),
            showlegend=True,
            margin=dict(l=200, r=0, t=0, b=0, pad=10),
        )

        return radar_chart
    else:
        return empty_radar()
