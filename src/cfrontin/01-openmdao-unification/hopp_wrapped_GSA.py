### imports

# system-level imports
import os
import sys
import copy
import io
from pprint import pprint

# IO imports
from dotenv import load_dotenv

# computational science imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# context manager for trapping stdout
class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


# overall run script
def run(args):
    (
        num_turbines_in,
        electrolyzer_size_mw,
        solar_size_mw,
        storage_size_mw,
        storage_size_mwh,
    ) = args
    num_turbines_in = int(num_turbines_in)
    electrolyzer_size_mw = float(electrolyzer_size_mw)
    solar_size_mw = float(solar_size_mw)
    storage_size_mw = float(storage_size_mw)
    storage_size_mwh = float(storage_size_mwh)

    ### imports

    # energy modeling imports (clean)
    from hybrid.sites import SiteInfo
    from hybrid.sites import flatirons_site as sample_site
    from hybrid.keys import set_developer_nrel_gov_key

    import hopp_tools_steel
    from hopp_tools_steel import hoppDict
    import inputs_py
    import run_profast_for_hydrogen
    import distributed_pipe_cost_analysis

    # energy modeling imports (dirty)
    source_root = os.path.split(hopp_tools_steel.__file__)[0]
    sys.path.append(source_root)
    from examples.H2_Analysis.hopp_for_h2 import hopp_for_h2
    from examples.H2_Analysis.run_h2a import run_h2a as run_h2a
    from examples.H2_Analysis.simple_cash_annuals import simple_cash_annuals

    sys.path.remove(source_root)

    # setup API key
    load_dotenv()
    NREL_API_KEY = os.getenv("NREL_API_KEY")
    set_developer_nrel_gov_key("NREL_API_KEY")

    # capture stdout
    for _dummy_ in [None,]:
    # with Capturing() as output:
        ### settings

        ## analysis switches
        floris = True
        run_RODeO_selector = False  # turn False to run ProFAST for H2 LCOH
        grid_price_scenario = (
            "retail-flat"  # ['wholesale', 'retail-peaks', 'retail-flat']
        )
        direct_coupling = True  # distributed scale power electronic direct coupling
        electrolyzer_cost_case = "Low"  # electrolzyer cost case: ['Mid', 'Low']
        electrolyzer_degradation_penalty = (
            True  # to run with electrolyzer degradation or not
        )
        pem_control_type = (
            "basic"  # determine if PEM stack operation is optimized or not
        )
        # ^- use 'optimize' for Sanjana's controller; 'basic' to not optimize
        run_reopt_flag = False
        custom_powercurve = True  # flag applicable w/ PySAM WindPower (not FLORIS)
        storage_used = True
        battery_can_grid_charge = False
        grid_connected_hopp = False
        user_defined_electrolyzer_EOL_eff_drop = True
        user_defined_electrolyzer_BOL_kWh_per_kg = False
        battery_for_minimum_electrolyzer_op = True  # if true, then dispatch battery (if on) to supply minimum power for operation to PEM, otherwise use it for rated PEM power
        if electrolyzer_degradation_penalty:
            user_defined_stack_replacement_time = False  # if true then not dependent on pem performance and set to constant
        else:
            user_defined_stack_replacement_time = True
        use_optimistic_pem_efficiency = False
        h2_model = "Simple"  # wind costs input from ORBIT analysis ["Simple", "H2A"]
        # ^- simple: basic cost model based on H2a and HFTO program record for PEM electrolysis
        forced_sizes = True
        force_electrolyzer_cost = False

        ## plotting and output switches
        plot_power_production = False
        plot_battery = False
        plot_grid = False
        plot_h2 = False
        plot_desal = False
        plot_wind = False
        plot_hvdcpipe = False
        plot_hvdcpipe_lcoh = False
        save_hybrid_plant_yaml = (
            True  # hybrid_plant requires special processing of the SAM objects
        )
        save_model_input_yaml = True  # saves the inputs for each model/major function
        save_model_output_yaml = True  # saves the outputs for each model/major function
        save_param_sweep_general_info = True
        save_param_sweep_best_case = True

        ## constants
        electrolyzer_degradation_power_increase = (
            0.13  # deg penalties for capital costs
        )
        wind_plant_degradation_power_decrease = (
            0.08  # to estimate cost of plant oversizing
        )

        resource_year = 2013
        sample_site["year"] = resource_year
        useful_life = 30
        critical_load_factor = 1
        EOL_eff_drop = electrolyzer_degradation_power_increase * 100
        BOL_kWh_per_kg = []

        discount_rate = 0.07  # financial inputs
        debt_equity_split = 60
        storage_om_percent = 0.025  # percent of capex

        hydrogen_consumption_for_steel = 0.06596  # kg H2/kg steel production
        hydrogen_consumption_for_ammonia = 0.197284403  # kg H2/kg NH3 production
        electrolyzer_energy_kWh_per_kg_estimate_BOL = 54.61
        # ^- eventually need to re-arrange things to get this from
        #      set_electrolyzer_info 54.55
        cluster_cap_mw = 40

        cooling_water_cost = 0.000113349938601175  # $/Gal
        iron_based_catalyst_cost = 23.19977341  # $/kg
        oxygen_cost = 0.0285210891617726  # $/kg

        ## variables
        atb_year = 2030  # 2020, 2025, 2030, 2035
        policy_key = "no-policy"
        site_location = "Site 2"  # "Site 1", "Site 2", "Site 3", "Site 4", "Site 5"
        electrolysis_scale = "Centralized"  # "Centralized", "Distributed"
        grid_connection_scenario = "off-grid"  # "off-grid", "grid-only", "hybrid-grid"
        storage_capacity_multiplier = 1.0  # 1.0, 1.25, 1.5
        number_pem_stacks = 6
        steel_annual_production_rate_target_tpy = 1000000  # target steel prod. rate
        # ^- note that this is the production after taking into account steel
        #      plant capacity factor. e.g., if CF is 0.9, divide the number
        #      above by 0.9 to get the total steel plant capacity used for
        #      economic calculations

        ### set-up

        # establish directories
        project_root = os.path.join(
            os.path.abspath(""), "out_cfrontin"
        )  # os.path.abspath("")
        results_dir = os.path.join(project_root, "results")
        fin_sum_dir = os.path.join(project_root, "results", "Phase1B", "Fin_summary")
        energy_profile_dir = os.path.join(
            project_root, "results", "Phase1B", "Energy_profiles"
        )
        price_breakdown_dir = os.path.join(
            project_root, "results", "Phase1B", "ProFAST_price"
        )
        floris_dir = os.path.join(project_root, "input", "floris")
        orbit_path = os.path.join(
            source_root,
            "examples",
            "H2_Analysis",
            "OSW_H2_sites_turbines_and_costs.xlsx",
        )
        renewable_cost_path = os.path.join(
            source_root,
            "examples",
            "H2_Analysis",
            "green_steel_site_renewable_costs_ATB.xlsx",
        )
        if run_RODeO_selector == True:
            # RODeO requires output directory in this format, but apparently this format
            # is problematic for people who use Mac
            rodeo_output_dir = os.path.join(project_root, "RODeO_files", "Output_test")
        else:
            # People who use Mac probably won't be running RODeO, so we can just give
            # the model a dummy string for this variable
            rodeo_output_dir = os.path.join(project_root, "RODeO_files", "Output_test")

        # derived parameters

        if grid_connection_scenario != "off-grid":
            sell_price = 0.025  # $/kWh
            buy_price = 0.025  # $/kWh
        else:
            sell_price = False
            buy_price = False
        # ^- enable ability to purchase/sell electricity to/from grid.

        assert atb_year in [2020, 2025, 2030, 2035]
        grid_year = atb_year + 5
        # ^- not sure why but grid_year was manually keyed before

        ## settings storage
        policy_set = {
            "no-policy": {"Wind ITC": 0, "Wind PTC": 0, "H2 PTC": 0, "Storage ITC": 0},
            "base": {
                "Wind ITC": 0,
                "Wind PTC": 0.0051,
                "H2 PTC": 0.6,
                "Storage ITC": 0.06,
            },
            "max": {
                "Wind ITC": 0,
                "Wind PTC": 0.03072,
                "H2 PTC": 3.0,
                "Storage ITC": 0.5,
            },
            "max on grid hybrid": {
                "Wind ITC": 0,
                "Wind PTC": 0.0051,
                "H2 PTC": 0.60,
                "Storage ITC": 0.06,
            },
            "max on grid hybrid": {
                "Wind ITC": 0,
                "Wind PTC": 0.026,
                "H2 PTC": 0.60,
                "Storage ITC": 0.5,
            },
            "option 3": {"Wind ITC": 0.06, "Wind PTC": 0, "H2 PTC": 0.6},
            "option 4": {"Wind ITC": 0.3, "Wind PTC": 0, "H2 PTC": 3},
            "option 5": {"Wind ITC": 0.5, "Wind PTC": 0, "H2 PTC": 3},
        }
        electrolyzer_model_parameters = {
            "Modify BOL Eff": user_defined_electrolyzer_BOL_kWh_per_kg,
            "BOL Eff [kWh/kg-H2]": BOL_kWh_per_kg,
            "Modify EOL Degradation Value": user_defined_electrolyzer_EOL_eff_drop,
            "EOL Rated Efficiency Drop": EOL_eff_drop,
        }

        ## load file-stored info

        # H2 storage and battery costs
        st_xl = pd.read_csv(
            os.path.join(
                source_root, "examples", "H2_Analysis", "storage_costs_ATB.csv"
            ),
            index_col=0,
        )
        storage_costs = st_xl[str(atb_year)]
        storage_cost_kwh = storage_costs["Battery Energy Capital Cost ($/kWh)"]
        storage_cost_kw = storage_costs["Battery Power Capital Cost ($/kW)"]

        # site specific turbine information
        xl = pd.ExcelFile(renewable_cost_path)
        save_outputs_dict = inputs_py.establish_save_output_dict()
        save_all_runs = list()

        ## site-location specific settings
        if site_location == "Site 1":  # Indiana
            storage_type = "Buried pipes"
            water_cost = 0.00612
            cf_estimate_offgrid = 0.402
            cabling_material_cost = 44553030
            transmission_cost_site = 81060771
        elif site_location == "Site 2":  # Texas
            storage_type = "Salt cavern"
            water_cost = 0.00811
            cf_estimate_offgrid = 0.492
            cabling_material_cost = 44553030
            transmission_cost_site = 83409258
        elif site_location == "Site 3":  # Iowa
            storage_type = "Buried pipes"
            water_cost = 0.00634
            cf_estimate_offgrid = 0.395
            cabling_material_cost = 44514220
            transmission_cost_site = 68034484
        elif site_location == "Site 4":  # Mississippi
            storage_type = "Salt cavern"
            water_cost = 0.00844
            cf_estimate_offgrid = 0.303
            cabling_material_cost = 62751510
            transmission_cost_site = 77274704
        elif site_location == "Site 5":  # Wyoming
            storage_type = "Salt cavern"  # unsure
            water_cost = 0.00533  # Commercial water cost for Cheyenne https://www.cheyennebopu.org/Residential/Billing-Rates/Water-Sewer-Rates
            cf_estimate_offgrid = 0.511
            cabling_material_cost = 44514220
            transmission_cost_site = 68034484
        else:
            raise NotImplementedError(f"{site_location} not configured.")
        # ^- water_cost: municipal water rates and wastewater treatment rates combined ($/gal)
        # ^- cabling_material_cost: eventually replace with calculations

        # THESE ARE WORKING VARIABLES NOW
        # solar_size_mw = 0
        # storage_size_mw = 0
        # storage_size_mwh = 0
        if electrolysis_scale == "Centralized":
            default_n_pem_clusters = 25
        else:
            default_n_pem_clusters = 1
        if number_pem_stacks == "None":
            n_pem_clusters = default_n_pem_clusters
        else:
            n_pem_clusters = number_pem_stacks
        scenario_choice = "Green Steel Ammonia Analysis"

        scenario = dict()

        # Site lat and lon will be set by data loaded from Orbit runs

        # These inputs are not used in this analysis (no solar or storage)
        solar_cost_kw = 9999  # THESE ARE OVERWRITTEN LATER
        solar_om_cost_kw = 9999
        renewable_plant_cost = {}

        # Read in gams exe and license location
        if run_RODeO_selector == True:
            with open("gams_exe_license_locations.txt") as f:
                gams_locations_rodeo_version = f.readlines()
            f.close()
        # ^- create a .txt file in notepad with the locations of the gams .exe
        #      file, the .gms RODeO version that you want to use, and the
        #      location of the gams license file. the text should look something
        #      like this:
        #        "C:\\GAMS\\win64\\24.8\\gams.exe" ..\\RODeO\\Storage_dispatch_SCS license=C:\\GAMS\\win64\\24.8\\gamslice.txt
        #      do not push this file to the remote repository because it will be
        #      different for every user and for every machine, depending on what
        #      version of gams they are using and where it is installed

        hopp_dict = hoppDict(save_model_input_yaml, save_model_output_yaml)

        sub_dict = {
            "policy": policy_set[policy_key],
            "atb_year": atb_year,
            "site_location": site_location,
            "parent_path": project_root,
            # 'load': load,
            # 'kw_continuous': kw_continuous,
            "sample_site": sample_site,
            "discount_rate": discount_rate,
            "forced_sizes": forced_sizes,
            "force_electrolyzer_cost": force_electrolyzer_cost,
            # "wind_size": wind_size_mw,
            "solar_size": solar_size_mw,
            "storage_size_mw": storage_size_mw,
            "storage_size_mwh": storage_size_mwh,
            "solar_cost_kw": solar_cost_kw,
            "storage_cost_kw": storage_cost_kw,
            "storage_cost_kwh": storage_cost_kwh,
            "debt_equity_split": debt_equity_split,
            "useful_life": useful_life,
            "critical_load_factor": critical_load_factor,
            "run_reopt_flag": run_reopt_flag,
            "custom_powercurve": custom_powercurve,
            "storage_used": storage_used,
            "battery_can_grid_charge": battery_can_grid_charge,
            "grid_connected_hopp": grid_connected_hopp,
            # 'interconnection_size_mw': interconnection_size_mw,
            "electrolyzer_size_mw": electrolyzer_size_mw,
            "scenario": {
                "Useful Life": useful_life,
                "Debt Equity": debt_equity_split,
                "discount_rate": discount_rate,
            },
            "sell_price": sell_price,
            "buy_price": buy_price,
            "h2_model": h2_model,
            "results_dir": results_dir,
            "scenario_choice": scenario_choice,
        }
        hopp_dict.add("Configuration", sub_dict)

        plot_dict = {
            "plot": {
                "plot_power_production": False,
                "plot_battery": False,
                "plot_grid": False,
                "plot_h2": False,
                "plot_desal": True,
                "plot_wind": True,
                "plot_hvdcpipe": True,
                "plot_hvdcpipe_lcoh": True,
            }
        }
        hopp_dict.add("Configuration", plot_dict)

        # set policy values
        hopp_dict, scenario, policy_option = hopp_tools_steel.set_policy_values(
            hopp_dict, scenario, policy_set, policy_key
        )

        scenario_df = xl.parse()
        scenario_df.set_index(["Parameter"], inplace=True)
        site_df = scenario_df[site_location]
        turbine_model = str(site_df["Turbine Rating"]) + "MW"
        turbine_rating = site_df["Turbine Rating"]

        # set turbine values
        hopp_dict, scenario, nTurbs, floris_config = hopp_tools_steel.set_turbine_model(
            hopp_dict,
            turbine_model,
            scenario,
            project_root,
            floris_dir,
            floris,
            site_location,
            grid_connection_scenario,
        )

        if floris:
            if nTurbs < num_turbines_in:
                raise Exception("default farm doesn't have enough turbines!")
            else:
                floris_config["farm"]["layout_x"] = floris_config["farm"]["layout_x"][
                    :num_turbines_in
                ]
                floris_config["farm"]["layout_y"] = floris_config["farm"]["layout_y"][
                    :num_turbines_in
                ]
                nTurbs_avail = nTurbs
                nTurbs = num_turbines_in

        # Establish wind farm and electrolyzer sizing

        # Calculate target hydrogen and electricity demand

        # Annual hydrogen production target to meet steel production target
        steel_ammonia_plant_cf = 0.9
        hydrogen_production_target_kgpy = (
            steel_annual_production_rate_target_tpy
            * 1000
            * hydrogen_consumption_for_steel
            / steel_ammonia_plant_cf
        )

        # Calculate equivalent ammona production target
        ammonia_production_target_kgpy = (
            hydrogen_production_target_kgpy
            / hydrogen_consumption_for_ammonia
            * steel_ammonia_plant_cf
        )

        electrolyzer_energy_kWh_per_kg_estimate_EOL = (
            electrolyzer_energy_kWh_per_kg_estimate_BOL
            * (1 + electrolyzer_degradation_power_increase)
        )

        wind_size_mw = nTurbs * turbine_rating

        hydrogen_production_capacity_required_kgphr = (
            electrolyzer_size_mw
            * 1000
            / electrolyzer_energy_kWh_per_kg_estimate_BOL
        )

        interconnection_size_mw = wind_size_mw  # this makes sense because wind_size_mw captures extra electricity needed by electrolzyer at end of life
        n_pem_clusters_max = int(np.ceil(electrolyzer_size_mw / cluster_cap_mw))

        if electrolysis_scale == "Distributed":
            n_pem_clusters = 1
        elif electrolysis_scale == "Centralized":
            n_pem_clusters = n_pem_clusters_max

        kw_continuous = electrolyzer_size_mw * 1000
        load = [
            kw_continuous for x in range(0, 8760)
        ]  # * (sin(x) + pi) Set desired/required load profile for plant
        if battery_for_minimum_electrolyzer_op:
            battery_dispatch_load = list(0.1 * np.array(load))
        else:
            battery_dispatch_load = list(np.array(load))

        # Add things to hopp_dict that we couldn't add before getting wind and electrolyzer size
        sub_dict = {
            "wind_size": wind_size_mw,
            "kw_continuous": kw_continuous,
            "interconnection_size_mw": interconnection_size_mw,
            "electrolyzer_size_mw": electrolyzer_size_mw,
        }
        hopp_dict.add("Configuration", sub_dict)

        scenario["Useful Life"] = useful_life

        # financials
        hopp_dict, scenario = hopp_tools_steel.set_financial_info(
            hopp_dict, scenario, debt_equity_split, discount_rate
        )

        # set electrolyzer information
        (
            hopp_dict,
            electrolyzer_capex_kw,
            electrolyzer_component_costs_kw,
            capex_ratio_dist,
            electrolyzer_energy_kWh_per_kg,
            time_between_replacement,
        ) = hopp_tools_steel.set_electrolyzer_info(
            hopp_dict,
            atb_year,
            electrolysis_scale,
            electrolyzer_cost_case,
            electrolyzer_degradation_power_increase,
            grid_connection_scenario,
            turbine_rating,
            direct_coupling,
        )
        print("electrolyzer_capex_kw:", electrolyzer_capex_kw)

        electrolyzer_installation_factor = 12 / 100
        electrolyzer_direct_cost_kw = electrolyzer_capex_kw * (
            1 + electrolyzer_installation_factor
        )

        # Extract Scenario Information from ORBIT Runs
        # Load Excel file of scenarios
        # OSW sites and cost file including turbines 8/16/2022

        # site info
        # solar_size_mw=0
        hopp_dict, site_df, sample_site = hopp_tools_steel.set_site_info(
            hopp_dict, site_df, sample_site
        )
        site_name = site_df["State"]
        # fixed_or_floating_wind = site_df['Substructure technology']
        site = SiteInfo(sample_site, hub_height=scenario["Tower Height"])

        # Assign scenario cost details
        if atb_year == 2020:
            total_capex = site_df["2020 CapEx"]
            wind_om_cost_kw = site_df["2020 OpEx ($/kw-yr)"] * (
                1 + wind_plant_degradation_power_decrease
            )
        if atb_year == 2025:
            total_capex = site_df["2025 CapEx"]
            wind_om_cost_kw = site_df["2025 OpEx ($/kw-yr)"] * (
                1 + wind_plant_degradation_power_decrease
            )
        if atb_year == 2030:
            total_capex = site_df["2030 CapEx"]
            wind_om_cost_kw = site_df["2030 OpEx ($/kw-yr)"] * (
                1 + wind_plant_degradation_power_decrease
            )
        if atb_year == 2035:
            total_capex = site_df["2035 CapEx"]
            wind_om_cost_kw = site_df["2035 OpEx ($/kw-yr)"] * (
                1 + wind_plant_degradation_power_decrease
            )

        hopp_dict.add("Configuration", {"site": site})
        if grid_connection_scenario != "grid-only":
            capex_multiplier = site_df["CapEx Multiplier"]
            wind_cost_kw = (
                copy.deepcopy(total_capex)
                * capex_multiplier
                * (1 + wind_plant_degradation_power_decrease)
            )
            hopp_dict.main_dict["Configuration"]["wind_om_cost_kw"] = wind_om_cost_kw
            hopp_dict.main_dict["Configuration"]["wind_cost_kw"] = wind_cost_kw
            renewable_plant_cost["wind"] = {
                "o&m_per_kw": wind_om_cost_kw,
                "capex_per_kw": wind_cost_kw,
                "size_mw": wind_size_mw,
            }
            if solar_size_mw > 0:
                solar_om_cost_kw = site_df[str(atb_year) + " PV OpEx"]
                solar_capex_multiplier = site_df["PV Capex Multiplier"]
                solar_capex = site_df[str(atb_year) + " PV base installed cost"]
                solar_cost_kw = solar_capex * solar_capex_multiplier
                hopp_dict.main_dict["Configuration"]["solar_size"] = solar_size_mw
                hopp_dict.main_dict["Configuration"]["solar_cost_kw"] = solar_cost_kw
                hopp_dict.main_dict["Configuration"][
                    "solar_om_cost_kw"
                ] = solar_om_cost_kw
            renewable_plant_cost["pv"] = {
                "o&m_per_kw": solar_om_cost_kw,
                "capex_per_kw": solar_cost_kw,
                "size_mw": solar_size_mw,
            }
            if storage_size_mw > 0:
                storage_hours = storage_size_mwh / storage_size_mw
            else:
                storage_hours = 0
            renewable_plant_cost["battery"] = {
                "capex_per_kw": storage_cost_kwh,
                "capex_per_kwh": storage_cost_kwh,
                "o&m_percent": storage_om_percent,
                "size_mw": storage_size_mw,
                "size_mwh": storage_size_mwh,
                "storage_hours": storage_hours,
            }

            # Plot Wind Cost Contributions
            # Plot a nested pie chart of results
            # TODO: Remove export system from pieplot
            # plot_results.plot_pie(site_df, site_name, turbine_model, results_dir)
            # start for-loop!
            if storage_size_mw > 0:
                storage_hours = storage_size_mwh / storage_size_mw
            else:
                storage_hours = 0
            renewable_plant_cost["battery"] = {
                "capex_per_kw": storage_cost_kwh,
                "capex_per_kwh": storage_cost_kwh,
                "o&m_percent": storage_om_percent,
                "size_mw": storage_size_mw,
                "size_mwh": storage_size_mwh,
                "storage_hours": storage_hours,
            }
            run_wind_plant = True
            if storage_size_mw > 0:
                hopp_dict.main_dict["Configuration"][
                    "storage_size_mw"
                ] = storage_size_mw
                hopp_dict.main_dict["Configuration"][
                    "storage_size_mwh"
                ] = storage_size_mwh
                hopp_dict.main_dict["Configuration"][
                    "battery_cost_kw"
                ] = storage_cost_kw
                hopp_dict.main_dict["Configuration"][
                    "battery_cost_kwh"
                ] = storage_cost_kwh

            # ## skip running renewables if grid-only
            # if True: #grid_connection_scenario != 'grid-only':
            # Run HOPP
            (
                hopp_dict,
                combined_pv_wind_power_production_hopp,
                energy_shortfall_hopp,
                combined_pv_wind_curtailment_hopp,
                hybrid_plant,
                wind_size_mw,
                solar_size_mw,
                lcoe,
            ) = hopp_tools_steel.run_HOPP(
                hopp_dict,
                scenario,
                site,
                sample_site,
                forced_sizes,
                solar_size_mw,
                wind_size_mw,
                storage_size_mw,
                storage_size_mwh,
                wind_cost_kw,
                solar_cost_kw,
                storage_cost_kw,
                storage_cost_kwh,
                kw_continuous,
                load,
                electrolyzer_size_mw,
                wind_om_cost_kw,
                solar_om_cost_kw,
                nTurbs,
                floris_config,
                floris,
                run_wind_plant,
            )

            cf_wind_annuals = hybrid_plant.wind._financial_model.Outputs.cf_annual_costs
            if solar_size_mw > 0:
                cf_solar_annuals = (
                    hybrid_plant.pv._financial_model.Outputs.cf_annual_costs
                )
            else:
                cf_solar_annuals = np.zeros(30)
            wind_itc_total = hybrid_plant.wind._financial_model.Outputs.itc_total

            generation_summary_df = pd.DataFrame(
                {
                    "Generation profile (kW)": hybrid_plant.grid.generation_profile[
                        0:8760
                    ]
                }
            )

            # run simple dispatch model
            (
                hopp_dict,
                combined_pv_wind_storage_power_production_hopp,
                battery_SOC,
                battery_used,
                excess_energy,
            ) = hopp_tools_steel.run_battery(
                hopp_dict,
                energy_shortfall_hopp,
                combined_pv_wind_curtailment_hopp,
                combined_pv_wind_power_production_hopp,
            )

            # grid information
            (
                hopp_dict,
                cost_to_buy_from_grid,
                profit_from_selling_to_grid,
                energy_to_electrolyzer,
            ) = hopp_tools_steel.grid(
                hopp_dict,
                combined_pv_wind_storage_power_production_hopp,
                sell_price,
                excess_energy,
                buy_price,
                kw_continuous,
                plot_grid,
            )

        # else:
        else:  # thus, (grid_connection_scenario == "grid-only")
            wind_cost_kw = 0
            lcoe = 0
            wind_size_mw = 0
            solar_size_mw = 0
            storage_size_mw = 0
            storage_hours = 0
            cf_wind_annuals = np.zeros(30)
            cf_solar_annuals = np.zeros(30)
            wind_itc_total = 0

            combined_pv_wind_storage_power_production_hopp = np.zeros(len(load))
            combined_pv_wind_curtailment_hopp = np.zeros(len(load))
            energy_shortfall_hopp = load
            excess_energy = np.zeros(len(load))
            hybrid_plant = 0

            # grid information
            (
                hopp_dict,
                cost_to_buy_from_grid,
                profit_from_selling_to_grid,
                energy_to_electrolyzer,
            ) = hopp_tools_steel.grid(
                hopp_dict,
                combined_pv_wind_storage_power_production_hopp,
                sell_price,
                excess_energy,
                buy_price,
                kw_continuous,
                plot_grid,
            )

        # Calculate capacity factor of electricity. For now  basing off wind size because we are setting electrolyzer capacity = wind capacity,
        # but in future may want to adjust this
        cf_electricity = sum(energy_to_electrolyzer) / (
            electrolyzer_size_mw * 8760 * 1000
        )

        # Step #: Calculate hydrogen pipe costs for distributed case
        if electrolysis_scale == "Distributed":
            # Add losses back into distributed case
            energy_to_electrolyzer_new = []
            for energy_hr in energy_to_electrolyzer:
                energy_to_electrolyzer_new.append(
                    energy_hr * (1 + 0.0424 / (1 - 0.1283))
                )

            energy_to_electrolyzer = energy_to_electrolyzer_new

            # High level estimate of max hydrogen flow rate. Doesn't have to be perfect, but should be slightly conservative (higher efficiency)
            hydrogen_max_hourly_production_kg = (
                max(energy_to_electrolyzer) / electrolyzer_energy_kWh_per_kg
            )

            # Run pipe cost analysis module
            (
                pipe_network_cost_total_USD,
                pipe_network_costs_USD,
                pipe_material_cost_bymass_USD,
            ) = distributed_pipe_cost_analysis.hydrogen_steel_pipeline_cost_analysis(
                project_root,
                turbine_model,
                hydrogen_max_hourly_production_kg,
                site_name,
            )

            pipeline_material_cost = pipe_network_costs_USD[
                "Total material cost ($)"
            ].sum()

            transmission_cost = 0

            cabling_vs_pipeline_cost_difference = (
                cabling_material_cost - pipeline_material_cost
            )

            turbine_power_electronics_savings = 13

        elif electrolysis_scale == "Centralized":
            cabling_vs_pipeline_cost_difference = 0
            if (
                grid_connection_scenario == "hybrid-grid"
                or grid_connection_scenario == "grid-only"
            ):
                transmission_cost = transmission_cost_site
            else:
                transmission_cost = 0

            turbine_power_electronics_savings = 0

        if grid_connection_scenario != "grid-only":
            revised_renewable_cost = (
                hybrid_plant.grid.total_installed_cost
                - cabling_vs_pipeline_cost_difference
                - turbine_power_electronics_savings * wind_size_mw * 1000
                + transmission_cost
            )
            renewable_plant_cost["wind_savings_dollars"] = {
                "turbine_power_electronics_savings_dollars": -1
                * turbine_power_electronics_savings
                * wind_size_mw
                * 1000,
                "tranmission_cost_dollars": transmission_cost,
                "cabling_vs_pipeline_cost_difference_dollars": -1
                * cabling_vs_pipeline_cost_difference,
            }
        else:
            revised_renewable_cost = 0.0

        # Step 6: Run RODeO or Profast for hydrogen

        if run_RODeO_selector == True:
            (
                rodeo_scenario,
                lcoh,
                electrolyzer_capacity_factor,
                hydrogen_storage_duration_hr,
                hydrogen_storage_capacity_kg,
                hydrogen_annual_production,
                water_consumption_hourly,
                RODeO_summary_results_dict,
                hydrogen_hourly_results_RODeO,
                electrical_generation_timeseries,
                electrolyzer_installed_cost_kw,
                hydrogen_storage_cost_USDprkg,
            ) = run_RODeO.run_RODeO(
                atb_year,
                site_name,
                turbine_model,
                electrolysis_scale,
                policy_option,
                policy_set[policy_key],
                i,
                wind_size_mw,
                solar_size_mw,
                electrolyzer_size_mw,
                energy_to_electrolyzer,
                electrolyzer_energy_kWh_per_kg,
                hybrid_plant,
                renewable_plant_cost,
                electrolyzer_capex_kw,
                capex_ratio_dist,
                wind_om_cost_kw,
                useful_life,
                time_between_replacement,
                grid_connection_scenario,
                grid_price_scenario,
                gams_locations_rodeo_version,
                rodeo_output_dir,
            )

            hydrogen_lifecycle_emissions = (
                LCA_single_scenario.hydrogen_LCA_singlescenario(
                    grid_connection_scenario,
                    atb_year,
                    site_name,
                    turbine_model,
                    electrolysis_scale,
                    policy_option,
                    grid_price_scenario,
                    electrolyzer_energy_kWh_per_kg,
                    hydrogen_hourly_results_RODeO,
                )
            )

            # Max hydrogen production rate [kg/hr]
            max_hydrogen_production_rate_kg_hr = hydrogen_hourly_results_RODeO[
                "Electrolyzer hydrogen production [kg/hr]"
            ].max()
            max_hydrogen_delivery_rate_kg_hr = hydrogen_hourly_results_RODeO[
                "Product Sold (units of product)"
            ].max()

            electrolyzer_capacity_factor = RODeO_summary_results_dict[
                "input capacity factor"
            ]

        else:
            # If not running RODeO, run H2A via ProFAST
            # Currently only works for offgrid
            # grid_string = 'offgrid'
            # scenario_name = 'steel_'+str(atb_year)+'_'+ site_location.replace(' ','-') +'_'+turbine_model+'_'+grid_string

            # Run the H2_PEM model to get hourly hydrogen output, capacity factor, water consumption, etc.
            (
                hopp_dict,
                H2_Results,
                electrical_generation_timeseries,
            ) = hopp_tools_steel.run_H2_PEM_sim(
                hopp_dict,
                energy_to_electrolyzer,
                scenario,
                electrolyzer_size_mw,
                electrolysis_scale,
                n_pem_clusters,
                pem_control_type,
                electrolyzer_direct_cost_kw,
                electrolyzer_model_parameters,
                electrolyzer_degradation_penalty,
                grid_connection_scenario,
                hydrogen_production_capacity_required_kgphr,
            )

            # Step 6b: Run desal model
            (
                hopp_dict,
                desal_capex,
                desal_opex,
                desal_annuals,
            ) = hopp_tools_steel.desal_model(
                hopp_dict,
                H2_Results,
                electrolyzer_size_mw,
                electrical_generation_timeseries,
                useful_life,
            )

            hydrogen_annual_production = H2_Results["hydrogen_annual_output"]

            # Calculate required storage capacity to meet a flat demand profile. In the future, we could customize this to
            # work with any demand profile

            # Storage costs as a function of location

            (
                hydrogen_production_storage_system_output_kgprhr,
                hydrogen_storage_capacity_kg,
                hydrogen_storage_capacity_MWh_HHV,
                hydrogen_storage_duration_hr,
                hydrogen_storage_cost_USDprkg,
                storage_status_message,
            ) = hopp_tools_steel.hydrogen_storage_capacity_cost_calcs(
                H2_Results, electrolyzer_size_mw, storage_type
            )

            # Apply storage multiplier
            hydrogen_storage_capacity_kg = (
                hydrogen_storage_capacity_kg * storage_capacity_multiplier
            )

            # Run ProFAST to get LCOH

            electrolyzer_efficiency_while_running = []
            water_consumption_while_running = []
            hydrogen_production_while_running = []
            for j in range(len(H2_Results["electrolyzer_total_efficiency"])):
                if H2_Results["hydrogen_hourly_production"][j] > 0:
                    electrolyzer_efficiency_while_running.append(
                        H2_Results["electrolyzer_total_efficiency"][j]
                    )
                    water_consumption_while_running.append(
                        H2_Results["water_hourly_usage"][j]
                    )
                    hydrogen_production_while_running.append(
                        H2_Results["hydrogen_hourly_production"][j]
                    )

            # Read in csv for grid prices
            grid_prices = pd.read_csv(
                os.path.join(
                    source_root,
                    "examples",
                    "H2_Analysis",
                    "annual_average_retail_prices.csv",
                ),
                index_col=None,
                header=0,
            )
            elec_price = grid_prices.loc[
                grid_prices["Year"] == grid_year, site_name
            ].tolist()[0]

            (
                h2_solution,
                h2_summary,
                profast_h2_price_breakdown,
                lcoh_breakdown,
                electrolyzer_installed_cost_kw,
                elec_cf,
                ren_frac,
                electrolysis_total_EI_policy_grid,
                electrolysis_total_EI_policy_offgrid,
                H2_PTC,
                Ren_PTC,
                h2_production_capex,
            ) = run_profast_for_hydrogen.run_profast_for_hydrogen(
                hopp_dict,
                electrolyzer_size_mw,
                H2_Results,
                electrolyzer_capex_kw,
                time_between_replacement,
                electrolyzer_energy_kWh_per_kg,
                hydrogen_storage_capacity_kg,
                hydrogen_storage_cost_USDprkg,
                desal_capex,
                desal_opex,
                useful_life,
                water_cost,
                wind_size_mw,
                solar_size_mw,
                storage_size_mw,
                renewable_plant_cost,
                wind_om_cost_kw,
                grid_connected_hopp,
                grid_connection_scenario,
                atb_year,
                site_name,
                policy_option,
                electrical_generation_timeseries,
                combined_pv_wind_storage_power_production_hopp,
                combined_pv_wind_curtailment_hopp,
                energy_shortfall_hopp,
                elec_price,
                grid_price_scenario,
                user_defined_stack_replacement_time,
                use_optimistic_pem_efficiency,
            )

            lcoh = h2_solution["price"]

            # # Max hydrogen production rate [kg/hr]
            max_hydrogen_production_rate_kg_hr = np.max(
                H2_Results["hydrogen_hourly_production"]
            )
            max_hydrogen_delivery_rate_kg_hr = np.mean(
                H2_Results["hydrogen_hourly_production"]
            )

            electrolyzer_capacity_factor = H2_Results["cap_factor"]

        # Calculate hydrogen transmission cost and add to LCOH
        (
            hopp_dict,
            h2_transmission_economics_from_profast,
            h2_transmission_economics_summary,
            h2_transmission_price,
            h2_transmission_price_breakdown,
        ) = hopp_tools_steel.levelized_cost_of_h2_transmission(
            hopp_dict,
            max_hydrogen_production_rate_kg_hr,
            max_hydrogen_delivery_rate_kg_hr,
            electrolyzer_capacity_factor,
            atb_year,
            site_name,
        )

        lcoh = lcoh + h2_transmission_price
        # Policy impacts on LCOH

        if run_RODeO_selector == True:
            (
                lcoh,
                lcoh_reduction_Ren_PTC,
                lcoh_reduction_H2_PTC,
            ) = hopp_tools_steel.policy_implementation_for_RODeO(
                grid_connection_scenario,
                atb_year,
                site_name,
                turbine_model,
                electrolysis_scale,
                policy_option,
                grid_price_scenario,
                electrolyzer_energy_kWh_per_kg,
                hydrogen_hourly_results_RODeO,
                RODeO_summary_results_dict,
                hydrogen_annual_production,
                useful_life,
                lcoh,
            )

        # Step 7: Calculate break-even cost of steel production without oxygen and heat integration
        lime_unit_cost = (
            site_df["Lime ($/metric tonne)"]
            + site_df["Lime Transport ($/metric tonne)"]
        )
        carbon_unit_cost = (
            site_df["Carbon ($/metric tonne)"]
            + site_df["Carbon Transport ($/metric tonne)"]
        )
        iron_ore_pellets_unit_cost = (
            site_df["Iron Ore Pellets ($/metric tonne)"]
            + site_df["Iron Ore Pellets Transport ($/metric tonne)"]
        )
        o2_heat_integration = 0
        (
            hopp_dict,
            steel_economics_from_profast,
            steel_economics_summary,
            profast_steel_price_breakdown,
            steel_breakeven_price,
            steel_annual_production_mtpy,
            steel_production_capacity_margin_pc,
            steel_price_breakdown,
        ) = hopp_tools_steel.steel_LCOS(
            hopp_dict,
            lcoh,
            hydrogen_annual_production,
            steel_annual_production_rate_target_tpy,
            lime_unit_cost,
            carbon_unit_cost,
            iron_ore_pellets_unit_cost,
            o2_heat_integration,
            atb_year,
            site_name,
        )

        # Calcualte break-even price of steel WITH oxygen and heat integration
        o2_heat_integration = 1
        (
            hopp_dict,
            steel_economics_from_profast_integration,
            steel_economics_summary_integration,
            profast_steel_price_breakdown_integration,
            steel_breakeven_price_integration,
            steel_annual_production_mtpy_integration,
            steel_production_capacity_margin_pc_integration,
            steel_price_breakdown_integration,
        ) = hopp_tools_steel.steel_LCOS(
            hopp_dict,
            lcoh,
            hydrogen_annual_production,
            steel_annual_production_rate_target_tpy,
            lime_unit_cost,
            carbon_unit_cost,
            iron_ore_pellets_unit_cost,
            o2_heat_integration,
            atb_year,
            site_name,
        )

        # Calculate break-even price of ammonia
        (
            hopp_dict,
            ammonia_economics_from_profast,
            ammonia_economics_summary,
            profast_ammonia_price_breakdown,
            ammonia_breakeven_price,
            ammonia_annual_production_kgpy,
            ammonia_production_capacity_margin_pc,
            ammonia_price_breakdown,
        ) = hopp_tools_steel.levelized_cost_of_ammonia(
            hopp_dict,
            lcoh,
            hydrogen_annual_production,
            ammonia_production_target_kgpy,
            cooling_water_cost,
            iron_based_catalyst_cost,
            oxygen_cost,
            atb_year,
            site_name,
        )

        # Step 7: Write outputs to file

        total_h2export_system_cost = 0
        opex_pipeline = 0
        total_export_system_cost = 0
        total_export_om_cost = 0

        if run_RODeO_selector == True:
            (
                policy_option,
                turbine_model,
                scenario["Useful Life"],
                wind_cost_kw,
                solar_cost_kw,
                scenario["Debt Equity"],
                atb_year,
                scenario["H2 PTC"],
                scenario["Wind ITC"],
                discount_rate,
                tlcc_wind_costs,
                tlcc_solar_costs,
                tlcc_hvdc_costs,
                tlcc_total_costs,
                run_RODeO_selector,
                lcoh,
                wind_itc_total,
                total_itc_hvdc,
            ) = hopp_tools_steel.write_outputs_RODeO(
                electrical_generation_timeseries,
                hybrid_plant,
                total_export_system_cost,
                total_export_om_cost,
                cost_to_buy_from_grid,
                electrolyzer_capex_kw,
                electrolyzer_installed_cost_kw,
                hydrogen_storage_cost_USDprkg,
                time_between_replacement,
                profit_from_selling_to_grid,
                useful_life,
                atb_year,
                policy_option,
                scenario,
                wind_cost_kw,
                solar_cost_kw,
                discount_rate,
                solar_size_mw,
                results_dir,
                fin_sum_dir,
                site_name,
                turbine_model,
                electrolysis_scale,
                scenario_choice,
                lcoe,
                run_RODeO_selector,
                grid_connection_scenario,
                grid_price_scenario,
                lcoh,
                h2_transmission_price,
                lcoh_reduction_Ren_PTC,
                lcoh_reduction_H2_PTC,
                electrolyzer_capacity_factor,
                hydrogen_storage_duration_hr,
                hydrogen_storage_capacity_kg,
                hydrogen_annual_production,
                water_consumption_hourly,
                RODeO_summary_results_dict,
                steel_annual_production_mtpy,
                steel_breakeven_price,
                steel_price_breakdown,
                steel_breakeven_price_integration,
                ammonia_annual_production_kgpy,
                ammonia_breakeven_price,
                ammonia_price_breakdown,
            )
        else:
            (
                policy_option,
                turbine_model,
                scenario["Useful Life"],
                wind_cost_kw,
                solar_cost_kw,
                scenario["Debt Equity"],
                atb_year,
                scenario["H2 PTC"],
                scenario["Wind ITC"],
                discount_rate,
                tlcc_wind_costs,
                tlcc_solar_costs,
                tlcc_hvdc_costs,
                tlcc_total_costs,
                run_RODeO_selector,
                lcoh,
                wind_itc_total,
                total_itc_hvdc,
            ) = hopp_tools_steel.write_outputs_ProFAST(
                electrical_generation_timeseries,
                cf_wind_annuals,
                cf_solar_annuals,
                wind_itc_total,
                total_export_system_cost,
                total_export_om_cost,
                cost_to_buy_from_grid,
                electrolyzer_capex_kw,
                electrolyzer_installed_cost_kw,
                electrolyzer_cost_case,
                hydrogen_storage_cost_USDprkg,
                time_between_replacement,
                profit_from_selling_to_grid,
                useful_life,
                atb_year,
                policy_option,
                scenario,
                wind_cost_kw,
                solar_cost_kw,
                wind_size_mw,
                solar_size_mw,
                storage_size_mw,
                storage_hours,
                electrolyzer_size_mw,
                discount_rate,
                results_dir,
                fin_sum_dir,
                energy_profile_dir,
                price_breakdown_dir,
                site_name,
                turbine_model,
                electrolysis_scale,
                scenario_choice,
                lcoe,
                cf_electricity,
                run_RODeO_selector,
                grid_connection_scenario,
                grid_price_scenario,
                lcoh,
                h2_transmission_price,
                h2_production_capex,
                H2_Results,
                elec_cf,
                ren_frac,
                electrolysis_total_EI_policy_grid,
                electrolysis_total_EI_policy_offgrid,
                H2_PTC,
                Ren_PTC,
                False,  # run_pv_battery_sweep,
                electrolyzer_degradation_penalty,
                user_defined_stack_replacement_time,
                pem_control_type,
                n_pem_clusters,
                storage_capacity_multiplier,
                floris,
                hydrogen_storage_duration_hr,
                hydrogen_storage_capacity_kg,
                lcoh_breakdown,
                steel_annual_production_mtpy,
                steel_production_capacity_margin_pc,
                steel_breakeven_price,
                steel_price_breakdown,
                steel_breakeven_price_integration,
                ammonia_annual_production_kgpy,
                ammonia_production_capacity_margin_pc,
                ammonia_breakeven_price,
                ammonia_price_breakdown,
                profast_h2_price_breakdown,
                profast_steel_price_breakdown,
                profast_ammonia_price_breakdown,
                hopp_dict,
            )

    return (lcoh, lcoe, 0.0, 0.0)


if __name__ == "__main__":
    solar_size_mw = 1000.0
    storage_size_mw = 0.0  # 1000.0
    storage_size_mwh = 0.0  # 1000.0

    args = (solar_size_mw, storage_size_mw, storage_size_mwh)

    lcoh, lcoe, _, _ = run(args)

    print(f"solar_size_mw: {solar_size_mw:0.3f}")
    print(f"lcoh: {lcoh}", f"lcoe: {lcoe}")
