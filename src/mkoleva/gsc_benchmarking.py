# -*- coding: utf-8 -*-

# Evan Reznicek
# 8/9/2023
# This code compares old version of green steel code to new cleaned up veresion of code

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolorsg
import matplotlib.ticker as ticker
import matplotlib.axes as axes
import sqlite3

#Specify directory name for original gsa database
original_gsa_results_dir = 'C:/Users/ereznic2/Documents/Projects/Wind-H2-Steel/Modeling/HOPP-RODeO/HOPP/examples/H2_Analysis/DRB/Fin_sum'

# Read in the summary data for original gsa database
conn = sqlite3.connect(original_gsa_results_dir+'/Default_summary.db')
original_gsa_finsum  = pd.read_sql_query("SELECT * From Summary",conn)

conn.commit()
conn.close()

# Specify directory name for cleanup gsa database
cleanup_gsa_results_dir = 'Res/FS'

# Read in the summary data for cleanup gsa database
conn = sqlite3.connect(cleanup_gsa_results_dir+'/Default_summary.db')
cleanup_gsa_finsum  = pd.read_sql_query("SELECT * From Summary",conn)

conn.commit()
conn.close()

# List of metrics to compare to

metrics = [
            'Total Electricity Production (kWh)',
            'Electricity CF (-)',
            'LCOH ($/kg)',
            'Electrolyzer CF (-)',
            'Fraction of electricity from renewables (-)',
            'Average stack life (hrs)',
            'Hydrogen storage capacity (kg)',
            'Steel annual production (tonne/year)',
            'Ammonia annual production (kg/year)',
            'Steel price: Total ($/tonne)',
            'Ammonia price: Total ($/kg)',
            'Grid Total Emission Intensity (kg-CO2/kg-H2)',
            'H2 PTC ($/kg)',
            'Ren PTC ($/kg)',

]

lcoh_breakdown_categories = [
                            'LCOH: Compression & storage ($/kg)',
                            'LCOH: Electrolyzer CAPEX ($/kg)',
                            'LCOH: Desalination CAPEX ($/kg)',
                            'LCOH: Electrolyzer FOM ($/kg)',
                            'LCOH:Desalination FOM ($/kg)',
                            'LCOH: Electrolyzer FOM ($/kg)',
                            'LCOH:Desalination FOM ($/kg)',
                            'LCOH: Electrolyzer VOM ($/kg)',
                            'LCOH: Wind Plant CAPEX ($/kg)',
                            'LCOH: Wind Plant FOM ($/kg)',
                            'LCOH: Solar Plant CAPEX ($/kg)',
                            'LCOH: Solar Plant FOM ($/kg)',
                            'LCOH: Battery Storage CAPEX ($/kg)',
                            'LCOH: Battery Storage FOM ($/kg)',
                            'LCOH: Taxes and Finances ($/kg)',
                            'LCOH: Water consumption ($/kg)',
                            'LCOH: Grid electricity ($/kg)',
                            'LCOH: Bulk H2 Transmission ($/kg)'
]

steelprice_breakdown_categories = [
                                    'Steel price: EAF and Casting CAPEX ($/tonne)',
                                    'Steel price: Shaft Furnace CAPEX ($/tonne)',
                                    'Steel price: Oxygen Supply CAPEX ($/tonne)',
                                    'Steel price: H2 Pre-heating CAPEX ($/tonne)',
                                    'Steel price: Cooling Tower CAPEX ($/tonne)',
                                    'Steel price: Piping CAPEX ($/tonne)',
                                    'Steel price: Electrical & Instrumentation ($/tonne)',
                                    'Steel price: Buildings, Storage, Water Service CAPEX ($/tonne)',

]

general_metric_errors = original_gsa_finsum[['Electrolysis case','Policy Option','Grid case','Renewables case','Wind model']]
lcoh_breakdown_errors = original_gsa_finsum[['Electrolysis case','Policy Option','Grid case','Renewables case','Wind model']]
steelprice_breakdown_errors = original_gsa_finsum[['Electrolysis case','Policy Option','Grid case','Renewables case','Wind model']]
ammoniaprice_breakdown_errors = original_gsa_finsum[['Electrolysis case','Policy Option','Grid case','Renewables case','Wind model']]



for metric in metrics:
    general_metric_errors[metric + ' Error (%)'] = (original_gsa_finsum[metric]-cleanup_gsa_finsum[metric])/original_gsa_finsum[metric]*100

for lcoh_category in lcoh_breakdown_categories:
    lcoh_breakdown_errors[lcoh_category + ' Error (%)'] = (original_gsa_finsum[lcoh_category]-cleanup_gsa_finsum[lcoh_category])/original_gsa_finsum[lcoh_category]*100

elec_cf_comparison  = original_gsa_finsum[['Electrolysis case','Policy Option','Grid case','Renewables case','Wind model']]
elec_cf_comparison['Original CF (-)']=original_gsa_finsum['Electricity CF (-)']
elec_cf_comparison['Cleanup CF (-)'] = cleanup_gsa_finsum['Electricity CF (-)']
elec_cf_comparison['CF Error (%)'] = general_metric_errors['Electricity CF (-) Error (%)']

lcoh_comparison = original_gsa_finsum[['Electrolysis case','Policy Option','Grid case','Renewables case','Wind model']]
lcoh_comparison['Original LCOH ($/kg)']=original_gsa_finsum['LCOH ($/kg)']
lcoh_comparison['Cleanup LCOH ($/kg)'] = cleanup_gsa_finsum['LCOH ($/kg)']
lcoh_comparison['LCOH Error (%)'] = general_metric_errors['LCOH ($/kg) Error (%)']

lcos_comparison = original_gsa_finsum[['Electrolysis case','Policy Option','Grid case','Renewables case','Wind model']]
lcos_comparison['Original LCOS ($/tonne)']=original_gsa_finsum['Steel price: Total ($/tonne)']
lcos_comparison['Cleanup LCOS ($/tonne)'] = cleanup_gsa_finsum['Steel price: Total ($/tonne)']
lcos_comparison['LCOS Error (%)'] = general_metric_errors['Steel price: Total ($/tonne) Error (%)']

[]