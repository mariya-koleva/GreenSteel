# system-level imports
import os
import sys
import copy
import io

import pprint as pp

# computational science imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from hopp_wrapped_GSA import Capturing


def run(args):
    (
        num_turbines_in,
        electrolyzer_size_mw,
        solar_size_mw,
        storage_size_mw,
        storage_size_mwh,
    ) = args
    # wind_plant_size_mw = float(wind_plant_size_mw)
    num_turbines_in = int(num_turbines_in)
    electrolyzer_size_mw = float(electrolyzer_size_mw)
    solar_size_mw = float(solar_size_mw)
    storage_size_mw = float(storage_size_mw)
    storage_size_mwh = float(storage_size_mwh)

    # specifications
    electrolyzer_rating = electrolyzer_size_mw
    grid_connection = "off-grid"
    storage_type = "pressure_vessel"
    # plant_size = wind_plant_size_mw
    plant_design_scenario = 0
    use_profast = True
    incentive_option = 1
    verbose = False
    show_plots = False
    save_plots = False
    output_level = 2

    ### imports

    # yaml imports
    import yaml
    from yamlinclude import YamlIncludeConstructor
    from pathlib import Path

    PATH = Path(__file__).parent
    YamlIncludeConstructor.add_to_loader_class(
        loader_class=yaml.FullLoader, base_dir=PATH / "./input/floris/"
    )
    YamlIncludeConstructor.add_to_loader_class(
        loader_class=yaml.FullLoader, base_dir=PATH / "./input/turbines/"
    )

    # HOPP imports
    import hopp.eco.electrolyzer as he_elec
    import hopp.eco.finance as he_fin
    import hopp.eco.hopp_mgmt as he_hopp
    import hopp.eco.utilities as he_util
    import hopp.eco.hydrogen_mgmt as he_h2

    # packages needed for setting NREL API key
    from hopp.keys import set_developer_nrel_gov_key, get_developer_nrel_gov_key

    ################ Set API key
    global NREL_API_KEY
    NREL_API_KEY = os.getenv("NREL_API_KEY")
    set_developer_nrel_gov_key(
        NREL_API_KEY
    )  # Set this key manually here if you are not setting it using the .env or with an env var

    # for _dummyvariable in [None,]:
    with Capturing() as output:
        # load inputs as needed
        turbine_model = "osw_18MW"
        filename_orbit_config = os.path.realpath(
            os.path.join(".", "input", "plant", f"orbit-config-{turbine_model}.yaml")
        )
        filename_turbine_yaml = os.path.realpath(
            os.path.join(".", "input", "turbines", f"{turbine_model}.yaml")
        )
        filename_floris_config = os.path.realpath(
            os.path.join(".", "input", "floris", "floris_input_iea_18MW_osw.yaml")
        )
        plant_config, turbine_config, wind_resource, floris_config = he_util.get_inputs(
            filename_orbit_config,
            filename_turbine_yaml,
            filename_floris_config,
            verbose=verbose,
            show_plots=show_plots,
            save_plots=save_plots,
        )

        if electrolyzer_rating != None:
            plant_config["electrolyzer"]["rating"] = electrolyzer_rating

        if grid_connection != None:
            plant_config["project_parameters"]["grid_connection"] = grid_connection

        if storage_type != None:
            plant_config["h2_storage"]["type"] = storage_type

        if solar_size_mw > 0:
            plant_config["pv"]["flag"] = True
            plant_config["pv"]["system_capacity_kw"] = storage_size_mw * 1e3
            plant_config["pv"]["system_capacity_kwh"] = storage_size_mwh * 1e3

        if (storage_size_mw > 0) and (storage_size_mwh > 0):
            plant_config["battery"]["flag"] = True
            plant_config["battery"]["flag"] = True

        plant_config["plant"]["num_turbines"] = num_turbines_in
        plant_config["plant"]["capacity"] = plant_size = (
            num_turbines_in * turbine_config["turbine_rating"]
        )
        plant_config["plant"]["turbine_spacing"] = plant_config["plant"][
            "turbine_spacing"
        ] = 15

        design_scenario = plant_config["plant_design"][
            "scenario%s" % (plant_design_scenario)
        ]
        design_scenario["id"] = plant_design_scenario

        # run orbit for wind plant construction and other costs

        ## TODO get correct weather (wind, wave) inputs for ORBIT input (possibly via ERA5)
        orbit_project = he_fin.run_orbit(plant_config, weather=None, verbose=verbose)

        # setup HOPP model
        hopp_site, hopp_technologies, hopp_scenario, hopp_h2_args = he_hopp.setup_hopp(
            plant_config,
            turbine_config,
            wind_resource,
            orbit_project,
            floris_config,
            show_plots=show_plots,
            save_plots=save_plots,
        )

        # run HOPP model
        hopp_results = he_hopp.run_hopp(
            hopp_site, hopp_technologies, hopp_scenario, hopp_h2_args, verbose=verbose
        )

        # this portion of the system is inside a function so we can use a solver to determine the correct energy availability for h2 production
        def energy_internals(
            hopp_results=hopp_results,
            hopp_site=hopp_site,
            hopp_technologies=hopp_technologies,
            hopp_scenario=hopp_scenario,
            hopp_h2_args=hopp_h2_args,
            orbit_project=orbit_project,
            design_scenario=design_scenario,
            plant_config=plant_config,
            turbine_config=turbine_config,
            wind_resource=wind_resource,
            floris_config=floris_config,
            electrolyzer_size_mw=electrolyzer_rating,
            plant_size=plant_size,
            verbose=verbose,
            show_plots=show_plots,
            save_plots=save_plots,
            use_profast=use_profast,
            storage_type=storage_type,
            incentive_option=incentive_option,
            plant_design_scenario=plant_design_scenario,
            output_level=output_level,
            solver=True,
            power_for_peripherals_kw_in=0.0,
            breakdown=False,
        ):
            hopp_results_internal = dict(hopp_results)

            # set energy input profile
            ### subtract peripheral power from supply to get what is left for electrolyzer
            remaining_power_profile_in = np.zeros_like(
                hopp_results["combined_pv_wind_power_production_hopp"]
            )

            high_count = sum(
                np.asarray(hopp_results["combined_pv_wind_power_production_hopp"])
                >= power_for_peripherals_kw_in
            )
            total_peripheral_energy = power_for_peripherals_kw_in * 365 * 24
            distributed_peripheral_power = total_peripheral_energy / high_count
            for i in range(len(hopp_results["combined_pv_wind_power_production_hopp"])):
                r = (
                    hopp_results["combined_pv_wind_power_production_hopp"][i]
                    - distributed_peripheral_power
                )
                if r > 0:
                    remaining_power_profile_in[i] = r

            hopp_results_internal["combined_pv_wind_power_production_hopp"] = tuple(
                remaining_power_profile_in
            )

            # run electrolyzer physics model
            electrolyzer_physics_results = he_elec.run_electrolyzer_physics(
                hopp_results_internal,
                hopp_scenario,
                hopp_h2_args,
                plant_config,
                wind_resource,
                design_scenario,
                show_plots=show_plots,
                save_plots=save_plots,
                verbose=verbose,
            )

            # run electrolyzer cost model
            electrolyzer_cost_results = he_elec.run_electrolyzer_cost(
                electrolyzer_physics_results,
                hopp_scenario,
                plant_config,
                design_scenario,
                verbose=verbose,
            )

            desal_results = he_elec.run_desal(
                plant_config, electrolyzer_physics_results, design_scenario, verbose
            )

            # run array system model
            h2_pipe_array_results = he_h2.run_h2_pipe_array(
                plant_config,
                orbit_project,
                electrolyzer_physics_results,
                design_scenario,
                verbose,
            )

            # compressor #TODO size correctly
            (
                h2_transport_compressor,
                h2_transport_compressor_results,
            ) = he_h2.run_h2_transport_compressor(
                plant_config,
                electrolyzer_physics_results,
                design_scenario,
                verbose=verbose,
            )

            # transport pipeline
            h2_transport_pipe_results = he_h2.run_h2_transport_pipe(
                plant_config,
                electrolyzer_physics_results,
                design_scenario,
                verbose=verbose,
            )

            # pressure vessel storage
            pipe_storage, h2_storage_results = he_h2.run_h2_storage(
                plant_config,
                turbine_config,
                electrolyzer_physics_results,
                design_scenario,
                verbose=verbose,
            )

            total_energy_available = np.sum(
                hopp_results["combined_pv_wind_power_production_hopp"]
            )

            ### get all energy non-electrolyzer usage in kw
            desal_power_kw = desal_results["power_for_desal_kw"]

            h2_transport_compressor_power_kw = h2_transport_compressor_results[
                "compressor_power"
            ]  # kW

            h2_storage_energy_kwh = h2_storage_results["storage_energy"]
            h2_storage_power_kw = h2_storage_energy_kwh * (1.0 / (365 * 24))

            # if transport is not HVDC and h2 storage is on shore, then power the storage from the grid
            if (design_scenario["transportation"] == "pipeline") and (
                design_scenario["h2_storage_location"] == "onshore"
            ):
                total_accessory_power_renewable_kw = (
                    desal_power_kw + h2_transport_compressor_power_kw
                )
                total_accessory_power_grid_kw = h2_storage_power_kw
            else:
                total_accessory_power_renewable_kw = (
                    desal_power_kw
                    + h2_transport_compressor_power_kw
                    + h2_storage_power_kw
                )
                total_accessory_power_grid_kw = 0.0

            ### subtract peripheral power from supply to get what is left for electrolyzer and also get grid power
            remaining_power_profile = np.zeros_like(
                hopp_results["combined_pv_wind_power_production_hopp"]
            )
            grid_power_profile = np.zeros_like(
                hopp_results["combined_pv_wind_power_production_hopp"]
            )
            for i in range(len(hopp_results["combined_pv_wind_power_production_hopp"])):
                r = (
                    hopp_results["combined_pv_wind_power_production_hopp"][i]
                    - total_accessory_power_renewable_kw
                )
                grid_power_profile[i] = total_accessory_power_grid_kw
                if r > 0:
                    remaining_power_profile[i] = r

            if verbose and not solver:
                print("\nEnergy/Power Results:")
                print("Supply (MWh): ", total_energy_available)
                print("Desal (kW): ", desal_power_kw)
                print("Transport compressor (kW): ", h2_transport_compressor_power_kw)
                print(
                    "Storage compression, refrigeration, etc (kW): ",
                    h2_storage_power_kw,
                )

            if (show_plots or save_plots) and not solver:
                fig, ax = plt.subplots(1)
                plt.plot(
                    np.asarray(hopp_results["combined_pv_wind_power_production_hopp"])
                    * 1e-6,
                    label="Total Energy Available",
                )
                plt.plot(
                    remaining_power_profile * 1e-6,
                    label="Energy Available for Electrolysis",
                )
                plt.xlabel("Hour")
                plt.ylabel("Power (GW)")
                plt.tight_layout()
                if save_plots:
                    savepath = "figures/power_series/"
                    if not os.path.exists(savepath):
                        os.makedirs(savepath)
                    plt.savefig(
                        savepath + "power_%i.png" % (design_scenario["id"]),
                        transparent=True,
                    )
                if show_plots:
                    plt.show()
            if solver:
                if breakdown:
                    return (
                        total_accessory_power_renewable_kw,
                        total_accessory_power_grid_kw,
                        desal_power_kw,
                        h2_transport_compressor_power_kw,
                        h2_storage_power_kw,
                    )
                else:
                    return total_accessory_power_renewable_kw
            else:
                return (
                    electrolyzer_physics_results,
                    electrolyzer_cost_results,
                    desal_results,
                    h2_pipe_array_results,
                    h2_transport_compressor,
                    h2_transport_compressor_results,
                    h2_transport_pipe_results,
                    pipe_storage,
                    h2_storage_results,
                    total_accessory_power_renewable_kw,
                    total_accessory_power_grid_kw,
                )

        # define function to provide to the brent solver
        def energy_residual_function(power_for_peripherals_kw_in):
            # get results for current design
            power_for_peripherals_kw_out = energy_internals(
                power_for_peripherals_kw_in=power_for_peripherals_kw_in,
                solver=True,
                verbose=False,
            )

            # collect residual
            power_residual = power_for_peripherals_kw_out - power_for_peripherals_kw_in

            return power_residual

        def simple_solver(initial_guess=0.0):
            # get results for current design
            (
                total_accessory_power_renewable_kw,
                total_accessory_power_grid_kw,
                desal_power_kw,
                h2_transport_compressor_power_kw,
                h2_storage_power_kw,
            ) = energy_internals(
                power_for_peripherals_kw_in=initial_guess,
                solver=True,
                verbose=False,
                breakdown=True,
            )

            return (
                total_accessory_power_renewable_kw,
                total_accessory_power_grid_kw,
                desal_power_kw,
                h2_transport_compressor_power_kw,
                h2_storage_power_kw,
            )

        #################### solving for energy needed for non-electrolyzer components ####################################
        # this approach either exactly over over-estimates the energy needed for non-electrolyzer components
        solver_results = simple_solver(0)
        solver_result = solver_results[0]

        # this approach exactly sizes the energy needed for the non-electrolyzer components (according to the current models anyway)
        # solver_result = optimize.brentq(energy_residual_function, -10, 20000, rtol=1E-5)
        # OptimizeResult = optimize.root(energy_residual_function, 11E3, tol=1)
        # solver_result = OptimizeResult.x
        ##################################################################################################################

        # get results for final design
        (
            electrolyzer_physics_results,
            electrolyzer_cost_results,
            desal_results,
            h2_pipe_array_results,
            h2_transport_compressor,
            h2_transport_compressor_results,
            h2_transport_pipe_results,
            pipe_storage,
            h2_storage_results,
            total_accessory_power_renewable_kw,
            total_accessory_power_grid_kw,
        ) = energy_internals(solver=False, power_for_peripherals_kw_in=solver_result)

        ## end solver loop here
        platform_results = he_h2.run_equipment_platform(
            plant_config,
            design_scenario,
            electrolyzer_physics_results,
            h2_storage_results,
            desal_results,
            verbose=verbose,
        )

        ################# OSW intermediate calculations" aka final financial calculations
        # does LCOE even make sense if we are only selling the H2? I think in this case LCOE should not be used, rather LCOH should be used. Or, we could use LCOE based on the electricity actually used for h2
        # I think LCOE is just being used to estimate the cost of the electricity used, but in this case we should just use the cost of the electricity generating plant since we are not selling to the grid. We
        # could build in a grid connection later such that we use LCOE for any purchased electricity and sell any excess electricity after H2 production
        # actually, I think this is what OSW is doing for LCOH

        # TODO double check full-system CAPEX
        capex, capex_breakdown = he_fin.run_capex(
            hopp_results,
            orbit_project,
            electrolyzer_cost_results,
            h2_pipe_array_results,
            h2_transport_compressor_results,
            h2_transport_pipe_results,
            h2_storage_results,
            plant_config,
            design_scenario,
            desal_results,
            platform_results,
            verbose=verbose,
        )

        # TODO double check full-system OPEX
        opex_annual, opex_breakdown_annual = he_fin.run_opex(
            hopp_results,
            orbit_project,
            electrolyzer_cost_results,
            h2_pipe_array_results,
            h2_transport_compressor_results,
            h2_transport_pipe_results,
            h2_storage_results,
            plant_config,
            desal_results,
            platform_results,
            verbose=verbose,
            total_export_system_cost=capex_breakdown["electrical_export_system"],
        )

        if use_profast:
            lcoe, pf_lcoe = he_fin.run_profast_lcoe(
                plant_config,
                orbit_project,
                capex_breakdown,
                opex_breakdown_annual,
                hopp_results,
                design_scenario,
                verbose=verbose,
                show_plots=show_plots,
                save_plots=save_plots,
            )
            lcoh_grid_only, pf_grid_only = he_fin.run_profast_grid_only(
                plant_config,
                orbit_project,
                electrolyzer_physics_results,
                capex_breakdown,
                opex_breakdown_annual,
                hopp_results,
                design_scenario,
                total_accessory_power_renewable_kw,
                total_accessory_power_grid_kw,
                verbose=verbose,
                show_plots=show_plots,
                save_plots=save_plots,
            )
            lcoh, pf_lcoh = he_fin.run_profast_full_plant_model(
                plant_config,
                orbit_project,
                electrolyzer_physics_results,
                capex_breakdown,
                opex_breakdown_annual,
                hopp_results,
                incentive_option,
                design_scenario,
                total_accessory_power_renewable_kw,
                total_accessory_power_grid_kw,
                verbose=verbose,
                show_plots=show_plots,
                save_plots=save_plots,
            )

        ################# end OSW intermediate calculations
        power_breakdown = he_util.post_process_simulation(
            lcoe,
            lcoh,
            pf_lcoh,
            pf_lcoe,
            hopp_results,
            electrolyzer_physics_results,
            plant_config,
            h2_storage_results,
            capex_breakdown,
            opex_breakdown_annual,
            orbit_project,
            platform_results,
            desal_results,
            design_scenario,
            plant_design_scenario,
            incentive_option,
            solver_results=solver_results,
            show_plots=show_plots,
            save_plots=save_plots,
        )  # , lcoe, lcoh, lcoh_with_grid, lcoh_grid_only)

    lcoe *= 1000.0  # convert from kWh to MWh

    # return
    if output_level == 0:
        return 0
    elif output_level == 1:
        return lcoh
    elif output_level == 2:
        return (
            lcoh,
            lcoe,
            capex_breakdown,
            opex_breakdown_annual,
            pf_lcoh,
            electrolyzer_physics_results,
        )
    elif output_level == 3:
        return (
            lcoh,
            lcoe,
            capex_breakdown,
            opex_breakdown_annual,
            pf_lcoh,
            electrolyzer_physics_results,
            pf_lcoe,
            power_breakdown,
        )


if __name__ == "__main__":
    plant_capacity = 180
    electrolyzer_rating = 180

    lcoh, lcoe, _, _, _, _ = run((plant_capacity, electrolyzer_rating))

    print()
    print(f"lcoh: {lcoh}", f"lcoe: {lcoe}")

    #
