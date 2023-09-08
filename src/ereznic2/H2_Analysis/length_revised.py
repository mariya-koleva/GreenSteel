import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


class MVAC_vs_Pipeline:
    """Please refer to diagrams in optimal_placement.ppt for visualizations of the layouts."""

    def __init__(self, _plot=True, state=None):
        self.parent_path = os.path.abspath("")
        if state is None:
            self.states = ["MN", "IN", "TX", "MS", "IA"]
        self.plot = _plot
        self.voltage = 35e3  # stepped up voltage in the turbine
        self.layout_info = {}
        self.total_cost_ac_line = {}
        self.grid_idx = ["_Grid", ""]
        for state in self.states:
            for grid in self.grid_idx:
                floris_dir = self.parent_path + "/floris_input_files_new/"
                turbine_file = (
                    floris_dir + "floris_input" + "_" + state + grid + ".yaml"
                )
                with open(turbine_file, "r") as f:
                    floris_config = yaml.load(f, Loader=yaml.Loader)
                self.layout_info[f"layout_x_{state}_{grid}"] = floris_config["farm"][
                    "layout_x"
                ]
                self.layout_info[f"layout_y_{state}_{grid}"] = floris_config["farm"][
                    "layout_y"
                ]
                if self.plot:
                    plt.figure()
                    plt.plot(
                        self.layout_info[f"layout_x_{state}_{grid}"],
                        self.layout_info[f"layout_y_{state}_{grid}"],
                        ".",
                    )
                    plt.plot(
                        [max(self.layout_info[f"layout_x_{state}_{grid}"]) / 2],
                        [max(self.layout_info[f"layout_y_{state}_{grid}"]) / 2],
                        "x",
                    )
                    plt.title(
                        f"Site: {state}{grid}\n"
                        f"Number of turbines:{len(floris_config['farm']['layout_x'])}"
                    )
                    plt.savefig(f"layout_plots/{state}{grid}")
                self.layout_info[f"size_X_{state}_{grid}"] = len(
                    [i for i in self.layout_info[f"layout_y_{state}_{grid}"] if i == 0]
                )
                self.layout_info[f"size_Y_{state}_{grid}"] = (
                    len(self.layout_info[f"layout_y_{state}_{grid}"])
                    / self.layout_info[f"size_X_{state}_{grid}"]
                )
                self.layout_info[f"electrolyzer_x_{state}_{grid}"] = (
                    max(self.layout_info[f"layout_x_{state}_{grid}"]) / 2
                )
                self.layout_info[f"electrolyzer_y_{state}_{grid}"] = (
                    max(self.layout_info[f"layout_y_{state}_{grid}"]) / 2
                )
                self.layout_info[f"X_spacing_{state}_{grid}"] = self.layout_info[
                    f"layout_x_{state}_{grid}"
                ][1]
                self.layout_info[f"Y_spacing_{state}_{grid}"] = self.layout_info[
                    f"layout_y_{state}_{grid}"
                ][int(self.layout_info[f"size_X_{state}_{grid}"])]
                self.layout_info[f"max_X_{state}_{grid}"] = max(
                    self.layout_info[f"layout_x_{state}_{grid}"]
                )
                self.layout_info[f"max_Y_{state}_{grid}"] = max(
                    self.layout_info[f"layout_y_{state}_{grid}"]
                )
                self.layout_info[f"turbine_rating_{state}_{grid}"] = floris_config[
                    "farm"
                ]["turbine_type"][0]

        self.cables_ampacity = {
            "AWG 1/0": 150,
            "AWG 4/0": 230,
            "MCM 500": 320,
            "MCM 1000": 455,
            "MCM 1250": 495,
        }
        self.cables_cost_per_km = {
            "AWG 1/0": 61115.1602528554,
            "AWG 4/0": 72334.3683802817,
            "MCM 500": 96358.26769213431,
            "MCM 1000": 104330.7086713996,
            "MCM 1250": 115964.28690974298,
        }

        self.resistivity_ohm_per_kft = {
            "AWG 1/0": 0.12,
            "AWG 4/0": 0.25,
            "MCM 500": 0.02,
            "MCM 1000": 0.01,
            "MCM 1250": 0.009,
        }

    def total_length_ac_line(self, turb="4MW"):
        """Computes the total length of the AC line from turbines to
        the electrolyzer"""

        print("--------------------------------------------")
        print(f"Computing ac line length for {turb} turbine..")
        print("--------------------------------------------")

        # Find the number of rows
        self.number_of_rows = self.layout_info["size_Y_" + turb]
        self.number_of_cols = self.layout_info["size_X_" + turb]

        if self.number_of_cols % 2 == 0:
            # Even
            total_length = (
                self.layout_info["max_X_" + turb]
                - self.layout_info["X_spacing_" + turb]
            )
            # All the rows
            total_length = total_length * self.layout_info["size_Y_" + turb]

            # One column
            col = (
                self.layout_info["max_Y_" + turb]
                - 2 * self.layout_info["Y_spacing_" + turb]
            )

            # All the columns
            total_length = total_length + 2 * col

            # Column in the middle:
            total_length = total_length + self.layout_info["max_Y_" + turb]

            # Diagonals in the center
            # One diag length:
            diag = np.sqrt(
                (self.layout_info["X_spacing_" + turb]) ** 2
                + (2 * self.layout_info["Y_spacing_" + turb]) ** 2
            )
            total_length = total_length + 2 * diag

            # Finally, the row at the center
            total_length = total_length + 2 * self.layout_info["X_spacing_" + turb]

        else:
            # Odd
            # One row
            total_length = (
                self.layout_info["max_X_" + turb]
                - self.layout_info["X_spacing_" + turb]
            )
            # All the rows
            total_length = total_length * self.layout_info["size_Y_" + turb]

            # One column
            col = (
                self.layout_info["max_Y_" + turb]
                - 2 * self.layout_info["Y_spacing_" + turb]
            )

            # All the columns
            total_length = total_length + 2 * col

            # Diagonals in the center
            # One diag length:
            diag = np.sqrt(
                (2 * self.layout_info["X_spacing_" + turb]) ** 2
                + (2 * self.layout_info["Y_spacing_" + turb]) ** 2
            )
            total_length = total_length + 2 * diag

            # Finally, the row at the center
            total_length = total_length + self.layout_info["X_spacing_" + turb]

        print("Total length of cable in m:", total_length)
        return total_length * 1e-3

    def cost_calculations_ac_line_naive_bounds(self, turb="4MW"):
        """Just multiplying the total length of the cable by $/m"""

        min_cost_dollar_per_km = 61474.89
        max_cost_dollar_per_km = 116599.08

        length = self.total_length_ac_line(turb=turb)

        return (
            min_cost_dollar_per_km * length * 1e-6,
            max_cost_dollar_per_km * length * 1e-6,
        )

    def cost_calculations_with_substation(self):
        pass

    def cost_calculations_pipeline(self, turb="4MW"):
        """"""

    def get_pipe_info(self):

        """Dataframe with pipe info"""
        df_all = pd.DataFrame()
        for turb in self.turbine_models:
            # Find the number of rows
            self.number_of_rows = self.layout_info["size_Y_" + turb]
            self.number_of_cols = self.layout_info["size_X_" + turb]
            df = pd.DataFrame()
            if self.number_of_cols % 2 == 0:
                # Row length:
                row_length = self.layout_info["X_spacing_" + turb]
                col_length = self.layout_info["Y_spacing_" + turb]
                diag_length = (
                    np.sqrt(
                        (2 * self.layout_info["X_spacing_" + turb]) ** 2
                        + (2 * self.layout_info["Y_spacing_" + turb]) ** 2
                    )
                    / 2
                )
                row_center_length = self.layout_info["X_spacing_" + turb] / 2

                # one row
                row_length_number = self.layout_info["size_X_" + turb] - 2
                row_length_number = (
                    row_length_number * self.layout_info["size_Y_" + turb]
                )

                col_length_number = self.layout_info["size_Y_" + turb] - 3
                col_length_number = col_length_number * 2

                diag_length_number = 4

                row_center_length_number = 2

                df["Length of Pipe (m)"] = [
                    row_length,
                    col_length,
                    diag_length,
                    row_center_length,
                ]
                df["Number of such pipes needed"] = [
                    row_length_number,
                    col_length_number,
                    diag_length_number,
                    row_center_length_number,
                ]
                df["Site"] = "lbw_" + turb

            else:

                row_length = self.layout_info["X_spacing_" + turb]
                col_length = self.layout_info["Y_spacing_" + turb]
                diag_length = diag_length = np.sqrt(
                    (self.layout_info["X_spacing_" + turb]) ** 2
                    + (self.layout_info["Y_spacing_" + turb]) ** 2
                )

                row_length_number = self.layout_info["size_X_" + turb] - 3
                row_length_number = (
                    row_length_number * self.layout_info["size_Y_" + turb]
                )
                row_length_number = row_length_number + 2

                col_length_number = self.layout_info["size_Y_" + turb] - 3
                col_length_number = col_length_number * 2
                col_length_number = (
                    col_length_number + self.layout_info["size_Y_" + turb] - 1
                )

                diag_length_number = 4
                df["Length of Pipe (m)"] = [
                    row_length,
                    col_length,
                    diag_length,
                ]
                df["Number of such pipes needed"] = [
                    row_length_number,
                    col_length_number,
                    diag_length_number,
                ]
                df["Site"] = "lbw_" + turb
            df_all = pd.concat([df_all, df], ignore_index=True)

        return df_all

    def get_pipe_arm_lengths(self):

        """Dataframe with"""
        df_all = pd.DataFrame()
        for state in self.states:
            for grid in self.grid_idx:
                print(f"Estimating {state} and {grid}")
                # Find the number of rows
                df = pd.DataFrame()
                if self.layout_info[f"size_X_{state}_{grid}"] % 2 == 0:
                    # Row length:
                    arm_length_1 = (
                        self.layout_info[f"max_X_{state}_{grid}"]
                        - self.layout_info[f"X_spacing_{state}_{grid}"]
                    ) / 2

                    # one row

                    if self.layout_info[f"size_Y_{state}_{grid}"] % 2 == 0:

                        arm_length_1_number = (
                            self.layout_info[f"size_Y_{state}_{grid}"] * 2
                        )
                        arm_length_2_number = 4
                        arm_length_3_number = 0
                        number_of_turbs_arm_1 = (
                            self.layout_info[f"size_X_{state}_{grid}"] / 2
                        )
                        number_of_turbs_arm_2 = (
                            self.layout_info[f"size_X_{state}_{grid}"]
                            * self.layout_info[f"size_Y_{state}_{grid}"]
                            / 4
                        )
                        number_of_turbs_arm_3 = 0

                        diag_length = (
                            np.sqrt(
                                (self.layout_info[f"X_spacing_{state}_{grid}"]) ** 2
                                + (self.layout_info[f"Y_spacing_{state}_{grid}"]) ** 2
                            )
                            / 2
                        )
                        arm_length_2 = (
                            self.layout_info[f"max_Y_{state}_{grid}"]
                            - self.layout_info[f"Y_spacing_{state}_{grid}"]
                        ) / 2
                        arm_length_2 = arm_length_2 + diag_length
                        arm_length_3 = 0

                    else:
                        arm_length_1_number = (
                            self.layout_info[f"size_Y_{state}_{grid}"] - 1
                        ) * 2
                        arm_length_2_number = 4
                        arm_length_3_number = 2
                        number_of_turbs_arm_1 = (
                            self.layout_info[f"size_X_{state}_{grid}"] / 2
                        )
                        number_of_turbs_arm_2 = (
                            self.layout_info[f"size_X_{state}_{grid}"]
                            / 2
                            * (self.layout_info[f"size_Y_{state}_{grid}"] - 1)
                            / 2
                        )
                        number_of_turbs_arm_3 = (
                            self.layout_info[f"size_X_{state}_{grid}"] / 2
                        )
                        diag_length = (
                            np.sqrt(
                                (self.layout_info[f"X_spacing_{state}_{grid}"]) ** 2
                                + (2 * self.layout_info[f"Y_spacing_{state}_{grid}"])
                                ** 2
                            )
                            / 2
                        )
                        arm_length_2 = (
                            self.layout_info[f"max_Y_{state}_{grid}"]
                            - 2 * self.layout_info[f"Y_spacing_{state}_{grid}"]
                        ) / 2
                        arm_length_2 = arm_length_2 + diag_length
                        row_center_length = (
                            self.layout_info[f"X_spacing_{state}_{grid}"] / 2
                        )
                        arm_length_3 = arm_length_1 + row_center_length

                    df["Length of Pipe in Arm (m)"] = [
                        arm_length_1,
                        arm_length_2,
                        arm_length_3,
                    ]
                    df["Number of such pipes needed"] = [
                        arm_length_1_number,
                        arm_length_2_number,
                        arm_length_3_number,
                    ]
                    df["Number of turbines in each pipe"] = [
                        number_of_turbs_arm_1,
                        number_of_turbs_arm_2,
                        number_of_turbs_arm_3,
                    ]
                    df["Site"] = f"{state}{grid}"

                else:
                    arm_length_1 = (
                        self.layout_info[f"max_X_{state}_{grid}"]
                        - 2 * self.layout_info[f"X_spacing_{state}_{grid}"]
                    ) / 2  # c

                    if self.layout_info[f"size_Y_{state}_{grid}"] % 2 == 0:

                        # Changed Sept 5 2023. Bug in diag lengths.

                        arm_length_1_number = (
                            self.layout_info[f"size_Y_{state}_{grid}"] * 2
                        )  #
                        arm_length_2_number = 4
                        arm_length_3_number = 2
                        arm_length_4_number = 0
                        number_of_turbs_arm_1 = (
                            self.layout_info[f"size_X_{state}_{grid}"] - 1
                        ) / 2
                        number_of_turbs_arm_2 = (
                            self.layout_info[f"size_X_{state}_{grid}"]
                            * (self.layout_info[f"size_Y_{state}_{grid}"] - 1)
                            / 4
                        )
                        number_of_turbs_arm_3 = (
                            self.layout_info[f"size_Y_{state}_{grid}"] / 2
                        )

                        number_of_turbs_arm_4 = 0

                        diag_length = (
                            np.sqrt(
                                (self.layout_info[f"X_spacing_{state}_{grid}"]) ** 2
                                + ((self.layout_info[f"Y_spacing_{state}_{grid}"]) / 2)
                                ** 2
                            )
                            / 2
                        )
                        arm_length_2 = (
                            self.layout_info[f"max_Y_{state}_{grid}"]
                            - self.layout_info[f"Y_spacing_{state}_{grid}"]
                        ) / 2
                        arm_length_2 = arm_length_2 + diag_length
                        arm_length_3 = (
                            arm_length_2
                            + self.layout_info[f"Y_spacing_{state}_{grid}"] / 2
                        )

                        arm_length_4 = 0

                    else:
                        arm_length_1_number = (
                            self.layout_info[f"size_Y_{state}_{grid}"] - 1
                        ) * 2
                        arm_length_2_number = 4
                        arm_length_3_number = 2
                        arm_length_4_number = 2
                        number_of_turbs_arm_1 = (
                            self.layout_info[f"size_X_{state}_{grid}"] - 1
                        ) / 2
                        number_of_turbs_arm_2 = (
                            number_of_turbs_arm_1
                            * (self.layout_info[f"size_Y_{state}_{grid}"] - 1)
                            / 2
                        )
                        number_of_turbs_arm_3 = (
                            self.layout_info[f"size_X_{state}_{grid}"] - 1
                        ) / 2
                        number_of_turbs_arm_4 = (
                            self.layout_info[f"size_Y_{state}_{grid}"] - 1
                        ) / 2
                        diag_length = np.sqrt(
                            (self.layout_info[f"X_spacing_{state}_{grid}"]) ** 2
                            + (self.layout_info[f"Y_spacing_{state}_{grid}"]) ** 2
                        )
                        arm_length_2 = (
                            self.layout_info[f"max_Y_{state}_{grid}"]
                            - 2 * self.layout_info[f"Y_spacing_{state}_{grid}"]
                        ) / 2
                        arm_length_2 = arm_length_2 + diag_length
                        row_center_length = self.layout_info[
                            f"X_spacing_{state}_{grid}"
                        ]
                        arm_length_3 = arm_length_1 + row_center_length
                        arm_length_4 = (
                            self.layout_info[f"max_Y_{state}_{grid}"]
                            - 2 * self.layout_info[f"Y_spacing_{state}_{grid}"]
                        ) / 2 + self.layout_info[f"Y_spacing_{state}_{grid}"]

                    df["Length of Pipe in Arm (m)"] = [
                        arm_length_1,
                        arm_length_2,
                        arm_length_3,
                        arm_length_4,
                    ]
                    df["Number of such pipes needed"] = [
                        arm_length_1_number,
                        arm_length_2_number,
                        arm_length_3_number,
                        arm_length_4_number,
                    ]
                    df["Number of turbines in each pipe"] = [
                        number_of_turbs_arm_1,
                        number_of_turbs_arm_2,
                        number_of_turbs_arm_3,
                        number_of_turbs_arm_4,
                    ]
                    df["Site"] = f"{state}{grid}"

                df_all = pd.concat([df_all, df], ignore_index=True)

        return df_all

    def compute_ampacity(self, turbine_list=[], voltage=None):
        self.currents = {}
        if voltage is not None:
            self.voltage = voltage
        if isinstance(turbine_list, str):
            print("----------Finding ampacity of only one turbine-------------")
            self.currents[f"{state}{grid}_lbw"] = (
                int(turbine_list[0]) * 1e6 / (self.voltage * np.sqrt(3))
            )
        elif isinstance(turbine_list, list):
            for state in self.states:
                for grid in self.grid_idx:

                    print(
                        f"------------------Finding ampacity of {state}{grid}-------------------"
                    )
                    self.currents[f"{state}_{grid}"] = (
                        int(self.layout_info[f"turbine_rating_{state}_{grid}"][4])
                        * 1e6
                        / (self.voltage * np.sqrt(3))
                    )
                    # print(f"Current along {turb} is {self.currents[f'{turb}_lbw']}")
        else:
            raise TypeError("Type not recognized.")

    def compute_costs(self, turbine_list=None):

        for state in self.states:
            for grid in self.grid_idx:

                print(f"Finding material costs for {state}{grid} farm")

                if self.layout_info[f"size_X_{state}_{grid}"] % 2 == 0:
                    number_of_turbines_in_one_string = (
                        self.layout_info[f"size_X_{state}_{grid}"] / 2
                    )
                    number_of_cables_in_one_string = int(
                        number_of_turbines_in_one_string - 1
                    )

                    # this is for rows (1)
                    cumulative_currents_in_string = [
                        (i + 1) * self.currents[f"{state}_{grid}"]
                        for i in range(number_of_cables_in_one_string)
                    ]
                    self.best_cable_in_string = []
                    cost_per_string = 0
                    for current in cumulative_currents_in_string:
                        best_cable = min(
                            self.cables_ampacity,
                            key=lambda x: abs(current - self.cables_ampacity[x]),
                        )
                        self.best_cable_in_string.append(best_cable)
                        cost_per_string = (
                            cost_per_string
                            + self.cables_cost_per_km[best_cable]
                            * self.layout_info[f"X_spacing_{state}_{grid}"]
                            * 1e-3
                        )

                    number_of_row_strings = (
                        self.layout_info[f"size_Y_{state}_{grid}"] * 2
                    )
                    total_cost_rows = number_of_row_strings * cost_per_string
                    # print(total_cost_rows)

                    # this is for columns going to the electrolyzer (arm 2)

                    # Even number of columns
                    if self.layout_info[f"size_Y_{state}_{grid}"] % 2 == 0:

                        number_of_turbines_in_one_string_col = (
                            self.layout_info[f"size_X_{state}_{grid}"] / 2
                        )
                        number_of_cables_in_one_string_col = int(
                            number_of_turbines_in_one_string_col
                        )

                    else:
                        number_of_turbines_in_one_string_col = (
                            self.layout_info[f"size_X_{state}_{grid}"] - 1
                        ) / 2
                        number_of_cables_in_one_string_col = int(
                            number_of_turbines_in_one_string_col
                        )
                    number_of_col_strings = 4
                    cumulative_currents_in_string_col = [
                        (i + 1)
                        * self.currents[f"{state}_{grid}"]
                        * number_of_cables_in_one_string
                        for i in range((number_of_cables_in_one_string_col))
                    ]
                    self.best_cable_in_string_col = []
                    cost_per_string = 0
                    for current in cumulative_currents_in_string_col:
                        best_cable = min(
                            self.cables_ampacity,
                            key=lambda x: abs(current - self.cables_ampacity[x]),
                        )
                        self.best_cable_in_string_col.append(best_cable)
                        if current == cumulative_currents_in_string_col[-1]:
                            if self.layout_info[f"size_Y_{state}_{grid}"] % 2 == 0:
                                length_of_cable = self.layout_info[
                                    f"Y_spacing_{state}_{grid}"
                                ] / (2)
                            else:
                                length_of_cable = self.layout_info[
                                    f"Y_spacing_{state}_{grid}"
                                ] / np.sqrt(2)
                        else:
                            length_of_cable = self.layout_info[
                                f"Y_spacing_{state}_{grid}"
                            ]

                        cost_per_string = (
                            cost_per_string
                            + self.cables_cost_per_km[best_cable]
                            * length_of_cable
                            * 1e-3
                        )
                    total_cost_cols = cost_per_string * number_of_col_strings

                    # TODO: There's a tiny chunk in the middle row I havent accounted for.
                    # For 3 phase
                    self.total_cost_ac_line[f"{state}{grid}"] = [
                        3 * (total_cost_rows + total_cost_cols)
                    ]

                else:

                    number_of_turbines_in_one_string = (
                        self.layout_info[f"size_X_{state}_{grid}"] - 1
                    ) / 2
                    number_of_cables_in_one_string = int(
                        number_of_turbines_in_one_string - 1
                    )

                    # this is for rows (1)
                    cumulative_currents_in_string = [
                        (i + 1) * self.currents[f"{state}_{grid}"]
                        for i in range(number_of_cables_in_one_string)
                    ]
                    best_cable_in_string = []
                    cost_per_string = 0
                    for current in cumulative_currents_in_string:
                        best_cable = min(
                            self.cables_ampacity,
                            key=lambda x: abs(current - self.cables_ampacity[x]),
                        )
                        best_cable_in_string.append(best_cable)
                        cost_per_string = (
                            cost_per_string
                            + self.cables_cost_per_km[best_cable]
                            * self.layout_info[f"X_spacing_{state}_{grid}"]
                            * 1e-3
                        )
                    number_of_row_strings = (
                        self.layout_info[f"size_Y_{state}_{grid}"] * 2
                    )
                    total_cost_rows = number_of_row_strings * cost_per_string

                    # This is for columns going to the electrolyzer (arm 2)

                    # Even number of columns
                    if self.layout_info[f"size_Y_{state}_{grid}"] % 2 == 0:

                        number_of_turbines_in_one_string_col = (
                            self.layout_info[f"size_X_{state}_{grid}"] - 1
                        ) / 2
                        number_of_cables_in_one_string_col = int(
                            number_of_turbines_in_one_string_col
                        )

                    else:
                        number_of_turbines_in_one_string_col = (
                            self.layout_info[f"size_X_{state}_{grid}"] - 1
                        ) / 2
                        number_of_cables_in_one_string_col = int(
                            number_of_turbines_in_one_string_col
                        )
                    number_of_col_strings = 6
                    cumulative_currents_in_string_col = self.currents[
                        f"{state}_{grid}"
                    ] = [
                        i
                        * self.currents[f"{state}_{grid}"]
                        * number_of_cables_in_one_string
                        for i in range(number_of_cables_in_one_string_col)
                    ]
                    best_cable_in_string = []
                    cost_per_string = 0
                    for current in cumulative_currents_in_string_col:
                        best_cable = min(
                            self.cables_ampacity,
                            key=lambda x: abs(current - self.cables_ampacity[x]),
                        )
                        best_cable_in_string.append(best_cable)
                        if current == cumulative_currents_in_string_col[-1]:
                            if self.layout_info[f"size_Y_{state}_{grid}"] % 2 == 0:
                                length_of_cable = self.layout_info[
                                    f"Y_spacing_{state}_{grid}"
                                ] * np.sqrt(2)
                            else:
                                length_of_cable = self.layout_info[
                                    f"Y_spacing_{state}_{grid}"
                                ] * np.sqrt(2)
                        else:
                            length_of_cable = self.layout_info[
                                f"Y_spacing_{state}_{grid}"
                            ]

                        cost_per_string = (
                            cost_per_string
                            + self.cables_cost_per_km[best_cable]
                            * length_of_cable
                            * 1e-3
                        )
                    total_cost_cols = cost_per_string * number_of_col_strings

                    # TODO: Theres a tiny chunk in the middle row I havent accounted for.
                    self.total_cost_ac_line[f"{state}{grid}"] = [
                        3 * (total_cost_rows + total_cost_cols)
                    ]

        return self.total_cost_ac_line

    def pipeline_vs_cable_costs(self):
        df = pd.DataFrame()
        d = self.compute_costs()
        print(d)

        return pd.DataFrame.from_dict(d)

    def compute_i2r_loss(self, farm="4MW"):

        """Compute bounds on I^2R loss."""

        lowest_ampacity = [
            (key, value)
            for key, value in self.cables_ampacity.items()
            if self.cables_ampacity[key] == min(self.cables_ampacity.values())
        ]
        highest_ampacity = [
            (key, value)
            for key, value in self.cables_ampacity.items()
            if self.cables_ampacity[key] == max(self.cables_ampacity.values())
        ]
        kft_tp_mile = 0.1894
        km_to_mile = 0.6214
        length = self.total_length_ac_line(turb=farm)
        power_loss_low = (
            np.sqrt(3)
            * lowest_ampacity[0][1] ** 2
            * self.resistivity_ohm_per_kft[lowest_ampacity[0][0]]
            / kft_tp_mile
            * length
            * km_to_mile
        )
        power_loss_high = (
            np.sqrt(3)
            * highest_ampacity[0][1] ** 2
            * self.resistivity_ohm_per_kft[highest_ampacity[0][0]]
            / kft_tp_mile
            * length
            * km_to_mile
        )

        return power_loss_high, power_loss_low
