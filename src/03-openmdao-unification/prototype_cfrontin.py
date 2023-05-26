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
        # self.add_input("wind_size_mw", val=0.0)
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

    # def setup(self):
    #     # add any additional inputs or outputs
    #     pass

    def compute(self, inputs, outputs):
        """compute the outputs given the outputs for this branch"""

        # transfer from openmdao inputs to the input args for the run script
        solar_size_mw = inputs["solar_size_mw"]
        storage_size_mw = inputs["storage_size_mw"]
        storage_size_mwh = inputs["storage_size_mwh"]

        args = (solar_size_mw, storage_size_mw, storage_size_mwh)

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
        system_hopp.set_input_defaults("solar_size_mw", 1000.0)
        system_hopp.set_input_defaults("storage_size_mw", 1000.0)
        system_hopp.set_input_defaults("storage_size_mwh", 1000.0)

        # block solver: shouldn't be needed for much?
        system_hopp.nonlinear_solver = om.NonlinearBlockGS()

        # add objective and constraint modules?
        system_hopp.add_subsystem(
            "obj_cmp", om.ExecComp("obj=lcoe", lcoe=0.0), promotes=["*"]
        )


### ############################
### SANDBOX CODE BELOW THIS LINE
### ############################


def main():
    just_plots = True
    if not just_plots:
        prob = om.Problem()
        model = prob.model

        model.add_subsystem(
            "hopp",
            UnifiedHOPP(),
            promotes_inputs=[
                "solar_size_mw",
                "storage_size_mw",
                "storage_size_mwh",
            ],
            promotes_outputs=[
                "lcoh",
                "lcoe",
                "obj",
            ],
        )
        # model.add_design_var("solar_size_mw", lower=0.0, upper=2000.0)
        model.add_design_var("storage_size_mw", lower=500.0, upper=2000.0)
        model.add_design_var("storage_size_mwh", lower=500.0, upper=2000.0)
        # model.add_objective("obj", )
        model.add_objective("lcoe")
        model.add_objective("lcoh")

        prob.model.approx_totals()  # set up approximation of differentials

        prob.driver = om.DOEDriver(om.FullFactorialGenerator(levels=7))
        recorder = om.SqliteRecorder("cases.sql")
        prob.driver.add_recorder(recorder)
        prob.model.add_recorder(recorder)
        # prob.driver.options["optimizer"] = "SNOPT"

        prob.setup()
        prob.set_solver_print(level=1)

        prob.set_val("solar_size_mw", 1000.0)
        prob.set_val("storage_size_mw", 1000.0)
        prob.set_val("storage_size_mwh", 1000.0)

        prob.run_model()
        print(f"lcoh: {prob['lcoh']}")
        print(f"lcoe: {prob['lcoe']}")

        prob.run_driver()
        # print(f"minimum found at:\n\tsolar_size_mw: {prob.get_val('solar_size_mw')}")
        prob.cleanup()

    cr = om.CaseReader("cases.sql")
    cases = cr.list_cases("driver")

    values = []
    for case in cases:
        outputs = cr.get_case(case).outputs
        values.append(
            [
                float(x)
                for x in [
                    outputs["storage_size_mw"],
                    outputs["storage_size_mwh"],
                    outputs["lcoe"],
                    outputs["lcoh"],
                ]
            ]
        )
    print(
        "\n".join(
            [
                f"storage_power: {xyf[0]:5.2f}, "
                + f"storage_capacity: {xyf[1]:5.2f}; "
                + f"lcoe: {xyf[2]:5.2f}, lcoh: {xyf[3]:5.2f}"
                for xyf in values
            ]
        )
    )

    df = pd.DataFrame(
        values, columns=["storage_size_mw", "storage_size_mwh", "lcoe", "lcoh"]
    )
    df.sort_values("storage_size_mw", inplace=True)
    print(df)
    # fig, ax = plt.subplots()
    # ax.plot(df.storage_size_mw, df.lcoe, label="lcoe")
    # axb = ax.twinx()
    # axb.plot([], [], label="__")
    # axb.plot(df.storage_size_mw, df.lcoh, label="lcoh")
    # ax.set_xlabel("storage size (MW)")
    # ax.set_ylabel("lcoe (-)")
    # axb.set_ylabel("lcoh (-)")
    # fig.legend()
    fig, ax = plt.subplots()
    ct0 = ax.tricontourf(df.storage_size_mw, df.storage_size_mwh, df.lcoe, label="lcoe")
    ct1 = ax.tricontour(
        df.storage_size_mw, df.storage_size_mwh, df.lcoh, colors="k", label="lcoh"
    )
    ax.clabel(ct1)
    ax.set_xlabel("storage power (MW)")
    ax.set_ylabel("storage capacity (MWh)")
    fig.colorbar(ct0)
    ax.legend()
    plt.show()


if __name__ == "__main__":
    main()

#
