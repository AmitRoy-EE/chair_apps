import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_flows_and_storage(flow_df, batteryStorage_df, bufferStorage_df):
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        # subplot_titles=("Electricity balance", "Storage content"),
    )

    colour_map_flows = {'rooftop PV': '#e4d27f', #gold
                        'Batterystorage charging': '#dbecff', #lightblue
                        'Batterystorage discharging': '#8394c3', #mediumblue
                        'Bufferstorage charging': '#e8b7e1', #rosa
                        'Bufferstorage discharging': '#59d9d0', #turkuis 
                        'feed-in in electricity grid': '#6CA380', #green
                        'grid electricity purchase': '#c2c1ff', #lilac
                        'heat pump electricity input': '#64915a', #dark green
                        }

    for col in flow_df.columns:
        if "demand" in col:
            continue
        if "heat_bus" in col:
            continue
        key1, key2 = col.split("->")
        stack_group = "positive" if "bus" in key2 else "negative"
        sign = 1 if "bus" in key2 else -1

        if "Batterystorage" in key1:
            trace_name = "Batterystorage discharging"
        elif "Batterystorage" in key2:
            trace_name = "Batterystorage charging"
        elif "Bufferstorage" in key1:
            trace_name = "Bufferstorage discharging"
        elif "Bufferstorage" in key2:
            trace_name = "Bufferstorage charging"
        elif "rooftop" in key1:
            trace_name = "rooftop PV"
        elif "electricity_bus" in key1 and "excess" in key2:
            trace_name = "feed-in in electricity grid"
        elif "grid" in key1:
            trace_name = "grid electricity purchase"
        elif "electricity_bus" in key1 and "heat_pump" in key2:
            trace_name = "heat pump electricity input"
        else:
            trace_name = col

        fig.add_trace(
            go.Scatter(
                x=flow_df.index,
                y=flow_df[col] * sign,
                name=trace_name,
                hoverinfo="x+y+name",
                mode="lines",
                line=dict(width=0),
                fillcolor=colour_map_flows[trace_name],
                stackgroup=stack_group,
                
            ),
            row=1,
            col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=batteryStorage_df.index,
            y=batteryStorage_df["storage_content"],
            name="Batterystorage content",
            line=dict(width=0.7),
            marker=dict(color='#334871'), #darkblue
        ),
        row=2,
        col=1,
    )
    
    fig.add_trace(
        go.Scatter(
            x=bufferStorage_df.index,
            y=bufferStorage_df["storage_content"],
            name="Bufferstorage content",
            line=dict(width=0.7),
            marker=dict(color='#34ebeb'), #brightblue
        ),
        row=3,
        col=1,
    )

    fig.update_layout(
        yaxis1={"title": "Energy balance [kWh/timestep]"},
        yaxis2={"title": "Batterystorage content [kWh]"},
        yaxis3={"title": "Bufferstorage content [kWh]"},
        width=800,
        height=900,
        margin=dict(t=30, l=10, b=10),
        legend={"traceorder": "reversed"},
    )

    return fig


def plot_input_df(input_data):
    fig = make_subplots(rows=2, cols=2, shared_xaxes=True, vertical_spacing=0.05, horizontal_spacing=0.2)
    fig.add_trace(
        go.Scatter(
            x=input_data.index,
            y=input_data["electricity_demand_kW"],
            name="Electricity demand",
            line=dict(width=0.7),
            mode='lines',
            marker=dict(color='#51548a') #darklilac
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=input_data.index,
            y=input_data["pv cf"],
            name="PV availability",
            line=dict(width=0.7),
            mode='lines',
            marker=dict(color='#e4d27f') #gold
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=input_data.index,
            y=input_data["heat_demand_kW"],
            name="Heat demand",
            line=dict(width=0.7),
            mode='lines',
            marker=dict(color='#e82700') #red
        ),
        row=1,
        col=2,
    )
    
    fig.add_trace(
        go.Scatter(
            x=input_data.index,
            y=input_data["cop"],
            name="COP",
            line=dict(width=0.7),
            mode='lines',
            marker=dict(color='#32a852') #green
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        yaxis={"title": "Electricity Demand [kWh/timeStep]"},
        yaxis3={"title": "PV Availability"},
        yaxis2={"title": "Heat Demand [kWh/timeStep]"},
        yaxis4={"title": "Coefficient of Performance [-]"},
        width=800,
        height=600,
        margin=dict(t=30, b=10, l=10, r=10),
    )
    fig.update_xaxes(matches="x1")
    return fig
