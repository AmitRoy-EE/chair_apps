import pandas as pd
from pathlib import Path

repo_root = Path(__file__).parent.parent


demand_series = pd.read_csv(
    f"{repo_root}/input_data/ffe_id-11-0_hourly_elec_demand.csv", index_col=0
)
# The electricity column contains generation from a 10kW Module, thus it corresponds to the capacity factor
default_inputs_df = pd.read_csv(
    f"{repo_root}/input_data/ninja_pv_51.4304_7.1458_corrected.csv",
    header=3,
    parse_dates=["time"],
    index_col=0,
)
default_inputs_df.index.freq = "h"
default_inputs_df.drop(
    ["irradiance_direct", "irradiance_diffuse", "temperature", "missing", "local_time"],
    axis=1,
    inplace=True,
)


imported_values = pd.read_csv(f"{repo_root}/input_data/default_dataset.csv")

default_inputs_df = default_inputs_df.drop("electricity", axis=1)
default_inputs_df["pv cf"] = imported_values["pv cf"].values
default_inputs_df["electricity_demand_kW"] = imported_values[
    "electricity_demand_kW"
].values
default_inputs_df["heat_demand_kW"] = imported_values["heat_demand_kW"].values
default_inputs_df["T_outside"] = imported_values["T_outside"].values

print(default_inputs_df)


def get_resampled_input_data(df, sampling_freq):
    sample_freq = f"{int(sampling_freq)}h"
    return df.resample(sample_freq).agg(
        {
            "pv cf": "mean",
            "electricity_demand_kW": "mean",
            "heat_demand_kW": "mean",
            "T_outside": "mean",
        }
    )
