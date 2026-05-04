import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly as plt
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from modules.load_data import select_df, select_dir_df
from modules.radarchart import create_radar_chart
from modules.table import table
from modules.multi_select import create_multiselect
from modules.result import write_result
from modules.style import aligned_st_component
from modules.normalisation import (
    norm_slider_values,
    compute_scores,
    compute_normalized_scores,
)
from modules.sensitivity_analysis import (
    compute_result_sensitivity_analysis,
    compute_sensitivity_weights,
)


def run():
    app_path = Path(__file__).parent

    db_path = app_path.joinpath("database.db").absolute().as_posix()
    db_conn = sqlite3.connect(db_path)

    df1 = pd.read_sql("SELECT * FROM Heating", db_conn)

    df2 = pd.read_sql("SELECT * FROM Cars", db_conn)
    # remove the hybrid cars from car database
    df2 = df2.drop(df2[df2["Kraftstoffart"] == "Hybrid"].index)
    all_models = {
        "Fahrzeug": df2["Modell"].tolist(),
        "Heizung": df1["Anlagentyp"].tolist(),
    }

    all_categories = {
        # don't select 'Modell', 'Antriebsart' and 'Anlagentyp'
        "Fahrzeug": df2.columns[2:].tolist(),
        "Heizung": df1.columns[2:].tolist(),
    }
    # Remove "CO2 Nutzung [g/km]" and "Tankvolumen [kWh]" from the "Fahrzeug" list
    all_categories["Fahrzeug"] = [
        item
        for item in all_categories["Fahrzeug"]
        if item != "CO2 Nutzung [g/km]" and item != "Tankvolumen [kWh]"
    ]

    all_categories["Fahrzeug"].append("Gesamte CO2-Emissionen (kg)")
    all_categories["Fahrzeug"].append("Gesamtkosten (Euro)")

    # ----------------------------------------------------------------------
    # app layout
    st.set_page_config(page_title="MCDA-Webtool", page_icon="📊", layout="wide")
    st.markdown(
        "<h1 style='text-align: center;'>MCDA-Webtool</h1>", unsafe_allow_html=True
    )

    st.markdown(
        """Sie stehen vor einer schwierigen Kaufentscheidung und möchten eine gut begründete Entscheidung treffen?
                    Genau bei solchen Entscheidungen soll dieses Tool helfen. Es ist an Methoden der 'Multikriteriellen Entscheidungsanalyse' 
                (engl. [MCDA](https://de.wikipedia.org/wiki/Multi_Criteria_Analysis)) angelehnt, bei denen Ihre persönlichen Präferenzen 
                    berücksichtigt werden. Wählen Sie dafür einige Modelle und Kategorien aus und das für Sie beste Ergebnis wird am Ende der 
                    Seite angezeigt.
                    """
    )

    # ----------------------------------------------------------------------
    # radiobutton selection 'Heizung/Fahrzeug'
    selected_radio = st.radio(
        "Was möchten Sie kaufen?", all_models.keys(), horizontal=True
    )
    st.write("<hr>", unsafe_allow_html=True)

    # inputs of heating
    if selected_radio == "Heizung":
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                heating_living_area = st.number_input(
                    "Wohnfläche (m²):", min_value=1, max_value=None, value=150
                )
            with col2:
                heating_specific_demand = st.number_input(
                    "Spezifischer Raumwärmebedarf (kWh/m²):",
                    min_value=1,
                    max_value=None,
                    value=150,
                )
            with col3:
                final_energy_demand = heating_living_area * heating_specific_demand
                st.number_input(
                    "Jahresenergiebedarf = (Wohnfläche)*(Spezifischer Raumwärmebedarf)",
                    value=final_energy_demand,
                    disabled=True,
                )
    else:
        final_energy_demand = 0

    # ----------------------------------------------------------------------
    # dropdown and select all button for categories and models
    st.subheader("Modell- und Kategorienauswahl")
    with st.container():
        col1, col2 = st.columns(2)
        selected_models = create_multiselect(
            col1,
            "Alle Modelle auswählen",
            all_models[selected_radio],
            f"{selected_radio}_models",
            preselect=slice(0, 3),
        )
        selected_categories = create_multiselect(
            col2,
            "Alle Kategorien auswählen",
            all_categories[selected_radio],
            f"{selected_radio}_categories",
            preselect=slice(3, None),
        )
    # ----------------------------------------------------------------------
    # LCA Indicators

    # df as main dataframe (contains all data)
    df = select_df(selected_radio, final_energy_demand)

    if selected_radio == "Fahrzeug":
        st.subheader("Fahrzeugbetriebsdaten Eingabe")
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                years = st.number_input(
                    "Geben Sie die Anzahl der Jahre ein, die das Auto betrieben wird:",
                    min_value=1,
                    max_value=50,
                    value=10,
                )
            with col2:
                annual_kms = st.slider(
                    "Wählen Sie die Anzahl der Kilometer aus, die das Auto pro Jahr fährt:",
                    min_value=1000,
                    max_value=50000,
                    value=8000,
                )

        # Calculate the total kilometers the car will drive in its lifetime
        total_kms = years * annual_kms
        st.write(
            f"Das Auto wird in seinem Lebenszyklus ungefähr {total_kms} Kilometer fahren."
        )

        fossil_fuel_cars = df[df["Kraftstoffart"].isin(["Benzin", "Diesel"])]
        electric_cars = df[df["Kraftstoffart"].isin(["Elektro"])]

        # Categorize car weight

        # Function to find the closest weight category based on midpoints
        def find_closest_category(weight, midpoints, labels):
            closest_index = np.argmin(
                [abs(weight - midpoint) for midpoint in midpoints]
            )
            return labels[closest_index]

        # categorize fossil fueled cars' weights
        weight_bins_fossil_fuel = [0, 995.5, 1188.5, 1590.5, 1794.5, float("inf")]
        weight_labels_fossil_fuel = ["Mini", "Small", "Medium", "Large", "Extra large"]
        midpoints_weights_fossil_fuel = [
            (weight_bins_fossil_fuel[i] + weight_bins_fossil_fuel[i + 1]) / 2
            for i in range(len(weight_bins_fossil_fuel) - 1)
        ]
        fossil_fuel_cars["Weight Category"] = fossil_fuel_cars["Leergewicht [t]"].apply(
            lambda x: find_closest_category(
                x, midpoints_weights_fossil_fuel, weight_labels_fossil_fuel
            )
        )

        # categorize electric cars' weights
        weight_bins_electric = [0, 1051.5, 1344, 1834, 2031.5, float("inf")]
        weight_labels_electric = ["Mini", "Small", "Medium", "Large", "Extra large"]
        midpoints_weights_electric = [
            (weight_bins_electric[i] + weight_bins_electric[i + 1]) / 2
            for i in range(len(weight_bins_electric) - 1)
        ]
        electric_cars["Weight Category"] = electric_cars["Leergewicht [t]"].apply(
            lambda x: find_closest_category(
                x, midpoints_weights_electric, weight_labels_electric
            )
        )

        # Embedded CO2 Emissions (kg) based on car size
        embedded_emissions_fossil_fuel = {
            "Mini": 6795.567,
            "Small": 8738.554,
            "Medium": 11690.59,
            "Large": 13820.16,
        }

        fossil_fuel_cars["Embedded CO2 Emissions (kg)"] = fossil_fuel_cars[
            "Weight Category"
        ].map(embedded_emissions_fossil_fuel)

        fossil_fuel_cars["Total CO2 Lifetime (kg)"] = (
            fossil_fuel_cars["CO2 Nutzung [g/km]"] * total_kms / 1000
        )

        fossil_fuel_cars["Gesamte CO2-Emissionen (kg)"] = (
            fossil_fuel_cars["Embedded CO2 Emissions (kg)"]
            + fossil_fuel_cars["Total CO2 Lifetime (kg)"]
        )

        # electric cars
        embedded_emissions_electric = {
            "Mini": 10392.65335,
            "Small": 13750.44053,
            "Medium": 18686.96947,
            "Large": 23702.48043,
        }

        electric_cars["lifetime_kwh"] = (
            electric_cars["Kraftstoffverbrauch [kWh/100km]"] * total_kms / 100
        )

        # https://www.nowtricity.com/country/germany/ based on this website the electricity emission intensity in year 2023 is 354 g/kwh
        emission_intensity = 354 / 2
        electric_cars["Total CO2 LIfetime (kg)"] = (
            emission_intensity * electric_cars["lifetime_kwh"] / 1000
        )

        electric_cars["Embedded CO2 Emissions (kg)"] = electric_cars[
            "Weight Category"
        ].map(embedded_emissions_electric)
        electric_cars["Gesamte CO2-Emissionen (kg)"] = (
            electric_cars["Embedded CO2 Emissions (kg)"]
            + electric_cars["Total CO2 LIfetime (kg)"]
        )

        car_embedded_emissions = pd.concat(
            [
                fossil_fuel_cars["Embedded CO2 Emissions (kg)"],
                electric_cars["Embedded CO2 Emissions (kg)"],
            ],
            axis=0,
        )

        df["Gesamte CO2-Emissionen (kg)"] = None

        # Update the column with calculated values for fossil fuel cars
        df.loc[fossil_fuel_cars.index, "Gesamte CO2-Emissionen (kg)"] = (
            fossil_fuel_cars["Gesamte CO2-Emissionen (kg)"]
        )

        # Update the column with calculated values for electric cars
        df.loc[electric_cars.index, "Gesamte CO2-Emissionen (kg)"] = electric_cars[
            "Gesamte CO2-Emissionen (kg)"
        ]
        # Fill None values with 0
        df["Gesamte CO2-Emissionen (kg)"].fillna(0, inplace=True)

        # Update the column with calculated values for fossil fuel cars
        df.loc[fossil_fuel_cars.index, "Weight Category"] = fossil_fuel_cars[
            "Weight Category"
        ]

        # Update the column with calculated values for electric cars
        df.loc[electric_cars.index, "Weight Category"] = electric_cars[
            "Weight Category"
        ]

    # ----------------------------------------------------------------------
    # life cycle costs
    if selected_radio == "Fahrzeug":
        car_purchase_cost = df["Kaufpreis [€]"]

        # calculate the fuel liters or kwhs over lifetime
        # number for the energy density of benzin and diesel from: https://nachhaltigmobil.schule/leistung-energie-verbrauch/#:~:text=Wie%20sieht%20das%20in%20Zahlen,9%2C8%20kWh%20pro%20Liter.
        df.loc[df["Kraftstoffart"] == "Benzin", "Lifetime_fuel_liters_or_kwh"] = (
            df["Kraftstoffverbrauch [kWh/100km]"] / 8.5
        ) * (total_kms / 100)
        df.loc[df["Kraftstoffart"] == "Diesel", "Lifetime_fuel_liters_or_kwh"] = (
            df["Kraftstoffverbrauch [kWh/100km]"] / 9.8
        ) * (total_kms / 100)
        df.loc[df["Kraftstoffart"] == "Elektro", "Lifetime_fuel_liters_or_kwh"] = df[
            "Kraftstoffverbrauch [kWh/100km]"
        ] * (total_kms / 100)

        df["Lifetime_operational_costs [€]"] = 0
        # average kwh price in germany for year 2023 is 0.42 Euro per kWh
        df.loc[df["Kraftstoffart"] == "Elektro", "Lifetime_operational_costs [€]"] = (
            df["Lifetime_fuel_liters_or_kwh"] * 0.42
        )
        # average price per liter of Benzin in germany in year 2023 is 1.849 euro: https://www.statista.com/statistics/1346041/premium-gasoline-average-price-germany/

        df.loc[df["Kraftstoffart"] == "Benzin", "Lifetime_operational_costs [€]"] = (
            df["Lifetime_fuel_liters_or_kwh"] * 1.849
        )
        # average price per liter of Diesel in germany in year 2023 is 1.737 euro:https://www.statista.com/statistics/1346072/diesel-fuel-average-price-germany/
        df.loc[df["Kraftstoffart"] == "Diesel", "Lifetime_operational_costs [€]"] = (
            df["Lifetime_fuel_liters_or_kwh"] * 1.737
        )
        car_operational_costs = df["Lifetime_operational_costs [€]"]
        df["purchase_and_operational_costs_lifetime [€]"] = (
            car_operational_costs + car_purchase_cost
        )
        car_purchase_and_operation_costs = df[
            "purchase_and_operational_costs_lifetime [€]"
        ]

        # applying the fixed costs

        # source for deciding on electric cars fixed costs: https://www.ayvens.com/en-cp/blog/total-cost-of-ownership/tco-ev-ice-comparison/
        # based on this the fixed costs of electric cars are 23% less than fossil fueled cars
        # source for the fossil fueled cars fixed costs: https://www.sciencedirect.com/science/article/pii/S0921800921003943?via%3Dihub

        fixed_costs_share_of_tco_small = 0.04 / 0.45
        fixed_costs_share_of_tco_large = 0.08 / 0.86
        fixed_costs_share_of_tco_small_electric = (
            1 - fixed_costs_share_of_tco_small * 0.77
        )
        fixed_costs_share_of_tco_large_electric = (
            1 - fixed_costs_share_of_tco_large * 0.77
        )
        # Define the conditions
        condition_fossil_fuel_small = (
            df["Kraftstoffart"].isin(["Diesel", "Benzin"])
        ) & (df["Weight Category"].isin(["Small", "Medium"]))
        condition_fossil_fuel_large = (
            df["Kraftstoffart"].isin(["Diesel", "Benzin"])
        ) & (df["Weight Category"].isin(["Large"]))
        condition_electric_large = (df["Kraftstoffart"].isin(["Elektro"])) & (
            df["Weight Category"].isin(["Large"])
        )
        condition_electric_small = (df["Kraftstoffart"].isin(["Elektro"])) & (
            df["Weight Category"].isin(["Small", "Medium"])
        )
        # Apply the conditions to update the column
        df.loc[
            condition_fossil_fuel_small,
            "purchase_and_operational_and_fixed_costs_lifetime [€]",
        ] = df["purchase_and_operational_costs_lifetime [€]"] / (
            1 - fixed_costs_share_of_tco_small
        )
        df.loc[
            condition_fossil_fuel_large,
            "purchase_and_operational_and_fixed_costs_lifetime [€]",
        ] = df["purchase_and_operational_costs_lifetime [€]"] / (
            1 - fixed_costs_share_of_tco_large
        )

        df.loc[
            condition_electric_small,
            "purchase_and_operational_and_fixed_costs_lifetime [€]",
        ] = df["purchase_and_operational_costs_lifetime [€]"] / (
            fixed_costs_share_of_tco_small_electric
        )
        df.loc[
            condition_electric_large,
            "purchase_and_operational_and_fixed_costs_lifetime [€]",
        ] = df["purchase_and_operational_costs_lifetime [€]"] / (
            fixed_costs_share_of_tco_large_electric
        )

        df.rename(
            columns={
                "purchase_and_operational_and_fixed_costs_lifetime [€]": "Gesamtkosten (Euro)"
            },
            inplace=True,
        )
        car_purchase_and_operation_and_fixed_costs = df["Gesamtkosten (Euro)"]

    # df based on selected models and categories
    df_transpose = df.transpose()
    df_slc_model = df_transpose[selected_models]
    df_slc_model_transpose = df_slc_model.transpose()
    df_slc_model_category = df_slc_model_transpose[selected_categories]

    # ----------------------------------------------------------------------
    # table and radio button for df selecion
    st.subheader("Modellvergleich: Detaillierte Daten")

    # radio button: min and max values shown in the table based on the entire database or selected database
    min_max_button = st.radio(
        "Minimal- und Maximalwert angezeigen basierend auf...",
        ("... der gesamten Datenbank.", "... den ausgewählten Modellen."),
        horizontal=True,
    )
    if min_max_button == "... den ausgewählten Modellen.":
        df = df_slc_model_category

    # table
    st.write(
        "Tabelle ausgewählter Modelle und Kategorien mit den entsprechenden Werten."
    )

    tab = table(
        selected_radio, selected_models, selected_categories, df, final_energy_demand
    )
    st.table(tab.style.format(precision=2))

    # text below table
    txt_table = ""
    if selected_radio == "Heizung":
        if "Energiebedarf [kWh]" in selected_categories:
            txt_table = "\n* Der Energiebedarf wird anhand der Eingabewerte über der Tabelle berechnet. Bitte stellen Sie sicher, dass Sie korrekte Daten verwenden."

    if selected_radio == "Fahrzeug":
        txt_table = "\n* Kraftstoffverbrauch [kWh/100km] errechnet sich aus dem Verbrauch [L/100km] und den Heizwerten für Diesel (=9,7 kWh/L) und Benzin (=8,5 kWh/L)\
                    \n* Tankvolumen [kWh] errechnet sich aus dem Tankvolumen [L] und den Heizwerten für Diesel (=9,7 kWh/L) und Benzin (=8,5 kWh/L)\
                    \n* Reichweite [km] und CO2-Emissionen [g/km] nach [WLTP](https://en.wikipedia.org/wiki/Worldwide_Harmonised_Light_Vehicles_Test_Procedure)"

    # Convert the DataFrame to CSV
    csv = tab.to_csv(index=False)

    # Add the download button with descriptive German text
    st.download_button(
        label="Daten als CSV herunterladen",
        data=csv,
        file_name="modellvergleich_daten.csv",
        mime="text/csv",
        help="Klicken Sie hier, um die Tabelle als CSV-Datei herunterzuladen. Diese Datei enthält die ausgewählten Modelle und Kategorien sowie deren Werte.",
    )

    st.markdown(txt_table)

    # ----------------------------------------------------------------------
    # Plot the emission data
    if selected_radio == "Fahrzeug":
        with st.expander(
            "Lebenszyklusanalyse: CO2-Emissionen und Gesamtkosten der Fahrzeuge"
        ):
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    x_start = 0
                    x_end = total_kms

                    car_emission_df = pd.DataFrame(
                        car_embedded_emissions.loc[selected_models]
                    ).rename(
                        columns={
                            "Embedded CO2 Emissions (kg)": "Gesamte CO2-Emissionen (kg)"
                        }
                    )

                    car_emission_df["kilometers"] = x_start
                    car_var_emissions_df = pd.DataFrame(
                        df_slc_model.loc["Gesamte CO2-Emissionen (kg)"]
                    )
                    car_var_emissions_df["kilometers"] = x_end
                    car_total_emissions_df = pd.concat(
                        [car_emission_df, car_var_emissions_df]
                    )

                    fig = go.Figure()

                    car_cost_df = pd.DataFrame(car_purchase_cost).rename(
                        columns={"Kaufpreis [€]": "Gesamtkosten (Euro)"}
                    )
                    car_cost_df["kilometers"] = x_start
                    car_fom_df = pd.DataFrame(
                        car_purchase_and_operation_and_fixed_costs
                    )
                    car_fom_df["kilometers"] = x_end

                    car_total_cost_df = pd.concat([car_cost_df, car_fom_df]).loc[
                        selected_models
                    ]
                    lca_df = pd.concat(
                        [
                            car_total_cost_df.melt(
                                id_vars=["kilometers"], ignore_index=False
                            ),
                            car_total_emissions_df.melt(
                                id_vars=["kilometers"], ignore_index=False
                            ),
                        ]
                    )
                    lca_fig = px.line(
                        lca_df.reset_index(),
                        x="kilometers",
                        y="value",
                        color="Modell",
                        facet_row="variable",
                    )
                    lca_fig.for_each_annotation(lambda a: a.update(text=""))
                    lca_fig.update_layout(
                        yaxis1_title="Gesamte CO2-Emissionen (kg)",
                        yaxis2_title="Gesamtkosten (€)",
                        xaxis_title="Fahrleistung (km)",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                        ),
                        margin={"r": 20},
                        height=700,
                    )
                    lca_fig.update_yaxes(matches=None)

                    st.plotly_chart(lca_fig, use_container_width=True)
                with col2:
                    st.markdown("""
                    ### Diagrammübersicht

                    Das obere Diagramm zeigt die **Lebenszykluskosten**, während das untere Diagramm die **CO2-Emissionen** für verschiedene Fahrzeugmodelle über deren **Lebensdauer** darstellt.

                    #### 1. **Lebenszykluskosten (Gesamtkosten)**
                    Dieses Diagramm vergleicht die Kosteneffizienz verschiedener Autos bei steigender Kilometerleistung.
                    - **Kaufpreis**: Anfangskosten für den Autokauf.
                    - **Betriebs- und Wartungskosten**: Laufende Kosten wie Kraftstoff, Wartung und Steuern, die mit der Fahrstrecke zunehmen.

               

                    #### 2. **CO2-Emissionen (Gesamtemissionen)**
                    Dieses Diagramm zeigt, wie sich die Emissionen für jedes Modell summieren, wobei sparsamere Autos über die Zeit geringere betriebsbedingte Emissionen haben.
                    - **Eingebettete Emissionen**: Emissionen aus der Fahrzeugproduktion (Materialgewinnung, Herstellung) bleiben konstant, unabhängig von der gefahrenen Strecke. (Daten abgeleitet von [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S030626192030533X) und [Carculator](https://carculator.psi.ch/tool/DE))
                    - **Betriebsbedingte Emissionen**: Emissionen aus dem Kraftstoff- oder Stromverbrauch, die mit zunehmender Kilometerzahl steigen. Für Elektroautos wurde eine Emissionsintensität von 354 g CO2eq/kWh auf Basis von [Nowtricity](https://www.nowtricity.com/country/germany/) für das Jahr 2023 verwendet.


                    """)

    # ----------------------------------------------------------------------
    # slider (score calculations) and radar (side by side)
    with st.container():
        col1, col2 = st.columns([1, 2])

        with col1:
            # slider
            st.subheader("Kategoriegewichtung nach Relevanz")
            st.write(
                "Passen Sie die Bedeutung jeder Kategorie an, indem Sie eine Gewichtung auf einer Skala von 0 (weniger relevant) bis 5 (sehr relevant) vornehmen:"
            )
            slider_values = {}
            for c in selected_categories:
                value = st.slider(c, min_value=0, max_value=5, value=1, step=1)
                slider_values[c] = value

            # ----------------------------------------------------------------------
            # score calculations

            normalized_slider_values = []
            weight_range = np.arange(0, 1.1, 0.1)

            for val in list(slider_values.values()):
                normalized_slider_value = norm_slider_values(
                    val, sum(slider_values.values())
                )
                normalized_slider_values.append(normalized_slider_value)

            # direction is 0 or 1 (the more the better)
            direction = select_dir_df(selected_radio)
            if selected_radio == "Fahrzeug":
                direction.loc["Gesamte CO2-Emissionen (kg)"] = 0
                direction.loc["Gesamtkosten (Euro)"] = 0

            normalized_df = compute_normalized_scores(
                df, direction, selected_categories, selected_models
            )
            normalized_df.columns = selected_models

            scores = compute_scores(normalized_slider_values, normalized_df)

            # scores for bar chart
            stacked_scores = scores.stack().reset_index()
            stacked_scores.columns = ["Kategorie", "Modell", "Score"]

        with col2:
            # radar chart
            radar = create_radar_chart(scores, None)
            st.subheader("Vergleich der Kategorien: Radar-Diagramm")
            st.write(
                "Das Radar-Diagramm visualisiert die normalisierten Beiträge jeder Kategorie basierend auf Ihrer Gewichtung. Eine größere Fläche zeigt eine höhere Übereinstimmung eines Modells mit Ihren Prioritäten an."
            )
            st.plotly_chart(radar, use_container_width=True)

    # ----------------------------------------------------------------------
    # bar chart
    st.subheader("Vergleich der Kategorienbeiträge: Gestapeltes Balkendiagramm")
    st.write(
        "Visualisiert die gewichteten Beiträge jeder Kategorie. Höhere Balken bedeuten eine stärkere Übereinstimmung eines Modells mit Ihren Gewichtungen."
    )

    bar_chart = px.bar(
        stacked_scores,
        x="Modell",
        y="Score",
        color="Kategorie",
        barmode="stack",
    )

    st.plotly_chart(bar_chart, use_container_width=True)

    # ----------------------------------------------------------------------
    # results
    st.subheader("Zusammenfassung der Ergebnisse")
    write_result(stacked_scores, selected_models, selected_categories)

    # ----------------------------------------------------------------------
    # senstivity analysis

    with st.expander(
        "Sensitivitätsanalyse: Einfluss der Kategoriegewichtung auf die Modellbewertung"
    ):
        sensitive_category = st.selectbox(
            "Kategorie für Sensitivitätsanalyse auswählen", selected_categories
        )
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                # Get the index of the selected option
                sensitivity_idx = selected_categories.index(sensitive_category)
                sensitivity_weights = compute_sensitivity_weights(
                    normalized_slider_values, sensitivity_idx, weight_range
                ).set_index(normalized_df.index)
                sensitivity_weights.columns = weight_range
                result_sensitivity_analysis = compute_result_sensitivity_analysis(
                    normalized_df, sensitivity_weights
                )

                # line chart
                fig = px.line(result_sensitivity_analysis.T, height=400)

                fig.update_layout(
                    legend_title_text="Ausgewählte Modelle",
                    xaxis_title="Gewicht der Kategorie",
                    yaxis_title="Gesamtscore der Modelle",
                    legend=dict(orientation="h", y=1.2, xanchor="right", x=1),
                    margin={
                        "r": 20,
                    },
                )

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("""
                ### Übersicht zur Sensitivitätsanalyse:
                            
                Dieses Diagramm hilft Ihnen dabei zu erkennen, wie empfindlich jedes Modell auf Veränderungen in der Gewichtung einer bestimmten Kategorie reagiert. Eine steilere Linie bedeutet, dass die Leistung des Modells stärker von der Gewichtung dieser Kategorie beeinflusst wird.

                Im Diagramm sehen Sie, wie sich die Gesamtnoten der verschiedenen Modelle ändern, wenn die Bedeutung einer ausgewählten Kategorie zunimmt. Jede Linie steht für ein anderes Modell. Wenn das Gewicht der ausgewählten Kategorie entlang der x-Achse steigt, können Sie sehen, wie sich die Punktzahl jedes Modells (auf der y-Achse) entsprechend anpasst. So können Sie leichter erkennen, welche Modelle basierend auf den für Sie wichtigsten Faktoren besser abschneiden.
                """)

    # ----------------------------------------------------------------------
    # footer
    st.write("")
    aligned_st_component(
        st.markdown,
        """
 
    - [Quellcode auf GitLab](https://gitlab.ruhr-uni-bochum.de/ee/mcda-dashboard)
    - [Feedback geben](https://www.ee.ruhr-uni-bochum.de/ee/team/huckebrink.html.de)
    """,
        "left",
    )


if __name__ == "__main__":
    run()
