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


# results based on the selection of models and categories by the user
def write_result(score, selected_models, selected_categories):
    # Check if both models and categories are selected
    if selected_models and selected_categories:
        # Aggregate scores by model and find the model with the highest score
        aggregated_score_df = score.groupby("Modell").sum(numeric_only=True)
        best_model = aggregated_score_df.idxmax()
        best_model_name = ", ".join([str(idx) for idx in best_model])
        
        result_text = (
            f"Basierend auf den von Ihnen festgelegten Gewichtungen ergibt sich das Modell "
            f"**'{best_model_name}'** als die beste Wahl. Dieses Modell hat die höchste "
            f"Gesamtbewertung und passt am besten zu Ihren Prioritäten."
        )
        st.markdown(result_text)
    else:
        # Message when no models or categories are selected
        st.markdown(
            "Es wurden noch keine Modelle oder Kategorien ausgewählt. "
            "Bitte wählen Sie Modelle und Kategorien aus, um die Ergebnisse anzuzeigen."
        )

