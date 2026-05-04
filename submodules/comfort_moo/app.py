import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path


def create_tooltip(
    hover_text, tooltip_text, hover_text_color="green", tooltip_width="400px"
):
    return f"""
    <span class="tooltip" style="color: {hover_text_color}; display: inline-block; position: relative;">
        {hover_text}
        <span class="tooltiptext" style="display: inline; width: {tooltip_width};">
            {tooltip_text}
        </span>
    </span>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var tooltip = document.querySelector('.tooltip');
            tooltip.addEventListener('mouseenter', function() {{
                var tooltipText = tooltip.querySelector('.tooltiptext');
                tooltipText.style.display = 'inline-block';
            }});
            tooltip.addEventListener('mouseleave', function() {{
                var tooltipText = tooltip.querySelector('.tooltiptext');
                tooltipText.style.display = 'none';
            }});
        }});
    </script>
    """


def create_slice_subplots(
    slices,
    slice_selector: list = None,
    color_list: dict = None,
    vertical_line_x: float = None,
    max_cost: float = None,
    min_cost: float = None,
):
    if not isinstance(slices, list):
        slices = [slices]

    label_map = {
        "heatpump heatGrid": "Heat pump",
        "rooftop pv elecGrid": "Rooftop pv",
        "heatpump_ac heatGrid": "Air conditioning",
        "elec import elecGrid": "Grid procurement",
        "electrolyzer elecGrid": "Electrolyser",
        "fuel cell elecGrid": "Fuel cell",
        "battery storage elecGrid": "Battery",
        "gas boiler heatGrid": "Gas boiler",
    }
    color_map = {
        "electrolyzer elecGrid": "black",
        "rooftop pv elecGrid": "#f4b60e",
        "heatpump_ac heatGrid": "#ae47b5",
        "elec import elecGrid": "#978137",
        "heatpump heatGrid": "#39b539",
        "fuel cell elecGrid": "slateblue",
        "battery storage elecGrid": "seagreen",
        "gas boiler heatGrid": "darkgrey",
    }

    if isinstance(slice_selector[0], str):
        slice_title = "Clothing scenarios"
        slice_selector_suffix = ""
    else:
        slice_title = "Discomfort levels"
        slice_selector_suffix = " % PPD"
    fig = make_subplots(
        rows=len(slices) + 1,
        shared_xaxes=True,
        row_heights=[0.5, *[0.3 / len(slices)] * len(slices)],
        vertical_spacing=0.04,
        subplot_titles=["", *[f"{x}{slice_selector_suffix}" for x in slice_selector]],
    )

    for i, slic in enumerate(slices):
        slic = slic.sort_values(by="emission").reset_index(drop=True)

        # the slices as pareto fronts
        fig.add_trace(
            go.Scatter(
                x=slic.emission,
                y=slic.cost,
                name=f"{slice_selector[i]}{slice_selector_suffix}",
                legendgroup="pareto",
                legendgrouptitle_text=slice_title,
                line=dict(
                    dash="solid",
                    color=color_list[slice_selector[i]] if color_list else None,
                ),
            ),
            row=1,
            col=1,
        )

        # the slices' energy utilisation
        energy_cols = [
            col for col in slic.columns if "elecGrid" in col or "heatGrid" in col
        ]
        for col in energy_cols:
            if "demand" in col:
                continue
            values = slic[col]

            # this is either "elecGrid" (positive) or "heatGrid" (negative)
            stack_group = col.split(" ")[-1]

            fig.add_trace(
                go.Scatter(
                    x=slic.emission,
                    y=values,
                    name=label_map[col],
                    hoverinfo="x+y+text",
                    hovertext=col,
                    mode="lines",
                    fillcolor=color_map[col],
                    line=dict(width=0, color=color_map[col]),
                    stackgroup=stack_group,
                    showlegend=not i,
                    legendgroup="techs",
                    legendgrouptitle_text="Technologies",
                ),
                row=i + 2,
                col=1,
            )
        # add rectangles for electricity (yellow) & heat (red)
        fig.add_hrect(
            y0=0.0,
            y1=30,
            line_width=0,
            fillcolor="yellow",
            opacity=0.1,
            row=i + 2,
            col=1,
        )
        fig.add_hrect(
            y0=0.0,
            y1=-60,
            line_width=0,
            fillcolor="red",
            opacity=0.1,
            row=i + 2,
            col=1,
        )

        fig.update_layout({f"yaxis{i+2}": dict(title="Energy (MWh)")})

    # Add vertical box to the first subplot (row=1, col=1)
    if vertical_line_x is not None:
        fig.add_shape(
            type="rect",
            x0=vertical_line_x - 0.08,
            x1=vertical_line_x + 0.08,
            y0=min_cost - 100,
            y1=max_cost + 100,
            xref="x",
            yref="y",
            fillcolor="rgba(255, 0, 0, 0.2)",  # Set the fill color of the box
            line=dict(color="purple", width=2),
            row=1,  # Specify the row
            col=1,  # Specify the column
        )

    fig.update_layout(
        {f"xaxis{len(slices)+1}": dict(title="CO2 Emissions (t)")},
        yaxis1=dict(title="Cost (€)"),
        height=600,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def analyze_emission_data(
    df_inxd, selected_clothing, selected_comfort_levels, selectbox_key
):
    selected_data = df_inxd.loc[selected_clothing, slice(None), selected_comfort_levels]

    if not isinstance(selected_comfort_levels, list):
        selected_comfort_levels = [selected_comfort_levels]
    if not isinstance(selected_clothing, list):
        selected_clothing = [selected_clothing]

    # Count the occurrences of emissions values
    emission_counts = selected_data.index.get_level_values("emission").value_counts()
    selected_emission = None

    # Determine the length to compare based on the larger of the two lists
    max_length = max(len(selected_comfort_levels), len(selected_clothing))
    matching_emissions = sorted(
        emission_counts[emission_counts == max_length].index.tolist()
    )

    # Find emissions values occurring as frequently as the discomfort options

    if max_length > 1:
        selected_emission = st.select_slider(
            "Select an emission level to compare the costs based on your choices",
            matching_emissions,
            key=selectbox_key,
            help="For comparison, please select more than one discomfort level",
        )
        if selected_emission:
            emission_data = selected_data.xs(selected_emission, level="emission")

            # Find the highest and lowest cost values for the current emission value
            max_cost = round(emission_data["cost"].max(), 2)
            min_cost = round(emission_data["cost"].min(), 2)
            cost_diff = max_cost - min_cost

            return selected_emission, max_cost, min_cost, cost_diff
    else:
        selected_emission = st.selectbox(
            "Select Emission Level", matching_emissions, key=selectbox_key
        )
        emission_data = selected_data.xs(selected_emission, level="emission")
        cost = round(emission_data["cost"].max(), 2)

        # If selected_emission is None, return default values for other variables
    return None, cost, None, None


def text_enum(items, drop_redundancy=False):
    if len(items) == 1:
        return items[0]

    if drop_redundancy:
        first_ending = items[0].split(" ")[-1]
        if all((item.split(" ")[-1] == first_ending for item in items)):
            for i, item in enumerate(items[:-1]):
                items[i] = item.split(" ")[0]

    head = ", ".join(items[:-1])
    tail = " & " + items[-1]
    return head + tail

text_clo_lvls = {
    "light_clothing": "light clothing",
    "medium_clothing": "medium clothing",
    "warm_clothing": "warm clothing",
}


def run(debug=False):
    # Page configurations
    st.set_page_config(layout="wide", page_title="Comfort App")

    ## INTRODUCTORY TEXT ##
    st.markdown(
        "<h1 style='text-align: center;'>Exploring the Impact of User Behaviour on Residential Energy Systems</h1>",
        unsafe_allow_html=True,
    )

    def load_css(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Load CSS
    repo_root = Path(__file__).parent
    load_css(f"{repo_root}/styles.css")

    ppd_tooltip = create_tooltip(
        "Predicted Percentage Dissatisfied (PPD)",
        "PPD measures indoor comfort based on many factors including temperature, clothing level and humidity. A higher PPD indicates a less comfortable environment, while a lower PPD means better comfort.",
    )
    st.subheader("Impactful Decision-Making: Your Behavior Matters")

    markdown_content_1 = "Traditionally, energy system models focus on economic and technical aspects, neglecting the human dimension. But our recent study by [David Huckebrink, Jonas Finke and Valentin Bertsch](https://iopscience.iop.org/article/10.1088/2515-7620/ad0990) adds "
    markdown_content = f"a special measure, the {ppd_tooltip}, to evaluate thermal comfort in different scenarios. It's not just about technology; it's about how your behavior, like adjusting your clothing level, the thermostat or adopting new systems, affects the overall picture."

    # Using st.markdown for the line with the tooltip
    st.markdown(markdown_content_1+markdown_content, unsafe_allow_html=True)

    st.markdown(
        """
        **Dive in and discover:**
        - How does your behavior impact the best choices for technology in your home? 
        - Can your choices actually reduce costs, carbon emissions, and energy consumption? 
        - What advice can we give to homeowners, policymakers, and energy experts?
        """
    )

    # clothing levels description
    clothing_lvls_description = {
        "Light": [
            "T-Shirt, Thin Trousers, Ankle Socks",
            "T-Shirt, Thin Trousers, Ankle Socks",
            "T-Shirt, Thin Trousers, Ankle Socks",
        ],
        "Medium": [
            "T-Shirt, Thin Trousers, Ankle Socks",
            "Sweatpants,Long-Sleeve Sweatshirt, Ankle Socks",
            "Sweatpants, Long-Sleeve Sweatshirt, Long-Underwear Top,Calf Length Socks",
        ],
        "Warm": [
            "T-Shirt, Thin Trousers, Ankle Socks",
            "Sweatpants, Long-Sleeve Sweatshirt, Long-Underwear Top,Calf Length Socks",
            "Long-Sleeve Long Wrap Robe, long underwear bottoms, Long-Sleeve Sweatshirt, Sweatpants,Calf Length Socks",
        ],
    }
    row_names = ["Summer", "Transition-Time", "Winter"]
    df_clothing_lvls = pd.DataFrame(clothing_lvls_description, index=row_names)

    ## LOAD RESULT DATA ##
    results = pd.read_csv(
        f"{repo_root}/comfort_moo_results.csv",
    )

    results["cost"] *= 1e6
    results["discomfort"] = results["discomfort"].round(1)
    results["emission"] = results["emission"].round(1)
    df_inxd = (
        results.reset_index()
        .set_index(["clo_lvl", "emission", "discomfort"])
        .sort_index()
    )

    comfort_lvls = sorted(list(results["discomfort"].unique()))

    clothing_lvls = sorted(results.clo_lvl.unique())
    clothing_colors = {
        "light_clothing": "#3b4cc0",
        "medium_clothing": "#808080",
        "warm_clothing": "#b40426",
    }

    "---------------------------------------------------------------------------------------------------------"
    ## FIRST SECTION ##
    st.markdown(
        "<h2 style='text-align: center;'>Impact of varying levels of thermal comfort</h2>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        r"""
        Here, you can compare the impacts of different discomfort levels for a fixed clothing scenario. 
    """,
    )
    selected_emission = None
    # Mapping from the select_slider values to the original format
    clothing_mapping = {
        "Light": "light_clothing",
        "Medium": "medium_clothing",
        "Warm": "warm_clothing",
    }

    col1, col2 = st.columns((4, 6))
    with col1:
        # lider for clothing level
        selected_clothing_slider = st.select_slider(
            label="Let's start by Choosing a clothing level",
            options=["Light", "Medium", "Warm"],
            value="Medium",  # Default to medium clothing
            help="Clothing level indicates the extent of insulation or warmth provided by individuals' clothing choices, impacting thermal comfort within a residential space and influencing energy consumption, costs, and emissions in the residential energy system optimization model.",
        )
        st.write("")

        with st.expander("Check out clothing scenarios"):
            st.write("")
            st.write(
                "The table below outlines the clothing scenarios for daytime associated with each clothing level in our research. It's important to note that in all cases, individuals are assumed to be wearing underwear and slippers while seated on a standard office chair. At nighttime blankets of different thicknesses are assumed."
            )
            # Create a Streamlit table with custom CSS
            st.table(df_clothing_lvls)

        st.write("")

        # multiselect for the discomfort level
        selected_comfort_levels_1 = st.multiselect(
            "### Next, choose up to 3 discomfort levels",
            comfort_lvls[1:40:3],
            comfort_lvls[1],
            max_selections=3,
            placeholder="please select at least one option",
            help="you need to choose at least one option here. Discomfort level refers to the degree of discomfort that occupants are willing to tolerate in terms of thermal conditions within a residential space. The higher discomfort indicates that occupants are less tolerant of the current thermal conditions.",
        )
        st.write("")
        if selected_comfort_levels_1:
            st.write(
                "Upon selecting discomfort levels and your desired clothing, the corresponding 3D solution of our model is displayed on the right side. Each chosen discomfort level is represented by a line intersecting the diagram. Below, you can observe these cross-sections in 2D, providing a clearer insight into the relationship between yearly CO2 emissions and cost based on your selections."
            )

    if selected_comfort_levels_1:
        # Map the selected value to the original format
        selected_clothing_1 = clothing_mapping[selected_clothing_slider]

        selected_clothing_df_1 = results.query(f"clo_lvl == '{selected_clothing_1}'")
        selected_comfort_levels_1 = sorted(selected_comfort_levels_1)

        discomfort_slices = []
        for disc in selected_comfort_levels_1:
            # st.write(disc)
            discomfort_slices.append(
                selected_clothing_df_1.query(f"discomfort == {disc}")
            )

        # 3D surface plot
        surf_fig_1 = go.Figure(
            data=[
                go.Mesh3d(
                    x=selected_clothing_df_1.discomfort,
                    y=selected_clothing_df_1.emission,
                    z=selected_clothing_df_1.cost,
                    opacity=0.5,
                    name=selected_clothing_1,
                    color=clothing_colors[selected_clothing_1],
                )
            ],
        )
        darker_grays = px.colors.make_colorscale(
            [
                "#000000",
                "#bbbbbb",
            ],
        )
        normalized_discomforts = np.array(selected_comfort_levels_1) / max(
            selected_comfort_levels_1
        )
        discomfort_color_values = px.colors.sample_colorscale(
            darker_grays, normalized_discomforts[::-1]
        )
        discomfort_colors = dict(
            zip(selected_comfort_levels_1, discomfort_color_values)
        )

        for i, comf_slc in enumerate(discomfort_slices):
            surf_fig_1.add_trace(
                go.Scatter3d(
                    x=comf_slc.discomfort,
                    y=comf_slc.emission,
                    z=comf_slc.cost,
                    mode="markers",
                    marker={
                        "color": discomfort_colors[selected_comfort_levels_1[i]],
                        "size": 5,
                    },
                    name=f"{selected_comfort_levels_1[i]} % PPD",
                )
            )

        surf_fig_1.update_layout(
            scene=dict(
                xaxis_title="Avg. PPD (%)",
                yaxis_title="CO2 Emissions (t)",
                zaxis_title="Annual cost (€)",
            ),
            margin=dict(l=20, r=20, t=20, b=20),
            height=600,
        )

        with col2:
            three_dplot_text_1 = f"<h3 style='text-align: center;'>3D solution for {text_clo_lvls[selected_clothing_1]}</h3>"
            st.markdown(three_dplot_text_1, unsafe_allow_html=True)
            st.plotly_chart(surf_fig_1)
        col1, col2 = st.columns((4, 6))

        # Display the first figure in the first column
        with col1:
            (
                selected_emission,
                max_cost_1,
                min_cost_1,
                cost_diff_1,
            ) = analyze_emission_data(
                df_inxd, selected_clothing_1, selected_comfort_levels_1, "key1"
            )
            if cost_diff_1:
                st.write(
                    f"Based on your prior selections, choosing a higher level of discomfort can save {cost_diff_1} € per year at a level of {selected_emission} tons of CO2 emissions per year."
                )
            else:
                # in this case, max_cost is eual to the cost for one selected option
                st.write(f"Cost is: {max_cost_1} €")
                st.write(
                    f"Please, select more than one discomfort level to see the difference between highest and lowest Cost."
                )

            st.markdown(
                """
            The area charts on the right hand side display the energy usage.
            Negative numbers (on red background) show energy used for heating,
            while positive numbers (on yellow background) represent electricity.
            """
            )

        fig = create_slice_subplots(
            discomfort_slices,
            selected_comfort_levels_1,
            discomfort_colors,
            vertical_line_x=selected_emission,
            min_cost=min_cost_1,
            max_cost=max_cost_1,
        )

        # Display the second figure in the second column
        with col2:
            surfaceplot_text_1 = f"<h3 style='text-align: center;'>Energy usage with {text_clo_lvls[selected_clothing_1]}</h3>"
            st.markdown(surfaceplot_text_1, unsafe_allow_html=True)

            st.plotly_chart(fig)
    else:
        st.warning("Please select at least one discomfort level")
    "---------------------------------------------------------------------------------------------------------"
    ## SECOND SECTION ##
    st.markdown(
        "<h2 style='text-align: center;'>Impact of varying clothing levels</h2>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        r"""
        Here, you can compare the impacts of different clothing scenarios for a fixed discomfort level.
    """,
    )

    col1, col2 = st.columns((4, 6))

    with col1:
        clothing_lvls_short = ["Light", "Medium", "Warm"]

        st.write("Let's start by choosing more than one clothing level")
        cols = st.columns(len(clothing_lvls_short))

        selected_clothing_2 = []

        # Loop through each column and add a checkbox
        for i, clothing_lvl in enumerate(clothing_lvls_short):
            with cols[i]:
                is_checked = st.checkbox(
                    clothing_lvl,
                    value=(clothing_lvl == clothing_lvls_short[1]),
                    key=clothing_lvl,
                )
                if is_checked:
                    selected_clothing_2.append(clothing_lvl)
        st.write("")
        selected_comfort_levels_2 = st.select_slider(
            "Next, select a discomfort level",
            options=comfort_lvls[1:40:3],
            value=comfort_lvls[1],  # Set a default value
        )
        if len(selected_clothing_2) > 0:
            st.write("")
            st.write(
                "Upon selecting clothing levels and your desired discomfort level, the corresponding 3D solution of our model is displayed on the right side. Each chosen clothing level is represented by a line intersecting the diagram. Below, you can observe these cross-sections in 2D, providing a clearer insight into the relationship between yearly CO2 emissions and cost based on your selections."
            )
    if len(selected_clothing_2) > 0:
        # apply mapping
        selected_clothing_2 = [
            clothing_mapping[level]
            for level in selected_clothing_2
            if level in clothing_mapping
        ]
        selected_clothing_2 = sorted(selected_clothing_2)

        clo_slices_2 = results.query(f"discomfort == {selected_comfort_levels_2}")

        surf_fig_2 = go.Figure()

        clo_slices = []

        for clo_lvl in selected_clothing_2:
            selected_clothing_df_2 = results.query(f"clo_lvl == '{clo_lvl}'")

            surf_fig_2.add_trace(
                go.Mesh3d(
                    x=selected_clothing_df_2.discomfort,
                    y=selected_clothing_df_2.emission,
                    z=selected_clothing_df_2.cost,
                    opacity=0.5,
                    color=clothing_colors[clo_lvl],
                    name=clo_lvl,
                )
            )

            selected_clo_slice_2 = clo_slices_2.query(f"clo_lvl == '{clo_lvl}'")

            clo_slices.append(selected_clo_slice_2)

            surf_fig_2.add_trace(
                go.Scatter3d(
                    x=selected_clo_slice_2.discomfort,
                    y=selected_clo_slice_2.emission,
                    z=selected_clo_slice_2.cost,
                    mode="markers",
                    marker={"color": clothing_colors[clo_lvl], "size": 5},
                    name=clo_lvl,
                )
            )
        surf_fig_2.update_layout(
            scene=dict(
                xaxis_title="Avg. PPD (%)",
                yaxis_title="CO2 Emissions (t)",
                zaxis_title="Annual cost (€)",
            ),
            margin=dict(l=20, r=20, t=20, b=20),
            height=600,
        )

        with col2:
            # Join the list elements into a single string
            selected_clothing_str = text_enum([text_clo_lvls[clo] for clo in selected_clothing_2], drop_redundancy=True)
            three_dplot_text_2 = f"<h3 style='text-align: center;'>3D solution for {selected_clothing_str}</h3>"
            st.markdown(three_dplot_text_2, unsafe_allow_html=True)

            st.plotly_chart(surf_fig_2)

        col1, col2 = st.columns((4, 6))

        with col1:
            (
                selected_emission_2,
                max_cost_2,
                min_cost_2,
                cost_diff_2,
            ) = analyze_emission_data(
                df_inxd, selected_clothing_2, selected_comfort_levels_2, "key2"
            )
            if cost_diff_2:
                st.write(
                    f"Based on your prior selections, wearing warmer clothes can save {cost_diff_2} € per year at emissions of {selected_emission_2} tons of CO2 emissions per year."
                )
            else:
                # in this case, max_cost is eual to the cost for one selected option
                st.write(f"Cost is: {max_cost_2} €")
                st.write(
                    f"Please, select more than one clothing level to see the difference between Highest and Lowest Cost."
                )

            fig = create_slice_subplots(
                clo_slices,
                sorted(selected_clothing_2),
                clothing_colors,
                vertical_line_x=selected_emission_2,
                min_cost=min_cost_2,
                max_cost=max_cost_2,
            )

        # Display the second figure in the second column
        with col2:
            surfaceplot_text_2 = f"<h3 style='text-align: center;'>Energy provided for clothing levels at {selected_comfort_levels_2} % PPD</h3>"
            st.markdown(surfaceplot_text_2, unsafe_allow_html=True)
            st.plotly_chart(fig)
    else:
        st.warning("Please choose at least one clothing level")

    st.sidebar.header("Understanding Key Terms")
    st.sidebar.write(
        "**PPD**: Predicted Percentage of Dissatisfied - a measure of thermal discomfort."
    )
    st.sidebar.write(
        "**CO2 Emissions**: Greenhouse Gas Emissions refer to the emissions of gases that contribute to the greenhouse effect."
    )
    st.sidebar.write("**MWh**: Megawatt-hour, a unit of energy.")

    # Feedback and Questions
    st.sidebar.header("Your Feedback")
    st.sidebar.markdown("Share your thoughts or ask us a question @ https://www.ee.ruhr-uni-bochum.de/ee/team/huckebrink.html.de ")
    

if __name__ == "__main__":
    run()
