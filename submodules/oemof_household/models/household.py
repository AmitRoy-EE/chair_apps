import hashlib
import sys
from pathlib import Path
from oemof.tools import economics
from oemof.solph import (
    Flow,
    EnergySystem,
    Bus,
    Investment,
    Model,
    processing,
)
from oemof.solph.components import (
    Sink,
    Source,
    GenericStorage,
    Converter,
)
import pandas as pd
from input_data import default_inputs_df, get_resampled_input_data


class Household(EnergySystem):
    def __init__(
        self,
        ts_data: pd.DataFrame,
        pv_inv_cost,
        battery_inv_cost,
        grid_electricity_price,
        feed_in_tariff,
        heat_pump_inv_cost,
        heat_storage_inv_cost,
        pv_lifetime=20,
        battery_lifetime=10,
        heat_pump_lifetime=20,
        heat_storage_lifetime=20,
        wacc=0.05,
        **kwargs,
    ):

        timeindex = ts_data.index
        electricity_demand_series = ts_data["electricity_demand_kW"].values
        pv_capacity_series = ts_data["pv cf"].values
        heat_demand_series = ts_data["heat_demand_kW"].values
        cop_series = ts_data["cop"].values

        self.ts_data = ts_data
        self.pv_inv_cost = pv_inv_cost
        self.battery_inv_cost = battery_inv_cost
        self.grid_electricity_price = grid_electricity_price
        self.feed_in_tariff = feed_in_tariff
        self.heat_pump_inv_cost = heat_pump_inv_cost
        self.heat_storage_inv_cost = heat_storage_inv_cost

        super().__init__(timeindex=timeindex, infer_last_interval=True, **kwargs)
        self.sampling_freq = self.timeincrement[0]

        pv_annual_costs = economics.annuity(pv_inv_cost, pv_lifetime, wacc)
        battery_annual_costs = economics.annuity(
            battery_inv_cost, battery_lifetime, wacc
        )
        heat_pump_annual_costs = economics.annuity(
            heat_pump_inv_cost, heat_pump_lifetime, wacc
        )
        heat_storage_annual_costs = economics.annuity(
            heat_storage_inv_cost, heat_storage_lifetime, wacc
        )

        electricity_bus = Bus(label="electricity_bus")
        heat_bus = Bus(label="heat_bus")

        electricity_demand_sink = Sink(
            label="electricity_demand",
            inputs={
                electricity_bus: Flow(fix=electricity_demand_series, nominal_value=1)
            },
        )

        heat_demand_sink = Sink(
            label="heat_demand",
            inputs={heat_bus: Flow(fix=heat_demand_series, nominal_value=1)},
        )

        pv_source = Source(
            label="rooftop pv",
            outputs={
                electricity_bus: Flow(
                    fix=pv_capacity_series,
                    investment=Investment(ep_costs=pv_annual_costs, maximum=50),
                )
            },
        )

        heat_pump_transformer = Converter(
            label="heat_pump",
            inputs={
                electricity_bus: Flow(
                    investment=Investment(ep_costs=heat_pump_annual_costs)
                )
            },
            outputs={
                heat_bus: Flow(investment=Investment(ep_costs=heat_pump_annual_costs))
            },
            conversion_factors={electricity_bus: 1 / cop_series},
        )

        # a way for the model to get rid of excess energy
        # aka "feed-in"
        excess_sink = Sink(
            label="electricity_excess",
            inputs={electricity_bus: Flow(variable_costs=-feed_in_tariff)},
        )

        grid_source = Source(
            label="grid electricity",
            outputs={
                electricity_bus: Flow(
                    variable_costs=grid_electricity_price,  # 750,
                )
            },
        )

        battery_storage = GenericStorage(
            label="Batterystorage",
            inputs={electricity_bus: Flow()},
            outputs={electricity_bus: Flow()},
            loss_rate=0.00054,
            inflow_conversion_factor=0.954,
            outflow_conversion_factor=0.954,
            invest_relation_input_capacity=1,
            invest_relation_output_capacity=1,
            investment=Investment(ep_costs=battery_annual_costs),
            initial_storage_level=None,
        )

        buffer_storage = GenericStorage(
            label="Bufferstorage",
            inputs={heat_bus: Flow()},
            outputs={heat_bus: Flow()},
            loss_rate=0.00054,
            inflow_conversion_factor=0.954,
            outflow_conversion_factor=0.954,
            invest_relation_input_capacity=1,
            invest_relation_output_capacity=1,
            investment=Investment(ep_costs=heat_storage_annual_costs),
            initial_storage_level=None,
        )

        # add all defined components to the energy system model
        super().add(
            electricity_bus,
            excess_sink,
            electricity_demand_sink,
            pv_source,
            grid_source,
            battery_storage,
            heat_bus,
            heat_demand_sink,
            heat_pump_transformer,
            buffer_storage,
        )

        pass

    def model_name(self):
        val_dict = dict(
            pv_inv_cost=self.pv_inv_cost,
            batt_inv_cost=self.battery_inv_cost,
            sampling_freq=self.sampling_freq,
            grid_el_price=self.grid_electricity_price,
            feed_in_tariff=self.feed_in_tariff,
            heat_pump_inv_cost=self.heat_pump_inv_cost,
            heat_storage_inv_cost=self.heat_storage_inv_cost,
        )
        self.ts_data
        input_hash = hashlib.sha1(
            pd.util.hash_pandas_object(self.ts_data).values
        ).hexdigest()
        long_model_name = "_".join([".".join([k, str(v)]) for k, v in val_dict.items()])
        return long_model_name + f"_{input_hash}"


if __name__ == "__main__":
    debug = False
    if debug:
        print(sys.argv)
        # correct usage:
        # ['run_oemof_model.py', '1000', '300', '12', '30']
    if len(sys.argv) != 5:
        raise ValueError(
            """
        Invalid number of Arguments! Must be called as follows: household.py 1000 300 12 30.
        Example Values represent:
        pv_inv_cost =       1000    €/kWp
        battery_inv_cost =  300     €/kWh
        sampling_freq =     12      h
        grid_el_price =     30      ct/kWh
        """
        )

    pv_inv_cost = int(sys.argv[1])  # €/kWp
    battery_inv_cost = int(sys.argv[2])  # €/kWh
    sampling_freq = int(sys.argv[3])  # h
    grid_el_price = float(sys.argv[4])  # ct/kWh

    # read the buffer (what has been passed to sp.run(...,`input=pickle.dumps(df)`)
    # inputs_df = pickle.loads(sys.stdin.buffer.read())

    inputs_df = get_resampled_input_data(default_inputs_df, 12)

    esm = Household(
        inputs_df,
        pv_inv_cost,
        battery_inv_cost,
        grid_electricity_price=grid_el_price,
    )

    long_model_name = esm.model_name()
    results_dir = Path(f"results/{long_model_name}")
    if results_dir.joinpath("results.oemof").exists():
        # if the results directory exists, don't run optimisation, instead return the directory
        print(dict(results_dir=results_dir.as_posix()))
        exit(0)
    else:
        Path(results_dir).mkdir(parents=True, exist_ok=True)

    # put the esm into an optimisation model
    om = Model(esm)

    # solve the model
    om.solve(solver="glpk")

    # store the results
    esm.results = processing.results(om)
    results_filename = f"{results_dir}/results.oemof"
    esm.dump(".", results_filename)

    # print results dir to allow for reading of results (i.e. in different process)
    print(dict(results_dir=results_dir.as_posix()))
    pass
