import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
def lcoh_bar_chart():

    colors = np.array(["#0079C2", "#00A4E4", "#F7A11A", "#FFC423", "#5D9732", "#8CC63F", "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"])
    use_colors = [0,2,4,9]
    colors = colors[use_colors]

    df = pd.read_csv("initial_out.csv")
    df = df.sort_values('LCOH', ascending=False)
    # df.rename(mapper={"Base": "(a) Base", "Min": "(b) Min", "Max": "(c) Max"}, axis=0, inplace=True, errors="raise")
    print(df)
    df_policy_onshore = df[df.Design == "Onshore H2"]
    df_policy_onshore = df.drop(columns=["Design", "Unnamed: 0"])
    df_pivot_policy = pd.pivot_table(df_policy_onshore, values="LCOH", index="Site", columns="Policy")
    df_pivot_policy.sort_values(by="Site", inplace=True)
    df_pivot_policy.plot.bar(stacked=False, rot=45, xlabel="Site", ylabel="LCOH ($/kg)", ylim=[-1,7], color=colors)

    plt.tight_layout()
    plt.savefig("policy-onshore.pdf", transparent=True)

    df_policy_offshore = df[df.Design == "Offshore H2"]
    df_policy_offshore = df.drop(columns=["Design", "Unnamed: 0"])
    df_pivot_policy = pd.pivot_table(df_policy_offshore, values="LCOH", index="Site", columns="Policy")
    df_pivot_policy.sort_values(by="Site", inplace=True)
    df_pivot_policy.plot.bar(stacked=False, rot=45, xlabel="Site", ylabel="LCOH ($/kg)", ylim=[-1,7], color=colors)

    plt.tight_layout()
    plt.savefig("policy-offshore.pdf", transparent=True)

    df_design = df[df.Policy == "Base"]
    # df_design = df.drop(columns=["Policy", "Unnamed: 0"])
    print(df_design)
    df_pivot_design = pd.pivot_table(df_design, values="LCOH", index="Site", columns="Design")
    df_pivot_design.sort_values(by="Site", inplace=True)
    df_pivot_design.plot.bar(stacked=False, rot=45, xlabel="Site", ylabel="LCOH ($/kg)", ylim=[-1,7], color=colors)
    

    plt.tight_layout()
    plt.savefig("design.pdf", transparent=True)
    plt.show()
if __name__ == "__main__":
    lcoh_bar_chart()