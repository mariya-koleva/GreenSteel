### imports

# system-level imports
import os
import sys
import io
import warnings
import copy
import abc  # abstract base classes

# io imports
from dotenv import load_dotenv

# computational science imports
import numpy as np
import numpy_financial as npf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import multiprocessing
import openmdao.api as om

# from green_steel_sweeps.sandbox import MonolithicHopp

from hopp_wrapped_GSA import run as run_GSA
from hopp_wrapped_offshore import run as run_offshore


class HOPP_template(om.ExplicitComponent, abc.ABC):
    """
    an abstract base component that should unify io across branches

    input variables:
      ### - `wind_size_mw`: the target size of the wind plant in MW ### turned off
      - `solar_size_mw`: the target size of the solar plant in MW
      - `storage_size_mw`: the target power of the storage system in MW
      - `storage_size_mwh`: the target capacity of the storage system in MWh
      - others, dependent on the branch being used

    output variables:
      - `lcoh`: levelized cost of hydrogen ($/kg?)
      - `lcoe`: levelized cost of energy ($/kW?)
      - others, dependent on the branch being used
    """

    def setup(self):
        """setup the openmdao instance: declare variables"""
        # add inputs
        self.add_discrete_input("n_turbines", val=10)
        self.add_input("electrolyzer_size_mw", val=1000.0)
        self.add_input("solar_size_mw", val=0.0)
        self.add_input("storage_size_mw", val=0.0)
        self.add_input("storage_size_mwh", val=0.0)

        # add outputs
        self.add_output("lcoh", val=0.0)
        self.add_output("lcoe", val=0.0)

    def setup_partials(self):
        """setup the openmdao instance: declare partial derivatives"""
        self.declare_partials("*", "*", method="fd")

    @abc.abstractmethod
    def compute(self, inputs, outputs):
        """setup the openmdao instance: run the subsystem kernel"""
        pass


class HOPP_GSA(HOPP_template):
    """
    a template for running a `green_steel_ammonia` instance
    """

    def setup(self):
        super().setup()  # call the base class setup

        # add any additional inputs or outputs
        # self.add_input("...", val=0.0)

    def compute(self, inputs, outputs, discrete_inputs, discrete_outputs=None):
        """compute the outputs given the inputs for this branch"""

        # transfer from openmdao inputs to the input args for the run script
        n_turbines = discrete_inputs["n_turbines"]
        electrolyzer_size_mw = inputs["electrolyzer_size_mw"]
        solar_size_mw = inputs["solar_size_mw"]
        storage_size_mw = inputs["storage_size_mw"]
        storage_size_mwh = inputs["storage_size_mwh"]

        args = (
            n_turbines,
            electrolyzer_size_mw,
            solar_size_mw,
            storage_size_mw,
            storage_size_mwh,
        )

        # pass through to run script and run!
        ret_vals = run_GSA(args)

        # for now, dump just levelized costs from the returns
        lcoh, lcoe, _, _ = ret_vals

        # pipe to openmdao
        outputs["lcoh"] = lcoh
        outputs["lcoe"] = lcoe


class HOPP_offshore(HOPP_template):
    """
    a template for running a `offshore` instance
    """

    def setup(self):
        super().setup()  # call the base class setup

        # add any additional inputs or outputs
        # self.add_discrete_input("n_turbines", val=1)

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """compute the outputs given the inputs for this branch"""

        # transfer from openmdao inputs to the input args for the run script
        n_turbines = discrete_inputs["n_turbines"]
        electrolyzer_size_mw = inputs["electrolyzer_size_mw"]
        solar_size_mw = inputs["solar_size_mw"]
        storage_size_mw = inputs["storage_size_mw"]
        storage_size_mwh = inputs["storage_size_mwh"]

        args = (
            n_turbines,
            electrolyzer_size_mw,
            solar_size_mw,
            storage_size_mw,
            storage_size_mwh,
        )

        # pass through to the run script and run!
        ret_vals = run_offshore(args)

        # for now dump just levelized costs from the returns
        lcoh, lcoe = ret_vals[0:2]

        # pipe to openmdao
        outputs["lcoh"] = lcoh
        outputs["lcoe"] = lcoe


class UnifiedHOPP(om.Group):
    """
    a master group, with which we can run either `jthomas2`'s `offshore` branch
    or `cfrontin`'s `green_steel_ammonia` branch
    """

    def initialize(self):
        self.options.declare("use_GSA", types=bool)

    def setup(self):
        # put together the final overarching system
        system_hopp = self.add_subsystem("system", om.Group(), promotes=["*"])
        if self.options["use_GSA"]:
            system_hopp.add_subsystem(
                "HOPP_case", HOPP_GSA(), promotes_inputs=["*"], promotes_outputs=["*"]
            )
        else:
            system_hopp.add_subsystem(
                "HOPP_case",
                HOPP_offshore(),
                promotes_inputs=["*"],
                promotes_outputs=["*"],
            )
            # raise NotImplementedError("add the offshore branch handler! -cfrontin")

        # set the default solver
        if self.options["use_GSA"]:
            system_hopp.set_input_defaults("solar_size_mw", 1000.0)
            system_hopp.set_input_defaults("storage_size_mw", 1000.0)
            system_hopp.set_input_defaults("storage_size_mwh", 1000.0)
        else:
            system_hopp.set_input_defaults("n_turbines", 54)

        # block solver: shouldn't be needed for much?
        system_hopp.nonlinear_solver = om.NonlinearBlockGS()


### ############################
### SANDBOX CODE BELOW THIS LINE
### ############################


def main():
    prob = om.Problem()
    model = prob.model

    use_GSA = True  # variable to use green-steel-ammonia or offshore-h2

    model.add_subsystem(
        "hopp",
        UnifiedHOPP(use_GSA=use_GSA),
        promotes_inputs=["*"],
        promotes_outputs=["*"],
    )

    if use_GSA:
        experiments = [
            # {  # green-steel-ammonia: n_turbines vs. (lcoe, lcoh)
            #     "type": "sensitivity",
            #     "design_variables": [
            #         {
            #             "name": "n_turbines",
            #             "query": np.arange(75, 125 + 1, 5),
            #             "print": "number of turbines (-)",
            #             "match_electrolyzer": True,
            #             "turbine_rating": 6,  # MW
            #         },
            #     ],
            #     "objectives": [
            #         {"name": "lcoe", "print": "LCOE (\$/MWh)"},
            #         {"name": "lcoh", "print": "LCOH (\$/kg)"},
            #     ],
            # },
            {  # green-steel-ammonia: electrolyzer_size_mw vs. (lcoe, lcoh)
                "type": "sensitivity",
                "design_variables": [
                    {
                        "name": "electrolyzer_size_mw",
                        "query": np.arange(10.0, 100.0, 10.0),
                        "print": "electrolyzer size (MW)",
                    },
                ],
                "objectives": [
                    {"name": "lcoe", "print": "LCOE (\$/MWh)"},
                    {"name": "lcoh", "print": "LCOH (\$/kg)"},
                ],
            },
            # {  # green-steel-ammonia: solar_size_mw vs. (lcoe, lcoh)
            #     "type": "sensitivity",
            #     "design_variables": [
            #         {
            #             "name": "solar_size_mw",
            #             "query": np.arange(0.0, 1501.0, 100.0),
            #             "print": "solar size (MW)",
            #         },
            #     ],
            #     "objectives": [
            #         {"name": "lcoe", "print": "LCOE (\$/MWh)"},
            #         {"name": "lcoh", "print": "LCOH (\$/kg)"},
            #     ],
            # },
            # {  # green-steel-ammonia: storage_size_mw vs. (lcoe, lcoh)
            #     "type": "sensitivity",
            #     "design_variables": [
            #         {
            #             "name": "storage_size_mw",
            #             "query": np.arange(100.0, 1501.0, 100.0),
            #             "print": "storage power (MW)",
            #         },
            #     ],
            #     "objectives": [
            #         {"name": "lcoe", "print": "LCOE (\$/MWh)"},
            #         {"name": "lcoh", "print": "LCOH (\$/kg)"},
            #     ],
            # },
            # {  # green-steel-ammonia: storage_size_mwh vs. (lcoe, lcoh)
            #     "type": "sensitivity",
            #     "design_variables": [
            #         {
            #             "name": "storage_size_mwh",
            #             "query": np.arange(100.0, 1501.0, 100.0),
            #             "print": "storage capacity (MWh)",
            #         },
            #     ],
            #     "objectives": [
            #         {"name": "lcoe", "print": "LCOE (\$/MWh)"},
            #         {"name": "lcoh", "print": "LCOH (\$/kg)"},
            #     ],
            # },
        ]
    else:
        experiments = [
            {  # offshore_h2: n_turbines vs. (lcoe, lcoh)
                "type": "sensitivity",
                "design_variables": [
                    {
                        "name": "n_turbines",
                        "query": np.arange(24, 31 + 1),
                        "print": "number of turbines (-)",
                        "match_electrolyzer": True,
                        "turbine_rating": 18,  # MW
                    },
                ],
                "objectives": [
                    {"name": "lcoe", "print": "LCOE (\$/MWh)"},
                    {"name": "lcoh", "print": "LCOH (\$/kg)"},
                ],
            },
            {  # offshore_h2: electrolyzer_size_mw vs. (lcoe, lcoh)
                "type": "sensitivity",
                "design_variables": [
                    {
                        "name": "electrolyzer_size_mw",
                        "query": np.arange(1000.0, 2100.0, 100.0),
                        "print": "electrolyzer size (MW)",
                    },
                ],
                "objectives": [
                    {"name": "lcoe", "print": "LCOE (\$/MWh)"},
                    {"name": "lcoh", "print": "LCOH (\$/kg)"},
                ],
            },
            {  # offshore_h2: solar_size_mw vs. (lcoe, lcoh)
                "type": "sensitivity",
                "design_variables": [
                    {
                        "name": "solar_size_mw",
                        "query": np.arange(0.0, 2500.0 * 1.001, 250.0),
                        "print": "solar size (MW)",
                    },
                ],
                "objectives": [
                    {"name": "lcoe", "print": "LCOE (\$/MWh)"},
                    {"name": "lcoh", "print": "LCOH (\$/kg)"},
                ],
            },
            # {  # offshore_h2: storage_size_mw vs. (lcoe, lcoh)
            #     "type": "sensitivity",
            #     "design_variables": [
            #         {
            #             "name": "storage_size_mw",
            #             "query": np.arange(0.0, 100.0*1.001, 10.0),
            #             "print": "storage power (MW)",
            #         },
            #     ],
            #     "objectives": [
            #         {"name": "lcoe", "print": "LCOE (\$/MWh)"},
            #         {"name": "lcoh", "print": "LCOH (\$/kg)"},
            #     ],
            # },
            # {  # offshore_h2: storage_size_mwh vs. (lcoe, lcoh)
            #     "type": "sensitivity",
            #     "design_variables": [
            #         {
            #             "name": "storage_size_mwh",
            #             "query": np.arange(0.0, 100.0*1.001, 10.0),
            #             "print": "storage capacity (MWh)",
            #         },
            #     ],
            #     "objectives": [
            #         {"name": "lcoe", "print": "LCOE (\$/MWh)"},
            #         {"name": "lcoh", "print": "LCOH (\$/kg)"},
            #     ],
            # },
        ]

    if use_GSA:
        default_values = {
            "n_turbines": 30,
            "electrolyzer_size_mw": 1000.0,
            "solar_size_mw": 0.0,
            "storage_size_mw": 100.0,
            "storage_size_mwh": 100.0,
        }
    else:
        default_values = {
            "n_turbines": 27,
            "electrolyzer_size_mw": 1000.0,
        }

    for exp in experiments:
        prob.setup()

        for var, def_val in default_values.items():
            prob.set_val(var, def_val)

        if exp["type"] != "sensitivity":
            raise NotImplementedError(
                "only set up for sensitivity studies rn. -cfrontin"
            )

        for dv in exp["design_variables"]:
            data_x = dv["query"]
            name_x = dv["name"]
            printname_x = dv["print"]

            data_y = {
                obj["name"]: np.zeros_like(data_x, dtype=float)
                for obj in exp["objectives"]
            }

            for idx, nq in enumerate(data_x):
                prob.set_val(name_x, nq)
                if dv.get("match_electrolyzer"):
                    turbine_rating = dv[
                        "turbine_rating"
                    ]  # if this isn't right you'll get an error
                    prob.set_val("electrolyzer_size_mw", turbine_rating * nq)
                prob.run_model()

                for obj in exp["objectives"]:
                    data_y[obj["name"]][idx] = float(prob[obj["name"]])

                prob.cleanup()

            fig, axes = plt.subplots(len(exp["objectives"]), 1, sharex=True)
            for idx_obj, obj in enumerate(exp["objectives"]):
                axes[idx_obj].plot(data_x, data_y[obj["name"]], ".-")
                if idx_obj == (len(axes) - 1):
                    axes[idx_obj].set_xlabel(dv["print"])
                axes[idx_obj].set_ylabel(obj["print"])
            fig.tight_layout()
            fig.savefig(
                f"figures/{'GS' if use_GSA else 'oH2'}_{exp['type']}_{name_x}_vs_{'_'.join([x['name'] for x in exp['objectives']])}.png"
            )
    plt.show()


if __name__ == "__main__":
    main()

#
