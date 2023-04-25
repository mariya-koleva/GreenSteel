from matplotlib import pyplot as plt
import matplotlib.patches as patches
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from pprint import pprint
import os

def plot_policy_storage_design_options(colors=None, normalized=False, save_plots=False, show_plots=False):

    if colors == None:
        colors_nrel = np.array(["#0079C2", "#00A4E4", "#F7A11A", "#FFC423", "#5D9732", "#8CC63F", "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"])
        use_colors = [0, 1, 2, 4, 6, 7, 8, 9]
        colors = colors_nrel[use_colors]

    results_path = "./data/"
    df = pd.read_csv(results_path+"design-storage-policy-lcoh.csv", index_col=False)
    
    print(df)

    for i in range(0, len(df["Storage"])):
        print(df["Storage"][i])
        if not df["Storage"][i] == "pressure_vessel":
            print("dropping")
            df.drop(labels=i, axis=0, inplace=True)
    print(df)
    df = df.drop(columns=["Storage", "Unnamed: 0", "LCOE [$/kWh]", "Electrolyzer capacity factor"])
    print(df)
    if normalized:
        df["LCOH [$/kg]"] = df["LCOH [$/kg]"].divide(df["LCOH [$/kg]"][0])
        ylim = [0, 1.499]
        ylabel = "LCOH/LCOH$_{base}$"
        tick_locator = ticker.MultipleLocator(0.5)

        # ylabel = "$\\frac{\\text{LCOH}}{\\text{LCOH}_{base}}$"
    else:
        ylim = [0, 14]
        ylabel = "LCOH ($/kg)"
        tick_locator = ticker.MultipleLocator(1)
    
    df_pivot = pd.pivot_table(df, values="LCOH [$/kg]", index="Design", columns="Policy")

    ax = df_pivot.plot.bar(xlabel="Design Scenario", ylabel=ylabel, ylim=ylim, rot=0, color=colors, zorder=1, width=0.8, figsize=(12,6))
    ax.spines[['right', 'top']].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_locator(tick_locator)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", rotation=90, padding=2, size=8)
    plt.grid(visible=True, which="major", axis="y", zorder=0, linestyle="--")
    plt.legend(frameon=False, ncol=4, title="Policy Options", loc=2)

    if normalized:
        normname = "normalized"
    else:
        normname = ""

    savepath = "figures/aggregate/"
    if not os.path.exists(savepath):
        os.makedirs(savepath)

    plt.tight_layout()

    if save_plots:
        plt.savefig(savepath+"design-policy-lcoh-%s.png" %(normname), transparent=True)
    if show_plots:
        plt.show()

def plot_design_options(save_plots=False, show_plots=False):

    colors = ["#0079C2", "#00A4E4", "#F7A11A", "#FFC423", "#5D9732", "#8CC63F", "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"]

    results_path = "./combined_results/"
    output_path = "./figures/aggregate/"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    df_metrics = pd.read_csv(results_path+"metrics.csv", index_col=False)
    df_capex = pd.read_csv(results_path+"capex.csv", index_col=False)
    df_opex = pd.read_csv(results_path+"opex.csv", index_col=False)

    # df_opex = df_opex.transpose()
    lcoe_mwh = df_metrics["LCOE [$/kWh]"]*1E3
    df_metrics["LCOE [$/MWh]"] = lcoe_mwh
    
    df_capex = df_capex.rename(columns={'Unnamed: 0': "Component"})
    df_opex = df_opex.rename(columns={'Unnamed: 0': "Component"})

    df_capex=df_capex.T
    header=df_capex.iloc[0]
    df_capex=df_capex[1:]
    df_capex.columns=header

    df_opex=df_opex.T
    header=df_opex.iloc[0]
    df_opex=df_opex[1:]
    df_opex.columns=header

    df_capex.set_index("Design")
    df_opex.set_index("Design")

    df_capex["Design"] = df_capex["Design"].astype(int)
    df_capex.iloc[:,1:] = df_capex.iloc[:,1:].mul(1E-9)

    df_opex["Design"] = df_opex["Design"].astype(int)
    df_opex.iloc[:,1:] = df_opex.iloc[:,1:].mul(1E-6)
    
    # ax = df_capex.plot.bar(x="Design", stacked=True, legend=True, ylabel="B USD", xlabel="Design Scenario", rot=0, title="CAPEX", ylim=[0,4], figsize=(8,5), color=colors)
    # ax.legend(ncol=2, frameon=False, loc=2)

    # plt.tight_layout()

    # if save_plots:
    #     plt.savefig(output_path+"bar-capex.pdf", transparent=True)
    # if show_plots: 
    #     plt.show()

    # ax = df_opex.plot.bar(x="Design", stacked=True, legend=True, ylabel="M USD", xlabel="Design Scenario", rot=0, title="OPEX", ylim=[0,100], figsize=(8,5), color=colors)
    # ax.legend(ncol=2, frameon=False, loc=2)
    # plt.tight_layout()
    
    # if save_plots:
    #     plt.savefig(output_path+"bar-opex.pdf", transparent=True)
    # if show_plots:
    #     plt.show()

    ax = df_metrics.plot.bar(x="Design", y="LCOH [$/kg]", legend=False, rot=0, ylim=[0,11], ylabel="LCOH ($/kg)", xlabel="Design Scenario", figsize=(4,4), color=colors[0])
    ax.bar_label(ax.containers[0], fmt="%.2f", rotation=90, padding=5)
    plt.tight_layout()

    if save_plots:
        plt.savefig(output_path+"lcoh.png")
    if show_plots:
        plt.show()

    ax = df_metrics.plot.bar(x="Design", y="LCOE [$/MWh]", legend=False, rot=0, ylim=[0,100], ylabel="LCOE ($/MWh)", xlabel="Design Scenario", figsize=(4,4), color=colors[0])
    ax.bar_label(ax.containers[0], fmt="%.2f", rotation=90, padding=5)
    plt.tight_layout()
    
    if save_plots:
        plt.savefig(output_path+"lcoe.png")
    if show_plots:
        plt.show()

    print(df_metrics)

    return 0

def plot_lcoh_breakdown():

    colors = ["#0079C2", "#00A4E4", "#F7A11A", "#FFC423", "#5D9732", "#8CC63F", "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"]

    results_path = "./data/lcoh/"

    designs = range(1,8)

    for d in designs:
        if d == 3:
            df = pd.read_csv(results_path+"cost_breakdown_lcoh_design%i_incentive1_turbinestorage.csv" % (d), index_col=False)
        else:
            df = pd.read_csv(results_path+"cost_breakdown_lcoh_design%i_incentive1_pressure_vesselstorage.csv" % (d), index_col=False)

        df = df[df["NPV"] > 0]

        lcoh = df[df["Name"]=="Hydrogen sales"]["NPV"].sum()
        op_rev = df[df["Type"]=="Operating Revenue"]["NPV"].sum()
        op_ex = df[df["Type"]=="Operating Expenses"]["NPV"].sum()
        fin_in = df[df["Type"]=="Financing cash inflow"]["NPV"].sum()
        fin_out = df[df["Type"]=="Financing cash outflow"]["NPV"].sum()

        print(df[df["Name"]=="Hydrogen sales"]["Type"])
        print(df[df["Type"]=="Operating Expenses"]["Name"])
        print(op_rev)
        print(op_ex)
        print(fin_in)
        print(fin_out)
        print(op_rev - op_ex + fin_in - fin_out)

    ## test
    # quit()

    # print(df[df["Name"]=="Hydrogen sales"]["NPV"])

    print(df.loc[df['Type'] == "Operating Revenue"])
    print(df.loc[df['Type'] == "Operating Expenses"])
    print(df.loc[df['Type'] == "Financing cash inflow"])
    print(df.loc[df['Type'] == "Financing cash outflow"])
    
    typespecs = ["Operating Revenue", "Operating Expenses", "Financing cash inflow", "Financing cash outflow"]
    total = []
    for typespec in typespecs:
        total.append(sum(df.loc[df['Type'] == typespec]["NPV"]))

    print(total[0]+total[2])
    print(total[1]+total[3])
    print(total)
    print()
    return

def plot_orbit_costs(save_plots=False, show_plots=False):
    threshold = 0.001
    round_digits = 2
    df = pd.read_csv("data/orbit_costs/orbit_cost_breakdown_with_onshore_substation_lcoh_design1_incentive1_pressure_vesselstorage.csv")#.set_index("Unnamed: 0").transpose()
    
    # df.drop(["Unnamed: 0"], inplace=True)
    df.rename(columns={"Unnamed: 0": "Item", "0": "CAPEX"}, inplace=True)
    
    df_percent = (df["CAPEX"]/df["CAPEX"].sum())

    df_high = df[df_percent > threshold].dropna()
    df_low = df[df_percent < threshold].dropna()
    # print(df_high)
    # print(df_low)
    df_plot = df_high.copy()
    if df_low["CAPEX"].sum() > 0:
        df_plot = df_plot.append({'Item': "Other", 'CAPEX': round(df_low["CAPEX"].sum(), ndigits=round_digits)}, ignore_index=True)
    print(df_plot)
    df_plot = df_plot.sort_values("CAPEX")
    df_plot["CAPEX"] = round(df_plot["CAPEX"]*1E-6, ndigits=round_digits)

    # get percent labels
    percent_labels = plot_orbit_costs_percent(save_plots=False, show_plots=False, return_labels=True)

    ax = df_plot.plot.barh(stacked=True, y="CAPEX", x="Item", legend=False, xlabel="Cost (M USD)", ylabel="", xlim=[0,1000])

    labels = []
    for cl, pl in zip(ax.containers[0], percent_labels):
        label = "%.1f M USD (%.1f%%)" % (cl.get_width(), pl.get_width())
        labels.append(label)
    ax.bar_label(ax.containers[0], labels=labels, padding=2)

    # # df_plot.append() = df_low.sum()
    # print(df_plot)
    # print(df_grouping)
    # df_grouping["Other"] = (df[df_percent < threshold].sum(axis=1))
    # print(df_grouping)
    # df_grouping.plot.bar()
    plt.tight_layout()

    if save_plots:
        plt.savefig("figures/wind_costs_breakdown.pdf", transparent=True)
    if show_plots:
        plt.show()

def plot_orbit_costs_percent(save_plots=False, show_plots=False, return_labels=False):
    threshold = 0.0
    round_digits = 3
    df = pd.read_csv("data/orbit_costs/orbit_cost_breakdown_with_onshore_substation_lcoh_design1_incentive1_pressure_vesselstorage.csv")#.set_index("Unnamed: 0").transpose()
    
    # df.drop(["Unnamed: 0"], inplace=True)
    df.rename(columns={"Unnamed: 0": "Item", "0": "CAPEX"}, inplace=True)
    
    df["Percent"] = round((df["CAPEX"]/df["CAPEX"].sum()), ndigits=round_digits)

    df_high = df[df["Percent"] > threshold].dropna()
    df_low = df[df["Percent"] < threshold].dropna()
    # print(df_high)
    # print(df_low)
    df_plot = df_high.copy()
    if df_low["CAPEX"].sum() > 0:
        df_plot = df_plot.append({'Item': "Other", 'CAPEX': df_low["CAPEX"].sum(), "Percent": round(df_low["CAPEX"].sum()/df["CAPEX"].sum(), ndigits=round_digits)}, ignore_index=True)
    
    df_plot = df_plot.sort_values("CAPEX")
    df_plot["Percent"] = df_plot["Percent"].multiply(100)

    ax = df_plot.plot.barh(stacked=True, y="Percent", x="Item", legend=False, xlabel="Cost fraction (%)", ylabel="", xlim=[0,40])

    ax.bar_label(ax.containers[0])

    if return_labels:
        return ax.containers[0]

    # # df_plot.append() = df_low.sum()
    # print(df_plot)
    # print(df_grouping)
    # df_grouping["Other"] = (df[df_percent < threshold].sum(axis=1))
    # print(df_grouping)
    # df_grouping.plot.bar()
    plt.tight_layout()

    if save_plots:
        plt.savefig("figures/wind_percent_costs_breakdown.pdf", transparent=True)
    if show_plots:
        plt.show()

def plot_energy_breakdown(colors=None, normalized=False):
    if colors == None:
        colors = np.array(["#0079C2", "#00A4E4", "#F7A11A", "#FFC423", "#5D9732", "#8CC63F", "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"])
        use_colors = [0,2,4,9]
        colors = colors[use_colors]

    results_path = "./data/"
    df = pd.read_csv(results_path+"annual_energy_breakdown.csv", index_col=False)
    
    print(df)


    for i in range(0, len(df["storage"])):
        print(df["storage"][i])
        if (not df["storage"][i] == "pressure_vessel") or (not df["policy"][i] == 1):
            print("dropping design %i, policy %i" %(df["design"][i], df["policy"][i]))
            df.drop(labels=i, axis=0, inplace=True)
    
    df.drop(columns=["policy", "Unnamed: 0", "storage"], inplace=True)
    df = df.rename(columns={"design": "Design"})

    # add sum columns
    df["Total power used"] = df["h2_storage_power_kwh"] + df["desal_kwh"] + df["h2_transport_compressor_power_kwh"] + df["electrolyzer_kwh"]
    # df.set_index("design", inplace=True)
    print(df)
    wind_power = df["wind_kwh"].iloc[0]
    cols = ["wind_kwh", "grid_power_kwh", "h2_storage_power_kwh", "desal_kwh", "h2_transport_compressor_power_kwh", "electrolyzer_kwh","Total power used"]
    df = df[cols]#/wind_power
    df = df.multiply(1E-6) # scale to GWh
    df.rename(columns={"wind_kwh": "Wind", "grid_power_kwh": "Grid", "h2_storage_power_kwh": "H$_2$ Storage", "desal_kwh": "Desalination", "h2_transport_compressor_power_kwh": "H$_2$ Transport Compressor", "electrolyzer_kwh": "Electrolyzer"}, errors="raise", inplace=True)
    # pprint(df)
    # df.plot.bar(stacked=True, ylim=[1E-1, 1E5], rot=0, color=colors, xlabel="Design", ylabel="Annual Energy Use (GWh)")
    
    print(df)
    dft = df.T
    print(dft)
    print(dft.to_latex(index=True, formatters={"design": str.upper},
                  float_format="{:.1f}".format))  
    
    # ax = plt.gca()
    # ax.set_yscale('log')
    # for c in ax.containers:
    #     labels = [str(round(v.get_height(), 2)) + "" if v.get_height() > 0 else '' for v in c]
    #     ax.bar_label(c,
    #                 label_type='center',
    #                 labels = labels,
    #                 size = 6) # add a container object "c" as first argument
    # plt.legend(frameon=False, loc="upper left")


    # print as a table
    # df = df.drop(columns=["Storage", "Unnamed: 0", "LCOE [$/kWh]", "Electrolyzer capacity factor"])
    # print(df)
    # if normalized:
    #     df["LCOH [$/kg]"] = df["LCOH [$/kg]"].divide(df["LCOH [$/kg]"][0])
    #     ylim = [0, 1.499]
    #     ylabel = "LCOH/LCOH$_{base}$"
    #     tick_locator = ticker.MultipleLocator(0.5)

    #     # ylabel = "$\\frac{\\text{LCOH}}{\\text{LCOH}_{base}}$"
    # else:
    #     ylim = [0, 10]
    #     ylabel = "LCOH ($/kg)"
    #     tick_locator = ticker.MultipleLocator(1)
    
    # df_pivot = pd.pivot_table(df, values="LCOH [$/kg]", index="Design", columns="Policy")

    # df_pivot.plot.bar(xlabel="Design Scenario", ylabel=ylabel, ylim=ylim, rot=0, color=colors, zorder=1)
    # ax = plt.gca()
    # ax.spines[['right', 'top']].set_visible(False)
    # ax.set_axisbelow(True)
    # ax.yaxis.set_major_locator(tick_locator)
    # plt.grid(visible=True, which="major", axis="y", zorder=0, linestyle="--")
    # plt.legend(frameon=False, ncol=4, title="Policy Options", loc=2)

    # if normalized:
    #     normname = "normalized"
    # else:
    #     normname = ""

    # plt.savefig("figures/aggregate/annual_energy_use.png", transparent=True)
    # plt.tight_layout()
    # plt.show()

def plot_sweep(save_plots=False, show_plots=False, colors=None):



    if colors == None:
        colors = np.array(["#0079C2", "#00A4E4", "#F7A11A", "#FFC423", "#5D9732", "#8CC63F", "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"])
        use_colors = [0,2,4,9]
        colors = colors[use_colors]

    plant_size = 400
    fig, ax = plt.subplots(1, 1, sharex=True, sharey=True, figsize=(5,3))

    data_no_storage = np.loadtxt("data/lcoh_vs_rating_none_storage_%sMWwindplant.txt" %(plant_size))
    data_pressure_vessel = np.loadtxt("data/lcoh_vs_rating_pressure_vessel_storage_%sMWwindplant.txt" %(plant_size))
    data_salt_cavern = np.loadtxt("data/lcoh_vs_rating_salt_cavern_storage_%sMWwindplant.txt" %(plant_size))
    data_pipe = np.loadtxt("data/lcoh_vs_rating_pipe_storage_%sMWwindplant.txt" %(plant_size))
    # print(indexes[i][0], indexes[i][1])
    # print(ax[indexes[i][0], indexes[i][1]])
    ax.plot(data_pressure_vessel[:,0]/plant_size, data_pressure_vessel[:,1], label="Pressure Vessel")
    ax.plot(data_pipe[:,0]/plant_size, data_pipe[:,1], label="Underground Pipe")
    ax.plot(data_salt_cavern[:,0]/plant_size, data_salt_cavern[:,1], label="Salt Cavern")
    ax.plot(data_no_storage[:,0]/plant_size, data_no_storage[:,1], "--k", label="No Storage")

    ax.scatter(data_pressure_vessel[np.argmin(data_pressure_vessel[:,1]),0]/plant_size, np.min(data_pressure_vessel[:,1]), color="k")
    ax.scatter(data_pipe[np.argmin(data_pipe[:,1]),0]/plant_size, np.min(data_pipe[:,1]), color="k")
    ax.scatter(data_salt_cavern[np.argmin(data_salt_cavern[:,1]),0]/plant_size, np.min(data_salt_cavern[:,1]), color="k")
    ax.scatter(data_no_storage[np.argmin(data_no_storage[:,1]),0]/plant_size, np.min(data_no_storage[:,1]), color="k", label="Optimal ratio")

    ax.legend(frameon=False, loc="best")

    ax.set_xlim([0.2,2.0])
    ax.set_ylim([0,25])

    ax.annotate("%s MW Wind Plant" %(plant_size), (0.6, 1.0))

    print(data_pressure_vessel)
    print(data_salt_cavern)

    ax.set_xlabel("Electrolyzer/Wind Plant Rating Ratio")
    ax.set_ylabel("LCOH ($/kg)")

    plt.tight_layout()

    if save_plots:
        plt.savefig("lcoh_vs_rating_ratio.pdf", transparent=True)
    if show_plots:
        plt.show()

    return 0

def process_design_options(verbose=True, show_plots=False, save_plots=False, colors=None):

    if colors == None:
        colors_nrel = np.array(["#0079C2", "#00A4E4", "#F7A11A", "#FFC423", "#5D9732", "#8CC63F", "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"])
        use_colors = [0, 1, 2, 3, 8, 4, 9]
        colors = colors_nrel[use_colors]
        use_colors = [0, 1, 3, 8, 4]
        colors_opex = colors_nrel[use_colors]

    results_path = "./combined_results/"
    df_metrics = pd.read_csv(results_path+"metrics.csv", index_col=False)
    df_capex = pd.read_csv(results_path+"capex.csv", index_col=False)
    df_opex = pd.read_csv(results_path+"opex.csv", index_col=False)

    # df_opex = df_opex.transpose()
    lcoe_mwh = df_metrics["LCOE [$/kWh]"]*1E3
    df_metrics["LCOE [$/MWh]"] = lcoe_mwh
    
    df_capex = df_capex.rename(columns={'Unnamed: 0': "Component"})
    df_opex = df_opex.rename(columns={'Unnamed: 0': "Component"})
    
    # df_capex = df_capex.transpose()

    # print(df_capex.columns[1])

    # print(df_metrics)
    print("\nCAPEX")

    # df_capex.set_index("Component")
    # df_capex.wind = pd.to_numeric(df_capex.wind)
    # df_capex.age=pd.to_numeric(pf.age)
    df_capex=df_capex.T
    header=df_capex.iloc[0]
    df_capex=df_capex[1:]
    df_capex.columns=header

    df_opex=df_opex.T
    header=df_opex.iloc[0]
    df_opex=df_opex[1:]
    df_opex.columns=header

    # print("\nOPEX")
    # print(df_opex)

    df_capex.set_index("Design")
    df_opex.set_index("Design")

    def group_stuff(df):

        # group all hydrogen transport elements
        columns_to_group = ["h2_pipe_array", "h2_transport_compressor", "h2_transport_pipeline"]
        df["Hydrogen Transport System"] = df[columns_to_group].sum(axis = 1, skipna = True)
        df.drop(columns_to_group, inplace=True, axis=1)

        # group electrolyzer and desal
        columns_to_group = ["desal", "electrolyzer"]
        df["Electrolysis and Desalination"] = df[columns_to_group].sum(axis = 1, skipna = True)
        df.drop(columns_to_group, inplace=True, axis=1)
        
        return df
    
    def rename_stuff(df):

        if "wind" in df.columns:
            wind_name = ["wind", "Wind Farm"]
        elif "wind_and_electrical" in df.columns:
            wind_name = ["wind_and_electrical", "Wind Farm and Electrical System"]

        df = df.rename(columns={wind_name[0]: wind_name[1], "platform": "Equipment Platform", "electrical_export_system": "Electrical Transport System", "h2_storage":"Hydrogen Storage System"})
        
        return df
    
    df_capex = group_stuff(df_capex)
    df_capex = rename_stuff(df_capex)

    df_opex = group_stuff(df_opex)
    df_opex = rename_stuff(df_opex)
    # df_capex.re

    df_capex["Design"] = df_capex["Design"].astype(int)
    df_capex.iloc[:,1:] = df_capex.iloc[:,1:].mul(1E-9)

    df_opex["Design"] = df_opex["Design"].astype(int)
    df_opex.iloc[:,1:] = df_opex.iloc[:,1:].mul(1E-6)
    
    ax = df_capex.plot.bar(x="Design", stacked=True, legend=True, ylabel="CAPEX (B USD)", xlabel="Design Scenario", rot=0, ylim=[0,4], figsize=(8,5), color=colors)
    ax.legend(ncol=2, frameon=False, loc=2)

    # for c in ax.containers:
    #     labels = [str(round(v.get_height(), 2)) + "" if v.get_height() > 0 else '' for v in c]
    #     ax.bar_label(c,
    #                 label_type='center',
    #                 labels = labels,
    #                 size = 14) # add a container object "c" as first argument
    # ax.set(xticks={"rotation": 90})
    print(df_capex)

    plt.tight_layout()

    savepath = "figures/aggregate/"
    if (not os.path.exists(savepath)) and save_plots:
        os.makedirs(savepath)
        
    if save_plots:
        plt.savefig(savepath+"bar-capex.pdf", transparent=True)
    if show_plots:
        plt.show()

    ax = df_opex.plot.bar(x="Design", stacked=True, legend=True, ylabel="OPEX (M USD)", xlabel="Design Scenario", rot=0, ylim=[0,100], figsize=(8,5), color=colors_opex)
    ax.legend(ncol=2, frameon=False, loc=2)

    # for c in ax.containers:
    #     labels = [str(round(v.get_height(), 2)) + "" if v.get_height() > 0 else '' for v in c]
    #     ax.bar_label(c,
    #                 label_type='center',
    #                 labels = labels,
    #                 size = 14) # add a container object "c" as first argument
    # ax.set(xticks={"rotation": 90})
    print(df_opex)
    plt.tight_layout()
    if save_plots:
        plt.savefig(savepath+"bar-opex.pdf", transparent=True)
    if show_plots:
        plt.show()

    # df_metrics.plot.bar(x="Design", y="LCOH [$/kg]", legend=False, rot=0, ylabel="LCOH ($/kg)", xlabel="Design Scenario", figsize=(3,4), color=colors[0])
    # plt.tight_layout()
    # if save_plots:
    #     plt.savefig(savepath+"lcoh.png")
    # if show_plots:
    #     plt.show()

    # df_metrics.plot.bar(x="Design", y="LCOE [$/MWh]", legend=False, rot=0, ylabel="LCOE ($/MWh)", xlabel="Design Scenario", figsize=(3,4), color=colors[0])
    # plt.tight_layout()
    
    # if save_plots:
    #     plt.savefig("figures/aggregate/lcoe.png")
    # if show_plots:
    #     plt.show()
    # print(df_metrics)

    return 0

def table_storage_type_metrics(colors=None):
    if colors == None:
        colors = np.array(["#0079C2", "#00A4E4", "#F7A11A", "#FFC423", "#5D9732", "#8CC63F", "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"])
        use_colors = [0,2,4,9]
        colors = colors[use_colors]

    results_path = "data/"
    df = pd.read_csv(results_path+"storage-types-and-matrics.csv", index_col=False)
    df.drop(columns=["Unnamed: 0"], inplace=True)
    dft = df
    print(dft)
    print(dft.to_latex(index=False, formatters={"Storage Type": str.capitalize},
                  float_format="{:.2f}".format))  
    
def plot_capacity_factors():

    return 0
if __name__ == "__main__":
    save_plots = True
    show_plots = True
    
    plot_policy_storage_design_options(show_plots=show_plots, save_plots=save_plots)
    # plot_lcoh_breakdown()
    # plot_energy_breakdown()
    # plot_design_options(show_plots=show_plots, save_plots=save_plots)
    # plot_orbit_costs(show_plots=show_plots, save_plots=save_plots)
    # plot_orbit_costs_percent(show_plots=show_plots, save_plots=save_plots)
    # plot_sweep(save_plots=save_plots, show_plots=show_plots)
    # process_design_options(save_plots=save_plots, show_plots=show_plots)  
    # table_storage_type_metrics()