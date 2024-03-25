# GreenSteel
Repository for NREL's green steel technoeconomic publication.

Requires NREL's HOPP model to run. The version of HOPP used for this study can be found at https://github.com/ereznicek/HOPP and selecting the branch titled "green_steel_publication". 

Please note that the latest version of HOPP can be found at github.com/NREL/HOPP.

All of the code required for the analysis can be found in src/ereznic2. The primary scripts used to perform the analysis are as follows:

src/ereznic2/green_steel_ammonia_define_scenarios.py (sets up electrolysis scenarios to run and runs them)

src/ereznic2/SMR_steel_ammonia_run_scenarios.py (runs SMR scenarios)

src/ereznic2/postprocessing_combine_financial_summary_csv_files.py (combines results into databases for easier plotting)

Primary plotting scripts are as follows:

src/ereznic2/green_steel_ammonia_stacked_bar_charts_all_usecases_allyears_alllocations.py

src/ereznic2/green_steel_ammonia_LCOH_stacked_bar_charts_vs_time.py (creates LCOH plots in supplemental info)

src/ereznic2/green_steel_ammonia_regionalsensitivity_allusecases_allyears.py

src/ereznic2/green_steel_ammonia_LCA_barcharts_all_usecases_allyears_alllocations.py

src/ereznic2/windvshybrid_comparison_barcharts.py

Results can be found in the following folders:

src/ereznic2/Results_main (electrolysis production route primary cases)

src/ereznic2/Results_sensitivity (electrolysis production route sensitivity cases)

src/ereznic2/Results_SMR (SMR production route primary and sensitivity cases)

Plots can be found in src/ereznic2/Plots


 