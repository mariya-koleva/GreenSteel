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


class HOPP_template(om.ExplicitComponent, abc.ABC):
    """
    an abstract base component that should unify io across branches

    input variables:
      - `wind_size_mw`: the target size of the wind plant in MW
      - others, dependent on the branch being used

    output variables:
      - `lcoh`: levelized cost of hydrogen ($/kg?)
      - `lcoe`: levelized cost of energy ($/kW?)
      - others, dependent on the branch being used
    """

    def setup(self):
        """setup the openmdao instance: declare variables"""
        # add inputs
        self.add_input("wind_size_mw", val=0.0)

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

    # def setup(self):
    #     # add any additional inputs or outputs
    #     pass

    def compute(self, inputs, outputs):
        """compute the outputs given the outputs for this branch"""

        # transfer from openmdao inputs to the input args for the run script
        wind_size_mw = inputs["wind_size_mw"]
        electrolyzer_size_mw = 1000.0
        user_wind_capex_multiplier = 1.0
        user_electrolyzer_capex_multiplier = 1.0

        args = (
            wind_size_mw,
            electrolyzer_size_mw,
            user_wind_capex_multiplier,
            user_electrolyzer_capex_multiplier,
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
        # add any additional inputs or outputs
        raise NotImplementedError("@jthomas2 should implement this! -cfrontin")

    def compute(self, inputs, outputs):
        # actually do the computation here for this branch
        raise NotImplementedError("@jthomas2 should implement this! -cfrontin")


class UnifiedHOPP(om.Group):
    """
    a master group, with which we can run either `jthomas2`'s `offshore` branch
    or `cfrontin`'s `green_steel_ammonia` branch
    """

    def setup(self, use_GSA=True):
        # put together the final overarching system
        system_hopp = self.add_subsystem("system", om.Group(), promotes=["*"])
        if use_GSA:
            system_hopp.add_subsystem(
                "HOPP_case", HOPP_GSA(), promotes_inputs=["*"], promotes_outputs=["*"]
            )
        else:
            raise NotImplementedError("add the offshore branch handler! -cfrontin")

        # set the default solver
        system_hopp.set_input_defaults("wind_size_mw", 1000.0)

        # block solver: shouldn't be needed for much?
        system_hopp.nonlinear_solver = om.NonlinearBlockGS()

        # add objective and constraint modules?
        system_hopp.add_subsystem(
            "obj_cmp", om.ExecComp("obj=-lcoe", lcoe=0.0), promotes=["lcoe", "obj"]
        )


### ############################
### SANDBOX CODE BELOW THIS LINE
### ############################


def main():
    prob = om.Problem()
    model = prob.model

    model.add_subsystem(
        "hopp",
        UnifiedHOPP(),
        promotes_inputs=[
            "wind_size_mw",
        ],
        promotes_outputs=[
            "lcoh",
            "lcoe",
        ],
    )
    model.add_design_var("wind_size_mw", lower=500., upper=2000.)
    model.add_objective("lcoh")
    model.add_objective("lcoe")

    prob.setup()

    prob.set_val("wind_size_mw", 1000.0)

    prob.run_model()
    print(f"lcoh: {prob['lcoh']}")
    print(f"lcoe: {prob['lcoe']}")


if __name__ == "__main__":
    main()

#
