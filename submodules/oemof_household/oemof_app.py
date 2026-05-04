from pathlib import Path
import streamlit as st
from input_data import get_resampled_input_data, default_inputs_df
from models.household import Household
from oemof.solph import EnergySystem, views, Model, processing
from postprocessing import get_flow_df, get_batteryStorage_df, get_bufferStorage_df
from visualisation import plot_flows_and_storage, plot_input_df
import pandas as pd
import plotly.express as px
from PIL import Image


st.set_page_config(layout="wide")


def run():
    st.markdown("# Simple Household Energy System Model")
    st.markdown(
        """
        This is an **energy system modelling tool** for a case study of a **simple household energy system**.\n

        The household energy system consists of one node with electricity demand and two units, rooftop PV and battery storage, 
        as well as a connection to the upstream grid where electricity can be purchased and fed in.\n
        
        If you select to simulate the heat system as well, the heat is provided by a heat-pump and a bufferstorage. 

        **Input parameters** can be defined below and the model automatically be solved. **Outputs** are shown as diagrams and can be downloaded as time series. 
        Depending on the input parameters the model decides on the **cost-optimal amount of investments** into rooftop PV, battery storage, heat pump and bufferstorage.\n

        This case study is embedded in ORCA.nrw.
        """
    )

    repo_root = Path(__file__).parent

    including_heat = st.selectbox(
        "**Mode of the tool:**", ("Without heat", "With heat")
    )

    if including_heat == "Without heat":
        image_scheme = Image.open(f"{repo_root}/setup/scheme_oemof.png")
        including_heat_bool = False
    else:
        image_scheme = Image.open(f"{repo_root}/setup/scheme_oemof_including_heat.png")
        including_heat_bool = True

    st.image(
        image_scheme,
        caption="Figure: Scheme of the energy system household. The demand node is depicted as a circle, the units and the upstream grid as icons and connecting lines are shown as arrows.",
        use_container_width=True,
    )

    st.markdown("## Inputs")
    st.markdown("### Upload of time series data")
    st.markdown(
        """
        You can upload a csv-file, containing hourly time series for a **PV capacity factor** (describing PV availabilty), **electricity demand**, **heating demand** and **outdoor temperature**. Please name the columns `pv cf`, `electricity_demand_kW`, `heat_demand_kW` and `T_outside`. Please do **not** provide a column concerning the dates and time. If you do not use heating, make sure to enter 0 for the values in the heat demand column `heat_demand_kW`.
        The input file must contain 1 row with the column names and 8760 rows of data (1 row per hour).
        """
    )
    uploaded_file = st.file_uploader(
        "Upload a csv-file (optional).\nIf you don't upload anything, a default time series will be used. If you don't find data for a PV capacity factor, you can simply run the model and download the results.",
        type=["csv"],
    )
    if uploaded_file is not None:
        dataframe = pd.read_csv(uploaded_file, sep=";|:|,", engine="python")
        assert len(dataframe) == 8760, AssertionError(
            f"Please provide exactly 8760 value rows. Found {len(dataframe)} rows with values."
        )
        assert all(
            col in ["pv cf", "electricity_demand_kW", "heat_demand_kW", "T_outside"]
            for col in dataframe.columns
        ), AssertionError(
            f"Please rename the columns to match [`pv cf`, `electricity_demand_kW`, `heat_demand_kW`, `T_outside`]! Found {dataframe.columns.to_list()}."
        )
        valid_cfs = (dataframe["pv cf"] >= 0) & (dataframe["pv cf"] <= 1)
        assert all(valid_cfs), AssertionError(
            f"Capacity factors must be within the range [0,1]. Found exceptions\n{dataframe[~valid_cfs]}"
        )

        raw_input_df = dataframe
        raw_input_df.index = default_inputs_df.index
    else:
        raw_input_df = default_inputs_df

    # display the input data
    st.write("### Resampled input data")
    st.markdown(
        """
        You can choose in which **time resolution** the model will be solved. 
        A range between an hourly (1 h time steps) and a daily (24 h time steps) resolution can be defined. 
        The higher the time resolution, the longer the model will take to solve. 
        Depending on your chosen time resolution, the input data time series for the PV capacity factor and the electricty demand will be **resampled**.
        
        """
    )

    sampling_freq_int = st.slider("Time resolution [hours]:", 1, 24, 12)

    input_data = get_resampled_input_data(raw_input_df, sampling_freq_int)
    T_outside_series = input_data["T_outside"].values
    cop = (
        0.0256 * T_outside_series + 3.2298
    )  # approximation based on the data of Jeter et al.
    input_data["cop"] = cop

    input_data["heat_demand_kW"] = input_data["heat_demand_kW"] * including_heat_bool

    # create the figure displaying the input time series
    fig = plot_input_df(input_data)
    st.plotly_chart(fig, use_container_width=True)

    # display the input data sliders
    st.write("### Input data settings")
    st.markdown(
        """
        **Input parameters** for specific investment cost for PV as well as battery storage can be defined.
        Also, for electricity purchases from the upstream grid an electricity price can be set. 
        
        With the **button "Start model calculation!"** the model will be automatically solved. 
        Depending on the input parameters, the energy system model decides on the **cost-optimal scheduling** of energy flows 
        as well as on **cost-optimal investments** into rooftop PV and battery storage to be made. 
        Above all, the model ensures that the **electricity demand is always met**.

        """
    )

    form = st.form("my_form")
    pv_inv_cost = form.slider(
        "PV investment cost [€/kWpeak]:", 500, 4000, 1000
    )  # €/kW_p
    battery_inv_cost = form.slider(
        "Battery storage investment cost [€/kWh]:", 100, 2000, 400
    )  # €/kWh
    electricity_price = (
        form.slider("Electricity price [ct/kWh]:", 0, 100, 30)
    )  # €/kWh
    feed_in_tariff = form.slider("Feed-in tariff [ct/kWh]", 0, electricity_price, 8)
    electricity_price /= 100
    feed_in_tariff /= 100
    heat_pump_inv_cost = form.slider(
        "Heat pump investment cost [€/kW]:", 500, 4000, 2000
    )
    heat_storage_inv_cost = form.slider(
        "Buffer storage investment cost [€/kWh]", 10, 100, 25
    )

    esm = Household(
        input_data,
        pv_inv_cost,
        battery_inv_cost,
        electricity_price,
        feed_in_tariff,
        heat_pump_inv_cost,
        heat_storage_inv_cost,
    )
    current_model_name = esm.model_name()

    current_model_path = Path(f"{repo_root}/results/{current_model_name}")
    model_has_run = current_model_path.exists()

    clicked = form.form_submit_button("Start model calculation!")

    if clicked and model_has_run:
        form.text("This Model has already been solved! Showing results:")

    if clicked or model_has_run:

        if not model_has_run:
            esm = Household(
                input_data,
                pv_inv_cost,
                battery_inv_cost,
                electricity_price,
                feed_in_tariff,
                heat_pump_inv_cost,
                heat_storage_inv_cost,
            )

            om = Model(esm)
            om.solve(solver="glpk")

            # store the results
            esm.results = processing.results(om)
            if not Path(current_model_path).exists():
                Path(current_model_path).mkdir(parents=True, exist_ok=True)
            results_filename = f"{current_model_path}/results.oemof"
            esm.dump(".", results_filename)

        esm = EnergySystem()
        esm.restore(".", f"{current_model_path}/results.oemof")

        results = esm.results
        easy_result = views.convert_keys_to_strings(results)

        st.markdown("___")
        st.markdown("## Outputs")
        st.markdown("### Electricity flows, satisfying the demand")
        st.markdown(
            """
        As the **energy balance** between electricity demand and supply must always be given, the diagrams below 
        insights into how much electricity was **generated** by rooftop PV, how much **stored** by battery storage 
        and how much **purchased** by and also fed into the upstream electricity grid. 
        The scheduling time series can be downloaded via the **button "Download result time series!"**.

        """
        )

        # collect all flows to the elec_bus for plotting
        flow_df = get_flow_df(easy_result) * sampling_freq_int
        batteryStorage_df = get_batteryStorage_df(easy_result)
        bufferStorage_df = get_bufferStorage_df(easy_result)
        fig = plot_flows_and_storage(flow_df, batteryStorage_df, bufferStorage_df)
        st.plotly_chart(fig)

        # weigh demand like oemof does for more intuitive display and postprocessing
        input_data["electricity_demand_kW"] *= sampling_freq_int
        # merge all data for download
        all_result_data = pd.concat(
            [input_data, flow_df, batteryStorage_df, bufferStorage_df], axis=1
        )
        st.download_button(
            "Download result time series!",
            all_result_data.to_csv(),
            file_name=f"flows_and_storage_{sampling_freq_int}H.csv",
            key="flow_storage",
        )

        st.markdown("### Autarky and emissions")
        st.markdown(
            """
        The **level of energy autarky of the household** is indicated by the share of PV self-consumption 
        and by shares of demand covered by rooftop PV and grid electricity purchases.
        
        """
        )

        total_electricity_demand = input_data["electricity_demand_kW"].sum()
        total_pv_gen = flow_df["rooftop pv->electricity_bus"].sum()
        total_procurement = flow_df["grid electricity->electricity_bus"].sum()
        total_feed_in = flow_df["electricity_bus->electricity_excess"].sum()
        utilized_pv_gen = total_pv_gen - total_feed_in
        self_consumption = utilized_pv_gen / total_pv_gen
        costs_of_electricity = total_procurement * electricity_price
        savings_from_pv = utilized_pv_gen * electricity_price
        earnings_from_feed_in = total_feed_in * feed_in_tariff

        totals_df = pd.DataFrame(
            dict(pv=[utilized_pv_gen], grid=[total_procurement]),
        )
        totals_df /= total_electricity_demand
        totals_df = totals_df.rename(columns={"pv": "rooftop PV"})
        totals_df = totals_df.rename(columns={"grid": "grid electricity purchase"})
        colour_map_autarky = {
            "rooftop PV": "#e4d27f",
            "grid electricity purchase": "#c2c1ff",
        }
        fig = px.pie(
            totals_df,
            names=totals_df.columns,
            values=totals_df.values.flatten(),
            title="Share of demand covered by:",
            color=totals_df.columns,
            color_discrete_map=colour_map_autarky,
        )
        # fig.data
        st.write(
            f"<span style='font-size: 45px; font-weight:bold;'>{self_consumption*100:.1f}%</span> of PV generation was self-consumed.",
            unsafe_allow_html=True,
        )

        st.plotly_chart(fig)

        st.markdown(
            """
        The electricity purchased from the **upstream grid** entails **CO$_2$ emissions**. 
        The grid electricity emissions can be altered — however, since the household energy system model is solved cost-optimally, 
        the emissions will not influence the scheduling and investment results.
        
        """
        )
        emission_factor = st.slider(
            "Grid electricity emissions [g CO₂/kWh]:", 0, 500, 300
        )
        st.write(
            f"Total grid purchase of **{total_procurement:.2f} kWh** caused <span style='font-size: 45px; font-weight:bold;'>{emission_factor*total_procurement/1000:.2f} kg CO$_2$</span>.",
            unsafe_allow_html=True,
        )

        st.markdown("### Investments")
        st.markdown(
            """
        The bar diagram below shows the **investments** in rooftop PV capacity and battery storage size. 
        The results can be downloaded via the **button "Download investment results!"**.
        
        """
        )

        storage_invest = easy_result[("Batterystorage", "electricity_bus")]["scalars"][
            "total"
        ]
        pv_invest = easy_result[("rooftop pv", "electricity_bus")]["scalars"]["total"]
        heat_pump_invest = easy_result[("heat_pump", "heat_bus")]["scalars"]["total"]
        buffer_storage_invest = easy_result[("Bufferstorage", "heat_bus")]["scalars"][
            "total"
        ]
        invest_df = pd.DataFrame(
            [
                (storage_invest, "Batterystorage capacity [kWh]"),
                (pv_invest, "rooftop PV [kW]"),
                (heat_pump_invest, "heat pump [kW]"),
                (buffer_storage_invest, "Bufferstorage capacity [kWh]"),
            ],
            columns=["amount", "category"],
        )

        total_invest = (
            invest_df["amount"][0] * battery_inv_cost
            + invest_df["amount"][1] * pv_inv_cost
            + invest_df["amount"][2] * heat_pump_inv_cost
            + invest_df["amount"][3] * heat_storage_inv_cost
        )
        colour_map_investments = {
            "rooftop PV [kW]": "#e4d27f",  # gold
            "Batterystorage capacity [kWh]": "#334871",  # darkblue
            "heat pump [kw]": "#64915a",  # dark green
            "Bufferstorage capacity [kWh]": "#e8b7e1",  # rosa
        }
        invest_fig = px.bar(
            invest_df,
            x="category",
            color="category",
            y="amount",
            color_discrete_map=colour_map_investments,
        )
        invest_fig.update_layout(
            legend=dict(title="Category"),
            yaxis={"title": "Amount"},
            xaxis={"title": "Category"},
        )

        st.plotly_chart(invest_fig)
        st.download_button(
            "Download investment results!",
            invest_df.to_csv(),
            file_name="investments.csv",
            key="investments",
        )

        st.write(f"This results into an overall investment of {total_invest:.2f} €.")
        st.write(f"Savings caused by the PV generation are {savings_from_pv:.2f} €.")
        st.write(
            f"Earnings from feeding into the electricity grid are {earnings_from_feed_in:.2f} €."
        )
        st.write(
            f"The purchased electricity from the grid costs {costs_of_electricity:.2f} €."
        )

        pass


if __name__ == "__main__":
    run()
