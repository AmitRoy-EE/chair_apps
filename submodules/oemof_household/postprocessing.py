import pandas as pd


def plot_all_flows_to_dir(easy_result, result_dir):
    for key1, key2 in easy_result.keys():
        val = easy_result[(key1, key2)]
        if "sequences" in val.keys():
            try:
                ax = val["sequences"].plot()
                ax.legend(title=f"{key1} --> {key2}")
                ax.get_figure().savefig(f"{result_dir}/{key1}_{key2}_p_el_.png")
            except:
                print("error on", key1, key2)


def get_flow_df(easy_result):
    flow_df = pd.DataFrame()
    for key1, key2 in easy_result.keys():
        if "bus" in key2 or "bus" in key1:
            result = easy_result[(key1, key2)]
            if "sequences" in result.keys():
                r_ts = result["sequences"]
                flow_df[f"{key1}->{key2}"] = r_ts
    return flow_df


def get_batteryStorage_df(easy_result):
    return easy_result[("Batterystorage", "None")]["sequences"]

def get_bufferStorage_df(easy_result):
    return easy_result[("Bufferstorage", "None")]["sequences"]
