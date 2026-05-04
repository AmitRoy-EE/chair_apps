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
import pandas as pd


def weight_adaptation(idx, normalized_slider_values, sensitivity_idx, sensitivity_val):
    if idx == sensitivity_idx:
        return sensitivity_val

    a_val = normalized_slider_values[idx] / sum(normalized_slider_values)
    b_val = (
        normalized_slider_values[sensitivity_idx] / sum(normalized_slider_values)
        - sensitivity_val
    )
    b_val *= normalized_slider_values[idx] / (
        sum(normalized_slider_values) - normalized_slider_values[sensitivity_idx]
    )
    return a_val + b_val


def compute_sensitivity_weights(
    normalized_slider_values, sensitivity_idx, weight_range
):
    """
    This function calculates the weights for sensitivity analysis based on the function "weight_adaptation"
    normalized_slider_values are normalized values of slider_values
    sensitivity_idx is the index of selected category from the dropdown
    weight range is stepped values between 0 and 1

    """
    sensitivity_weights = []
    for sens_w in weight_range:
        temp_list = []
        for idx, _ in enumerate(normalized_slider_values):
            temp_list.append(
                weight_adaptation(
                    idx, normalized_slider_values, sensitivity_idx, sens_w
                )
            )
        sensitivity_weights.append(temp_list)
    return pd.DataFrame(sensitivity_weights).T


def compute_result_sensitivity_analysis(normalized_df, weights_sensitivity_analysis):
    """
    multiply the result of 2 functions : compute_normalized_scores and compute_sensitivity_weights
    """
    result_df = pd.DataFrame()
    # Iterate through the columns
    for col in normalized_df.columns:
        for column in weights_sensitivity_analysis.columns:
            # Multiply the first column of normalized_df with the current column in weights_sensitivity_analysis
            multiply = weights_sensitivity_analysis[column].multiply(normalized_df[col])
            # Sum the results column-wise
            result_sum = multiply.sum()
            # Add the result to the result_df
            result_df.at[col, column] = result_sum
    return result_df
