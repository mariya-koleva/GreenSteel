# -*- coding: utf-8 -*-
"""
Created on Thu Nov 10 14:36:13 2022

@author: ereznic2
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

aeo_dir = '../../../Cost data/AEO Data/'
dircambium = 'H2_Analysis/Cambium_data/' 
final_retail_price_directory = 'examples/H2_Analysis/RODeO_files/Data_files/TXT_files/Elec_prices/Elec_purch_price_MWh_MC95by35_'

plot_directory = 'Plots'
plot_subdirectory = 'Grid_Prices'

write_output_tofile = True

#---------------- Calculate Cambium average wholesale prices ------------------

# Analysis years
years_cambium = [2022,2025,2030,2035,2040,2045,2050]

cambium_ws_prices_IN_avg = []
cambium_ws_prices_IA_avg = []
cambium_ws_prices_TX_avg = []
cambium_ws_prices_MS_avg = []
cambium_ws_prices_WY_avg = []
cambium_ws_prices_MN_avg = []

for year in years_cambium:
    # Read in Cambium wholesale prices
    cambium_ws_prices_IN = pd.read_csv(dircambium + 'Cambium22_MidCase100by2035_hourly_IN_'+str(year)+'.csv',index_col = None,header = 5,usecols = ['energy_cost_enduse','total_cost_enduse'])
    cambium_ws_prices_IA = pd.read_csv(dircambium + 'Cambium22_MidCase100by2035_hourly_IA_'+str(year)+'.csv',index_col = None,header = 5,usecols = ['energy_cost_enduse','total_cost_enduse'])
    cambium_ws_prices_TX = pd.read_csv(dircambium + 'Cambium22_MidCase100by2035_hourly_TX_'+str(year)+'.csv',index_col = None,header = 5,usecols = ['energy_cost_enduse','total_cost_enduse'])
    cambium_ws_prices_MS = pd.read_csv(dircambium + 'Cambium22_MidCase100by2035_hourly_MS_'+str(year)+'.csv',index_col = None,header = 5,usecols = ['energy_cost_enduse','total_cost_enduse'])
    cambium_ws_prices_WY = pd.read_csv(dircambium + 'Cambium22_MidCase100by2035_hourly_WY_'+str(year)+'.csv',index_col = None,header = 5,usecols = ['energy_cost_enduse','total_cost_enduse'])
 
    # Calculate average annual Cambium wholesale prices
    cambium_ws_prices_IN_avg.append(np.mean(cambium_ws_prices_IN['total_cost_enduse']))
    cambium_ws_prices_IA_avg.append(np.mean(cambium_ws_prices_IA['total_cost_enduse']))
    cambium_ws_prices_TX_avg.append(np.mean(cambium_ws_prices_TX['total_cost_enduse']))
    cambium_ws_prices_MS_avg.append(np.mean(cambium_ws_prices_MS['total_cost_enduse']))    
    cambium_ws_prices_WY_avg.append(np.mean(cambium_ws_prices_WY['total_cost_enduse']))

#----------------- Get AEO projected retail prices for 2022 -------------------

# Read in AEO projected retail prices
aeo_projected_retail_prices = pd.read_csv(aeo_dir + 'aeo_2022_retail_rates'+'.csv',index_col = None,header = 0)
    
# Calculate future retail prices using 2022 AEO retail prices and Cambium wholesale prices    
# Get 2022 AEO projected retail prices
retail_price_aeo_2022_IN = aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==2022,'Indiana'].tolist()[0]
retail_price_aeo_2022_IA = aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==2022,'Iowa'].tolist()[0]    
retail_price_aeo_2022_TX = aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==2022,'Texas'].tolist()[0]
retail_price_aeo_2022_MS = aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==2022,'Mississippi'].tolist()[0] 
retail_price_aeo_2022_WY = aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==2022,'Wyoming'].tolist()[0]   

# Calculate ratio of AEO 2022 retail prices to Cambium 2022 Wholesale prices
ratios_retail_ws = {'IN':retail_price_aeo_2022_IN/cambium_ws_prices_IN_avg[0],
                    'IA':retail_price_aeo_2022_IA/cambium_ws_prices_IA_avg[0],
                    'TX':retail_price_aeo_2022_TX/cambium_ws_prices_TX_avg[0],
                    'MS':retail_price_aeo_2022_MS/cambium_ws_prices_MS_avg[0],
                    'WY':retail_price_aeo_2022_WY/cambium_ws_prices_WY_avg[0]}

# Calculate adders for AEO 2022 retail prices from Cambium 2022 Wholesale prices
adders_retail_ws = {'IN':retail_price_aeo_2022_IN-cambium_ws_prices_IN_avg[0],
                    'IA':retail_price_aeo_2022_IA-cambium_ws_prices_IA_avg[0],
                    'TX':retail_price_aeo_2022_TX-cambium_ws_prices_TX_avg[0],
                    'MS':retail_price_aeo_2022_MS-cambium_ws_prices_MS_avg[0],
                    'WY':retail_price_aeo_2022_WY-cambium_ws_prices_WY_avg[0]}

#-------------- Calculate AEO/Cambium scaled future retail prices -------------
cambium_retail_prices_IN_avg_mult = []
cambium_retail_prices_IA_avg_mult = []
cambium_retail_prices_TX_avg_mult = []
cambium_retail_prices_MS_avg_mult = []
cambium_retail_prices_WY_avg_mult = []

cambium_retail_prices_IN_avg_adder = []
cambium_retail_prices_IA_avg_adder = []
cambium_retail_prices_TX_avg_adder = []
cambium_retail_prices_MS_avg_adder = []
cambium_retail_prices_WY_avg_adder = []

for year in range(len(years_cambium)):
    cambium_retail_prices_IN_avg_mult.append(ratios_retail_ws['IN']*cambium_ws_prices_IN_avg[year])
    cambium_retail_prices_IA_avg_mult.append(ratios_retail_ws['IA']*cambium_ws_prices_IA_avg[year])
    cambium_retail_prices_TX_avg_mult.append(ratios_retail_ws['TX']*cambium_ws_prices_TX_avg[year])
    cambium_retail_prices_MS_avg_mult.append(ratios_retail_ws['MS']*cambium_ws_prices_MS_avg[year])   
    cambium_retail_prices_WY_avg_mult.append(ratios_retail_ws['WY']*cambium_ws_prices_WY_avg[year])  
    cambium_retail_prices_IN_avg_adder.append(adders_retail_ws['IN']+cambium_ws_prices_IN_avg[year])
    cambium_retail_prices_IA_avg_adder.append(adders_retail_ws['IA']+cambium_ws_prices_IA_avg[year])
    cambium_retail_prices_TX_avg_adder.append(adders_retail_ws['TX']+cambium_ws_prices_TX_avg[year])
    cambium_retail_prices_MS_avg_adder.append(adders_retail_ws['MS']+cambium_ws_prices_MS_avg[year])   
    cambium_retail_prices_WY_avg_adder.append(adders_retail_ws['WY']+cambium_ws_prices_WY_avg[year])  

# ---------------- Moving average of future retail prices ---------------------

cambium_retail_prices_IN_moving_avg_mult = []
cambium_retail_prices_IA_moving_avg_mult = []
cambium_retail_prices_TX_moving_avg_mult = []
cambium_retail_prices_MS_moving_avg_mult = []
cambium_retail_prices_WY_moving_avg_mult = []

cambium_retail_prices_IN_moving_avg_adder = []
cambium_retail_prices_IA_moving_avg_adder = []
cambium_retail_prices_TX_moving_avg_adder = []
cambium_retail_prices_MS_moving_avg_adder = []
cambium_retail_prices_WY_moving_avg_adder = []

cambium_ws_prices_IN_moving_avg = []
cambium_ws_prices_IA_moving_avg = []
cambium_ws_prices_TX_moving_avg = []
cambium_ws_prices_MS_moving_avg = []
cambium_ws_prices_WY_moving_avg = []

# For 2022, just use same value
cambium_retail_prices_IN_moving_avg_mult.append(cambium_retail_prices_IN_avg_mult[0])
cambium_retail_prices_IA_moving_avg_mult.append(cambium_retail_prices_IA_avg_mult[0])
cambium_retail_prices_TX_moving_avg_mult.append(cambium_retail_prices_TX_avg_mult[0])
cambium_retail_prices_MS_moving_avg_mult.append(cambium_retail_prices_MS_avg_mult[0])
cambium_retail_prices_WY_moving_avg_mult.append(cambium_retail_prices_WY_avg_mult[0])

cambium_retail_prices_IN_moving_avg_adder.append(cambium_retail_prices_IN_avg_adder[0])
cambium_retail_prices_IA_moving_avg_adder.append(cambium_retail_prices_IA_avg_adder[0])
cambium_retail_prices_TX_moving_avg_adder.append(cambium_retail_prices_TX_avg_adder[0])
cambium_retail_prices_MS_moving_avg_adder.append(cambium_retail_prices_MS_avg_adder[0])
cambium_retail_prices_WY_moving_avg_adder.append(cambium_retail_prices_WY_avg_adder[0])

cambium_ws_prices_IN_moving_avg.append(cambium_ws_prices_IN_avg[0])
cambium_ws_prices_IA_moving_avg.append(cambium_ws_prices_IA_avg[0])
cambium_ws_prices_TX_moving_avg.append(cambium_ws_prices_TX_avg[0])
cambium_ws_prices_MS_moving_avg.append(cambium_ws_prices_MS_avg[0])
cambium_ws_prices_WY_moving_avg.append(cambium_ws_prices_WY_avg[0])

for j in range(1,len(years_cambium)-1):
    cambium_retail_prices_IN_moving_avg_mult.append(0.3*cambium_retail_prices_IN_avg_mult[j-1]+0.4*cambium_retail_prices_IN_avg_mult[j]+0.3*cambium_retail_prices_IN_avg_mult[j+1])
    cambium_retail_prices_IA_moving_avg_mult.append(0.3*cambium_retail_prices_IA_avg_mult[j-1]+0.4*cambium_retail_prices_IA_avg_mult[j]+0.3*cambium_retail_prices_IA_avg_mult[j+1])
    cambium_retail_prices_TX_moving_avg_mult.append(0.3*cambium_retail_prices_TX_avg_mult[j-1]+0.4*cambium_retail_prices_TX_avg_mult[j]+0.3*cambium_retail_prices_TX_avg_mult[j+1])
    cambium_retail_prices_MS_moving_avg_mult.append(0.3*cambium_retail_prices_MS_avg_mult[j-1]+0.4*cambium_retail_prices_MS_avg_mult[j]+0.3*cambium_retail_prices_MS_avg_mult[j+1])
    cambium_retail_prices_WY_moving_avg_mult.append(0.3*cambium_retail_prices_WY_avg_mult[j-1]+0.4*cambium_retail_prices_WY_avg_mult[j]+0.3*cambium_retail_prices_WY_avg_mult[j+1])

    cambium_retail_prices_IN_moving_avg_adder.append(0.3*cambium_retail_prices_IN_avg_adder[j-1]+0.4*cambium_retail_prices_IN_avg_adder[j]+0.3*cambium_retail_prices_IN_avg_adder[j+1])
    cambium_retail_prices_IA_moving_avg_adder.append(0.3*cambium_retail_prices_IA_avg_adder[j-1]+0.4*cambium_retail_prices_IA_avg_adder[j]+0.3*cambium_retail_prices_IA_avg_adder[j+1])
    cambium_retail_prices_TX_moving_avg_adder.append(0.3*cambium_retail_prices_TX_avg_adder[j-1]+0.4*cambium_retail_prices_TX_avg_adder[j]+0.3*cambium_retail_prices_TX_avg_adder[j+1])
    cambium_retail_prices_MS_moving_avg_adder.append(0.3*cambium_retail_prices_MS_avg_adder[j-1]+0.4*cambium_retail_prices_MS_avg_adder[j]+0.3*cambium_retail_prices_MS_avg_adder[j+1])
    cambium_retail_prices_WY_moving_avg_adder.append(0.3*cambium_retail_prices_WY_avg_adder[j-1]+0.4*cambium_retail_prices_WY_avg_adder[j]+0.3*cambium_retail_prices_WY_avg_adder[j+1])

    cambium_ws_prices_IN_moving_avg.append(0.3*cambium_ws_prices_IN_avg[j-1]+0.4*cambium_ws_prices_IN_avg[j]+0.3*cambium_ws_prices_IN_avg[j+1])
    cambium_ws_prices_IA_moving_avg.append(0.3*cambium_ws_prices_IA_avg[j-1]+0.4*cambium_ws_prices_IA_avg[j]+0.3*cambium_ws_prices_IA_avg[j+1])
    cambium_ws_prices_TX_moving_avg.append(0.3*cambium_ws_prices_TX_avg[j-1]+0.4*cambium_ws_prices_TX_avg[j]+0.3*cambium_ws_prices_TX_avg[j+1])
    cambium_ws_prices_MS_moving_avg.append(0.3*cambium_ws_prices_MS_avg[j-1]+0.4*cambium_ws_prices_MS_avg[j]+0.3*cambium_ws_prices_MS_avg[j+1])
    cambium_ws_prices_WY_moving_avg.append(0.3*cambium_ws_prices_WY_avg[j-1]+0.4*cambium_ws_prices_WY_avg[j]+0.3*cambium_ws_prices_WY_avg[j+1])

# Only plot/process through 2040 (2046 is just there for the moving averages)
years_cambium = years_cambium[0:-1]

# Global Plot Settings
font = 'Arial'
title_size = 10
axis_label_size = 10
legend_size = 6
tick_size = 10
resolution = 150

# # Plot future retail prices with and without moving average
# fig, ax = plt.subplots(1,1,figsize=(4.8,3.6), dpi= resolution)
# ax = plt.gca()
# ax.plot(years_cambium,cambium_retail_prices_IN_avg[0:-1],marker = '.',color = 'b',linestyle='--')
# ax.plot(years_cambium,cambium_retail_prices_IA_avg[0:-1],marker='.',color = 'r',linestyle='--')
# ax.plot(years_cambium,cambium_retail_prices_TX_avg[0:-1],marker = '.',color = 'g',linestyle='--')
# ax.plot(years_cambium,cambium_retail_prices_MS_avg[0:-1],marker='.',color = 'm',linestyle='--')
# ax.plot(years_cambium,cambium_retail_prices_WY_avg[0:-1],marker='.',color = 'k',linestyle='--')

# ax.plot(years_cambium,cambium_retail_prices_IN_moving_avg,marker = '.',color = 'b')
# ax.plot(years_cambium,cambium_retail_prices_IA_moving_avg,marker='.',color = 'r')
# ax.plot(years_cambium,cambium_retail_prices_TX_moving_avg,marker = '.',color = 'g')
# ax.plot(years_cambium,cambium_retail_prices_MS_moving_avg,marker='.',color = 'm')
# ax.plot(years_cambium,cambium_retail_prices_WY_moving_avg,marker='.',color = 'k')

# labels = ['IN Cambium retail','IA Cambium retail','TX Cambium retail','MS Cambium retail','WY Cambium retail',\
#           'IN Cambium retail MA','IA Cambium retail MA','TX Cambium retail MA','MS Cambium retail MA','WY Camium retail MA']
# ax.legend(labels,prop = {'family':'Arial','size':6},loc='upper left')
# ax.set_ylabel('Price ($/MWh)', fontname = font, fontsize = axis_label_size)
# ax.set_xlabel('Year', fontname = font, fontsize = axis_label_size)
# ax.tick_params(axis = 'y',labelsize = 10,direction = 'in')
# ax.tick_params(axis = 'x',labelsize = 10,direction = 'in')
# #ax.set_ylim([20,140])
# plt.show()

# # Plot future retail prices vs AEO projections
# fig, ax = plt.subplots(1,1,figsize=(4.8,3.6), dpi= resolution)
# ax = plt.gca()
# ax.plot(years_cambium,cambium_retail_prices_IN_moving_avg,marker = '.',color = 'b')
# ax.plot(years_cambium,cambium_retail_prices_IA_moving_avg,marker='.',color = 'r')
# ax.plot(years_cambium,cambium_retail_prices_TX_moving_avg,marker = '.',color = 'g')
# ax.plot(years_cambium,cambium_retail_prices_MS_moving_avg,marker='.',color = 'm')
# ax.plot(years_cambium,cambium_retail_prices_WY_moving_avg,marker='.',color = 'k')

# ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Indiana'],color = 'b',linestyle = '--')
# ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Iowa'],color = 'r',linestyle = '--')
# ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Texas'],color = 'g',linestyle = '--')
# ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Mississippi'],color = 'm',linestyle = '--')
# ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Wyoming'],color = 'k',linestyle = '--')

# labels = ['IN Cambium retail','IA Cambium retail','TX Cambium retail','MS Cambium retail','WY Cambium retail',\
#           'IN AEO retail','IA AEO retail','TX AEO retail','MS AEO retail', 'WY AEO retail']
# ax.legend(labels,prop = {'family':'Arial','size':6},loc='upper left')
# ax.set_ylabel('Price ($/MWh)', fontname = font, fontsize = axis_label_size)
# ax.set_xlabel('Year', fontname = font, fontsize = axis_label_size)
# ax.tick_params(axis = 'y',labelsize = 10,direction = 'in')
# ax.tick_params(axis = 'x',labelsize = 10,direction = 'in')
# ax.set_ylim([20,200])
# plt.show()

# Select whichever is higher: AEO projection or Cambium estimation
future_retail_price_IN_combined_mult = []
future_retail_price_IA_combined_mult = []
future_retail_price_TX_combined_mult = []
future_retail_price_MS_combined_mult = []
future_retail_price_WY_combined_mult = []
future_retail_price_IN_combined_dict_mult = {}
future_retail_price_IA_combined_dict_mult = {}
future_retail_price_TX_combined_dict_mult = {}
future_retail_price_MS_combined_dict_mult = {}
future_retail_price_WY_combined_dict_mult = {}

future_retail_price_IN_combined_adder = []
future_retail_price_IA_combined_adder = []
future_retail_price_TX_combined_adder = []
future_retail_price_MS_combined_adder = []
future_retail_price_WY_combined_adder = []
future_retail_price_IN_combined_dict_adder = {}
future_retail_price_IA_combined_dict_adder = {}
future_retail_price_TX_combined_dict_adder = {}
future_retail_price_MS_combined_dict_adder = {}
future_retail_price_WY_combined_dict_adder = {}

cambium_ws_price_IN_combined_dict = {}
cambium_ws_price_IA_combined_dict = {}
cambium_ws_price_TX_combined_dict = {}
cambium_ws_price_MS_combined_dict = {}
cambium_ws_price_WY_combined_dict = {}

for j in range(len(years_cambium)):
    year = years_cambium[j]
    
    # Put into list for plotting
    future_retail_price_IN_combined_mult.append(max(cambium_retail_prices_IN_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Indiana'].tolist()[0]))
    future_retail_price_IA_combined_mult.append(max(cambium_retail_prices_IA_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Iowa'].tolist()[0]))
    future_retail_price_TX_combined_mult.append(max(cambium_retail_prices_TX_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Texas'].tolist()[0]))
    future_retail_price_MS_combined_mult.append(max(cambium_retail_prices_MS_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Mississippi'].tolist()[0]))
    future_retail_price_WY_combined_mult.append(max(cambium_retail_prices_WY_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Wyoming'].tolist()[0]))
    
    # Put into dictionary for subsequent data processing
    future_retail_price_IN_combined_dict_mult[year]=max(cambium_retail_prices_IN_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Indiana'].tolist()[0])
    future_retail_price_IA_combined_dict_mult[year]=max(cambium_retail_prices_IA_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Iowa'].tolist()[0])
    future_retail_price_TX_combined_dict_mult[year]=max(cambium_retail_prices_TX_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Texas'].tolist()[0])
    future_retail_price_MS_combined_dict_mult[year]=max(cambium_retail_prices_MS_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Mississippi'].tolist()[0])
    future_retail_price_WY_combined_dict_mult[year]=max(cambium_retail_prices_WY_moving_avg_mult[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Wyoming'].tolist()[0])

    # Put into list for plotting
    future_retail_price_IN_combined_adder.append(max(cambium_retail_prices_IN_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Indiana'].tolist()[0]))
    future_retail_price_IA_combined_adder.append(max(cambium_retail_prices_IA_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Iowa'].tolist()[0]))
    future_retail_price_TX_combined_adder.append(max(cambium_retail_prices_TX_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Texas'].tolist()[0]))
    future_retail_price_MS_combined_adder.append(max(cambium_retail_prices_MS_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Mississippi'].tolist()[0]))
    future_retail_price_WY_combined_adder.append(max(cambium_retail_prices_WY_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Wyoming'].tolist()[0]))
    
    # Put into dictionary for subsequent data processing
    future_retail_price_IN_combined_dict_adder[year]=max(cambium_retail_prices_IN_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Indiana'].tolist()[0])
    future_retail_price_IA_combined_dict_adder[year]=max(cambium_retail_prices_IA_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Iowa'].tolist()[0])
    future_retail_price_TX_combined_dict_adder[year]=max(cambium_retail_prices_TX_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Texas'].tolist()[0])
    future_retail_price_MS_combined_dict_adder[year]=max(cambium_retail_prices_MS_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Mississippi'].tolist()[0])
    future_retail_price_WY_combined_dict_adder[year]=max(cambium_retail_prices_WY_moving_avg_adder[j],aeo_projected_retail_prices.loc[aeo_projected_retail_prices['Year']==year,'Wyoming'].tolist()[0])

    cambium_ws_price_IN_combined_dict[year] = cambium_ws_prices_IN_moving_avg[j]
    cambium_ws_price_IA_combined_dict[year] = cambium_ws_prices_IA_moving_avg[j]
    cambium_ws_price_TX_combined_dict[year] = cambium_ws_prices_TX_moving_avg[j]
    cambium_ws_price_MS_combined_dict[year] = cambium_ws_prices_MS_moving_avg[j]
    cambium_ws_price_WY_combined_dict[year] = cambium_ws_prices_WY_moving_avg[j]

# Set final year data equal to 2050 data from cambium
future_retail_price_IN_combined_mult.append(cambium_retail_prices_IN_avg_mult[-1])
future_retail_price_TX_combined_mult.append(cambium_retail_prices_TX_avg_mult[-1])
future_retail_price_IA_combined_mult.append(cambium_retail_prices_IA_avg_mult[-1])
future_retail_price_MS_combined_mult.append(cambium_retail_prices_MS_avg_mult[-1])
future_retail_price_WY_combined_mult.append(cambium_retail_prices_WY_avg_mult[-1])

future_retail_price_IN_combined_dict_mult[2050] = cambium_retail_prices_IN_avg_mult[-1]
future_retail_price_TX_combined_dict_mult[2050] = cambium_retail_prices_TX_avg_mult[-1]
future_retail_price_IA_combined_dict_mult[2050] = cambium_retail_prices_IA_avg_mult[-1]
future_retail_price_MS_combined_dict_mult[2050] = cambium_retail_prices_MS_avg_mult[-1]
future_retail_price_WY_combined_dict_mult[2050] = cambium_retail_prices_WY_avg_mult[-1]

# Set final year data equal to 2050 data from cambium
future_retail_price_IN_combined_adder.append(cambium_retail_prices_IN_avg_adder[-1])
future_retail_price_TX_combined_adder.append(cambium_retail_prices_TX_avg_adder[-1])
future_retail_price_IA_combined_adder.append(cambium_retail_prices_IA_avg_adder[-1])
future_retail_price_MS_combined_adder.append(cambium_retail_prices_MS_avg_adder[-1])
future_retail_price_WY_combined_adder.append(cambium_retail_prices_WY_avg_adder[-1])

future_retail_price_IN_combined_dict_adder[2050] = cambium_retail_prices_IN_avg_adder[-1]
future_retail_price_TX_combined_dict_adder[2050] = cambium_retail_prices_TX_avg_adder[-1]
future_retail_price_IA_combined_dict_adder[2050] = cambium_retail_prices_IA_avg_adder[-1]
future_retail_price_MS_combined_dict_adder[2050] = cambium_retail_prices_MS_avg_adder[-1]
future_retail_price_WY_combined_dict_adder[2050] = cambium_retail_prices_WY_avg_adder[-1]

cambium_ws_prices_IN_moving_avg.append(cambium_ws_prices_IN_avg[-1])
cambium_ws_prices_TX_moving_avg.append(cambium_ws_prices_TX_avg[-1])
cambium_ws_prices_IA_moving_avg.append(cambium_ws_prices_IA_avg[-1])
cambium_ws_prices_MS_moving_avg.append(cambium_ws_prices_MS_avg[-1])
cambium_ws_prices_WY_moving_avg.append(cambium_ws_prices_WY_avg[-1])

cambium_ws_price_IN_combined_dict[2050] = cambium_ws_prices_IN_avg[-1]
cambium_ws_price_IA_combined_dict[2050] = cambium_ws_prices_IA_avg[-1]
cambium_ws_price_TX_combined_dict[2050] = cambium_ws_prices_TX_avg[-1]
cambium_ws_price_MS_combined_dict[2050] = cambium_ws_prices_MS_avg[-1]
cambium_ws_price_WY_combined_dict[2050] = cambium_ws_prices_WY_avg[-1]

future_retail_prices_dict_mult = {'IN':future_retail_price_IN_combined_dict_mult,'IA':future_retail_price_IA_combined_dict_mult,'TX':future_retail_price_TX_combined_dict_mult,'MS':future_retail_price_MS_combined_dict_mult,'WY':future_retail_price_WY_combined_dict_mult,'MN':future_retail_price_IA_combined_dict_mult}    
future_retail_prices_dict_adder = {'IN':future_retail_price_IN_combined_dict_adder,'IA':future_retail_price_IA_combined_dict_adder,'TX':future_retail_price_TX_combined_dict_adder,'MS':future_retail_price_MS_combined_dict_adder,'WY':future_retail_price_WY_combined_dict_adder,'MN':future_retail_price_IA_combined_dict_adder}    
future_ws_prices_dict = {'IN':cambium_ws_price_IN_combined_dict,'IA':cambium_ws_price_IA_combined_dict,'TX':cambium_ws_price_TX_combined_dict,'MS':cambium_ws_price_MS_combined_dict,'WY':cambium_ws_price_WY_combined_dict,'MN':cambium_ws_price_IA_combined_dict}    


future_retail_prices_df_mult = pd.DataFrame.from_dict(future_retail_prices_dict_mult,orient='columns')
future_retail_prices_df_adder = pd.DataFrame.from_dict(future_retail_prices_dict_adder,orient='columns')
future_ws_prices_df = pd.DataFrame.from_dict(future_ws_prices_dict,orient='columns')
future_retail_prices_df_mult.to_csv('H2_Analysis/annual_average_retail_prices_mult.csv',sep = ',')
future_retail_prices_df_adder.to_csv('H2_Analysis/annual_average_retail_prices_adder.csv',sep = ',')
future_ws_prices_df.to_csv('H2_Analysis/annual_average_ws_prices.csv',sep=',')

years_cambium.append(2050)
# Plot combined future retail prices vs AEO projections
fig, ax = plt.subplots(1,1,figsize=(4.8,3.6), dpi= resolution)
ax = plt.gca()
ax.plot(years_cambium,future_retail_price_IN_combined_adder,marker = '.',color = 'b')
ax.plot(years_cambium,future_retail_price_IA_combined_adder,marker='.',color = 'r')
ax.plot(years_cambium,future_retail_price_TX_combined_adder,marker = '.',color = 'g')
ax.plot(years_cambium,future_retail_price_MS_combined_adder,marker='.',color = 'm')
#ax.plot(years_cambium,future_retail_price_WY_combined,marker='.',color = 'k')

ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Indiana'],color = 'b',linestyle = '--')
ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Iowa'],color = 'r',linestyle = '--')
ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Texas'],color = 'g',linestyle = '--')
ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Mississippi'],color = 'm',linestyle = '--')
#ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Minnesota'],color = 'm',linestyle = '--')

#labels = ['IN combined retail','IA combined retail','TX combined retail','MS combined retail','WY combined retail',\
#          'IN AEO retail','IA AEO retail','TX AEO retail','MS AEO retail','WY AEO retail']
labels = ['IN combined retail','IA combined retail','TX combined retail','MS combined retail',\
'IN AEO retail','IA AEO retail','TX AEO retail','MS AEO retail']
ax.legend(labels,prop = {'family':'Arial','size':6},loc='upper left')
ax.set_ylabel('Price ($/MWh)', fontname = font, fontsize = axis_label_size)
ax.set_xlabel('Year', fontname = font, fontsize = axis_label_size)
ax.tick_params(axis = 'y',labelsize = 10,direction = 'in')
ax.tick_params(axis = 'x',labelsize = 10,direction = 'in')
ax.set_ylim([20,200])
#plt.show()
[]

locations = ['IN','TX','IA','MS']

# Plot combined future price spread
fig, ax = plt.subplots(len(locations),1,figsize=(4,6),sharex=True,sharey=True,dpi= resolution)

for axi1,location in enumerate(locations):
    #ax[axi1] = plt.gca()
    ax[axi1].plot(years_cambium,list(future_retail_prices_dict_adder[location].values()),marker = '.',color = 'k')
    # ax[axi1].plot(years_cambium,future_retail_price_IA_combined_adder,marker='.',color = 'r')
    # ax[axi1].plot(years_cambium,future_retail_price_TX_combined_adder,marker = '.',color = 'g')
    # ax[axi1].plot(years_cambium,future_retail_price_MS_combined_adder,marker='.',color = 'm')
    #ax.plot(years_cambium,future_retail_price_WY_combined,marker='.',color = 'k')

    ax[axi1].plot(years_cambium,list(future_retail_prices_dict_mult[location].values()),marker = '.',color = 'r',linestyle = '--')
    # ax[axi1].plot(years_cambium,future_retail_price_IA_combined_mult,marker='.',color = 'r',linestyle = '--')
    # ax[axi1].plot(years_cambium,future_retail_price_TX_combined_mult,marker = '.',color = 'g',linestyle = '--')
    # ax[axi1].plot(years_cambium,future_retail_price_MS_combined_mult,marker='.',color = 'm',linestyle = '--')

    ax[axi1].plot(years_cambium,list(future_ws_prices_dict[location].values()),marker = '.',color = 'b',linestyle = 'dotted')
    # ax[axi1].plot(years_cambium,cambium_ws_prices_IA_moving_avg,marker='.',color = 'r',linestyle = 'dotted')
    # ax[axi1].plot(years_cambium,cambium_ws_prices_TX_moving_avg,marker = '.',color = 'g',linestyle = 'dotted')
    # ax[axi1].plot(years_cambium,cambium_ws_prices_MS_moving_avg,marker='.',color = 'm',linestyle = 'dotted')

    # ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Indiana'],color = 'b',linestyle = '--')
    # ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Iowa'],color = 'r',linestyle = '--')
    # ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Texas'],color = 'g',linestyle = '--')
    # ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Mississippi'],color = 'm',linestyle = '--')
    #ax.plot(aeo_projected_retail_prices['Year'],aeo_projected_retail_prices['Minnesota'],color = 'm',linestyle = '--')

    #labels = ['IN combined retail','IA combined retail','TX combined retail','MS combined retail','WY combined retail',\
    #          'IN AEO retail','IA AEO retail','TX AEO retail','MS AEO retail','WY AEO retail']
    # labels = ['IN combined retail','IA combined retail','TX combined retail','MS combined retail',\
    # 'IN AEO retail','IA AEO retail','TX AEO retail','MS AEO retail']
    labels = ['Adder','Multiplier','Wholesale']
    if axi1==0:   
        ax[axi1].legend(labels,prop = {'family':'Arial','size':6},loc='upper left')
    ax[axi1].set_ylabel(location + ' Grid Price \n ($/MWh)', fontname = font, fontsize = axis_label_size)
    #ax.set_ylabel('Price ($/MWh)', fontname = font, fontsize = axis_label_size)
    if axi1==len(locations):
        ax[axi1].set_xlabel('Year', fontname = font, fontsize = axis_label_size)
    ax[axi1].tick_params(axis = 'y',labelsize = 10,direction = 'in')
    ax[axi1].tick_params(axis = 'x',labelsize = 10,direction = 'in')
    ax[axi1].set_ylim([20,200])
fig.tight_layout()
fig.savefig(plot_directory +'/' + plot_subdirectory +'/' + 'grid_prices_spread.png',pad_inches = 0.1,bbox_inches='tight')
#plt.show()
[]


# locations = ['IN','IA','TX','MS','WY']

# wholesale_price_cases = {}
# retail_flat_price_cases = {}
# retail_peak_price_cases = {}
# for location in locations:
#     for year in years_cambium:
#         #location = 'IN'
#         #year = 2026
#         scenario = location + ' ' + str(year)
        
#         # Read in cambium wholesale prices
#         cambium_prices = pd.read_csv(dircambium + 'StdScen21_MidCASE95by2035_hourly_'+location+'_'+str(year)+'.csv',index_col = None,header = 4,usecols = ['energy_cost_enduse','total_cost_enduse'])

#         # Annual average retail price
#         future_retail_prices = future_retail_prices_dict[location]
        
#         retail_price_avg_year = future_retail_prices[year]
        
#         # Use wholesale prices if higher than annual average retail price
#         wholesale_prices_for_RODeO = []
#         retail_prices_flat_for_RODeO = []
#         retail_prices_peaks_for_RODeO = []
#         for j in range(cambium_prices.shape[0]):
#             # Wholesale only prices
#             wholesale_prices_for_RODeO.append(cambium_prices.loc[j,'total_cost_enduse'])
#             # Retail prices without peaks
#             retail_prices_flat_for_RODeO.append(retail_price_avg_year)
#             # Retail prices with wholesale peaks
#             retail_prices_peaks_for_RODeO.append(max(retail_price_avg_year,cambium_prices.loc[j,'total_cost_enduse']))
         
#         # Formulate dataframes to work with RODeO
#         wholesale_prices_for_RODeO = pd.DataFrame(wholesale_prices_for_RODeO,columns = ['Energy Purchase Price'])
#         retail_prices_flat_for_RODeO = pd.DataFrame(retail_prices_flat_for_RODeO,columns = ['Energy Purchase Price'])
#         retail_prices_peaks_for_RODeO = pd.DataFrame(retail_prices_peaks_for_RODeO,columns = ['Energy Purchase Price'])
        
#         wholesale_prices_for_RODeO = wholesale_prices_for_RODeO.reset_index().rename(columns = {'index':'Interval',0:1})
#         retail_prices_flat_for_RODeO = retail_prices_flat_for_RODeO.reset_index().rename(columns = {'index':'Interval',0:1})
#         retail_prices_peaks_for_RODeO = retail_prices_peaks_for_RODeO.reset_index().rename(columns = {'index':'Interval',0:1})
        
#         wholesale_prices_for_RODeO['Interval'] = wholesale_prices_for_RODeO['Interval']+1
#         retail_prices_flat_for_RODeO['Interval'] = retail_prices_flat_for_RODeO['Interval']+1
#         retail_prices_peaks_for_RODeO['Interval'] = retail_prices_peaks_for_RODeO['Interval']+1
        
#         wholesale_prices_for_RODeO = wholesale_prices_for_RODeO.set_index('Interval')
#         retail_prices_flat_for_RODeO = retail_prices_flat_for_RODeO.set_index('Interval')
#         retail_prices_peaks_for_RODeO = retail_prices_peaks_for_RODeO.set_index('Interval') 
        
#         # Write retail rate dataframe to csv for importing to HOPP or RODeO    
#         if write_output_tofile == True:
#             wholesale_prices_for_RODeO.to_csv(final_retail_price_directory + 'wholesale_' + location+'_' + str(year) + '.csv',sep = ',')
#             retail_prices_flat_for_RODeO.to_csv(final_retail_price_directory + 'retail-flat_' + location+'_' + str(year) + '.csv',sep = ',')
#             retail_prices_peaks_for_RODeO.to_csv(final_retail_price_directory + 'retail-peaks_' + location+'_' + str(year) + '.csv',sep = ',') 
            
#         # Put retail rates into dictionary for plotting
#         wholesale_price_cases[scenario]=wholesale_prices_for_RODeO
#         retail_flat_price_cases[scenario]=retail_prices_flat_for_RODeO
#         retail_peak_price_cases[scenario]=retail_prices_peaks_for_RODeO
        
# # Plot annual retail rate profile for location and year of interest
# location = 'WY'
# year = 2025
# scenario = location + ' ' + str(year)

# wholesale_prices = wholesale_price_cases[scenario] 
# retail_flat_prices = retail_flat_price_cases[scenario]
# retail_peak_prices = retail_peak_price_cases[scenario]
        
# # Plot hourly wholesale price profile
# fig, ax = plt.subplots(3,1,sharex = 'all',figsize=(4,8), dpi= resolution)
# #ax = plt.gca()
# ax[0].plot(wholesale_prices,color = 'k')
# ax[1].plot(retail_flat_prices,color = 'k')
# ax[2].plot(retail_peak_prices,color = 'k')
# ax[0].set_ylabel('Wholesale ($/MWh)', fontname = font, fontsize = axis_label_size)
# ax[1].set_ylabel('Retail Flat ($/MWh)', fontname = font, fontsize = axis_label_size)
# ax[2].set_ylabel('Retail Peaks ($/MWh)', fontname = font, fontsize = axis_label_size)
# ax[2].set_xlabel('Hour of the year', fontname = font, fontsize = axis_label_size)
# ax[0].tick_params(axis = 'y',labelsize = 10,direction = 'in')
# ax[0].tick_params(axis = 'x',labelsize = 10,direction = 'in')
# ax[1].tick_params(axis = 'y',labelsize = 10,direction = 'in')
# ax[1].tick_params(axis = 'x',labelsize = 10,direction = 'in')
# ax[2].tick_params(axis = 'y',labelsize = 10,direction = 'in')
# ax[2].tick_params(axis = 'x',labelsize = 10,direction = 'in')
# plt.show()










