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
import numpy as np
import pandas as pd


def norm_min_max(x, x_min, x_max):
    """
    normalize x
    """
    if x < x_min:
        return 0
    if np.isnan(x):
        return 0
    if x_min == x_max:
        print("WARNING: x_min == x_max")
        return 0
    x_norm = (x - x_min) / (x_max - x_min)
    return x_norm


def norm_slider_values(slider_value, sum_slider_values):
    """
    normalize the slider values
    """
    if sum_slider_values == 0:
        slider_value_norm = 0
    else:
        slider_value_norm = slider_value / sum_slider_values
    return slider_value_norm


def compute_normalized_scores(df, direction, selected_categories, selected_models):
    """
    By using the function norm_min_max, it caculates the normalized value for each value in dataframe
    """
    normalized_scores = {}
    for category in selected_categories:
        x_min = min(df.loc[:, category])
        x_max = max(df.loc[:, category])
        normalized_values = []

        for model in selected_models:
            # x is specific value for a model
            x = df.loc[model, category]
            # Normalized x value, always a value between 0 and 1
            x_norm = norm_min_max(x, x_min, x_max)
            direc = direction.loc[category, "Direction"]
            if not direc:
                x_norm = 1 - x_norm
            # Append the normalized value to the list
            normalized_values.append(x_norm)

        # Store the list of normalized values in the dictionary with the category as the key
        normalized_scores[category] = normalized_values

    # Create a DataFrame from the normalized_scores dictionary
    normalized_df = pd.DataFrame(normalized_scores).T
    return normalized_df


def compute_scores(normalized_slider_values, normalized_df):
    """
    normalized_slider_values are normalized values of slider_values
    normalized_df are normalized values of the values in the dataframe
    """
    scores = normalized_df.values * np.array(normalized_slider_values)[:, np.newaxis]
    scores = pd.DataFrame(
        scores, index=normalized_df.index, columns=normalized_df.columns
    )

    return scores
