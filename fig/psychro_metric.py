import matplotlib.pyplot as plt
import numpy as np
from psychrochart import PsychroChart
import psychrolib

__all__ = ["PsyChart"]

psychrolib.SetUnitSystem(psychrolib.SI)


# === 全域 Matplotlib 設定為 Times New Roman + 刻度、外框、字型大小、粗體 ===
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman"]
plt.rcParams["mathtext.fontset"] = "stix"
plt.rcParams["mathtext.rm"] = "Times New Roman"

plt.rcParams.update(
    {
        "xtick.top": True,
        "ytick.right": True,
        "axes.linewidth": 2,
        "font.weight": "bold",
        "axes.labelweight": "bold",
        "axes.titleweight": "bold",
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "axes.labelsize": 16,
    }
)
# ================================================================


class PsyChart:
    # Pass a dict with the changes wanted:
    def __init__(self):

        self.__points = {}
        self.__num: float = 0

        self.__connectors = []

        custom_style = {
            "figure": {
                # "title": "Psychrometric Chart (sea level)",
                "x_label": "DRY-BULB TEMPERATURE, $°C$",
                "y_label": "HUMIDITY RATIO $w, g_w / kg_{da}$",
                "x_axis": {
                    "color": [0.0, 0.0, 0.0],
                    "linewidth": 1.5,
                    "linestyle": "-",
                },
                "x_axis_labels": {"color": [0.0, 0.0, 0.0], "fontsize": 12},
                "x_axis_ticks": {"direction": "in", "color": [0.0, 0.0, 0.0]},
                "y_axis": {
                    "color": [0.0, 0.0, 0.0],
                    "linewidth": 1.5,
                    "linestyle": "-",
                },
                "y_axis_labels": {"color": [0.0, 0.0, 0.0], "fontsize": 12},
                "y_axis_ticks": {"direction": "in", "color": [0.0, 0.0, 0.0]},
                "partial_axis": False,
                "position": [0.025, 0.075, 0.925, 0.875],
            },
            "limits": {
                "range_temp_c": [20, 60],
                "range_humidity_g_kg": [0, 40],
                "altitude_m": 0,
                "step_temp": 1.0,
            },
            "saturation": {"color": [0.0, 0.0, 0.0], "linewidth": 2, "linestyle": "-"},
            "constant_rh": {
                "color": [0.24, 0.24, 0.24],
                "linewidth": 1,
                "linestyle": "-",
            },
            "constant_v": {
                "color": [0.28, 0.28, 0.28],
                "linewidth": 0.5,
                "linestyle": "-",
            },
            "constant_h": {
                "color": [0.53, 0.53, 0.53],
                "linewidth": 0.75,
                "linestyle": "-",
            },
            "constant_wet_temp": {
                "color": [0.55, 0.55, 0.55],
                "linewidth": 1,
                "linestyle": "--",
            },
            "constant_dry_temp": {
                "color": [0.0, 0.0, 0.0],
                "linewidth": 0.25,
                "linestyle": "-",
            },
            "constant_humidity": {
                "color": [0.0, 0.0, 0.0],
                "linewidth": 0.25,
                "linestyle": "-",
            },
            "chart_params": {
                "with_constant_rh": True,
                "constant_rh_curves": [10, 20, 30, 40, 50, 60, 70, 80, 90],
                "constant_rh_labels": [10, 20, 30],
                "with_constant_v": False,
                "constant_v_step": 0.01,
                "range_vol_m3_kg": [0.78, 0.96],
                "with_constant_h": False,
                "constant_h_step": 10,
                "constant_h_labels": [0],
                "range_h": [20, 170],
                "with_constant_wet_temp": True,
                "constant_wet_temp_step": 1,
                "range_wet_temp": [0, 40],
                "constant_wet_temp_labels": [15, 20, 25, 30],
                "with_constant_dry_temp": True,
                "constant_temp_step": 5,
                "with_constant_humidity": True,
                "constant_humid_step": 2,
                "with_zones": False,
            },
        }

        self.__chart = PsychroChart.create(custom_style)

    def addPoint(self, temp, rh, label="", color="red"):
        key = f"pt{self.__num}"
        self.__points[key] = {
            "label": label,
            "style": {
                "color": color,
                "marker": "o",
                "markersize": 8,
            },
            "xy": (temp, rh),
        }
        self.__num += 1

    def connect(self, start_idx, end_idx, label="", color="red"):
        start_key = f"pt{start_idx}" if isinstance(start_idx, int) else start_idx
        end_key = f"pt{end_idx}" if isinstance(end_idx, int) else end_idx

        self.__connectors.append(
            {
                "start": start_key,
                "end": end_key,
                "label": label,
                "style": {
                    "color": color,
                    "linewidth": 2,
                    "linestyle": "-",
                },
            }
        )

    def plot(self, name: str):
        fig, ax = plt.subplots(figsize=(7, 5))

        self.__chart.plot(ax)

        self.__chart.plot_points_dbt_rh(self.__points, self.__connectors)
        # #
        for idx, (key, pt) in enumerate(self.__points.items(), start=1):
            x, y = pt["xy"]

            w = (
                psychrolib.GetHumRatioFromRelHum(x, y / 100, 101325) * 1000
            )  # e.g. ≈9 g/kg

            print(x, y)
            dx, dy = 1, 1  # 文字偏移量，可自行微調
            ax.text(
                x - dx,
                w + dy,
                str(idx),
                fontsize=12,
                fontweight="bold",
                color="black",
                va="center",
                ha="left",
            )
        self.__chart.plot_legend(
            markerscale=0.25, frameon=False, fontsize=8, labelspacing=1.2
        )

        plt.tight_layout()
        plt.savefig(rf"NTU Thesis/figures/{name}.png", transparent=True)


if __name__ == "__main__":
    chart = PsyChart()
    chart.addPoint(30, 30, "1")
    chart.addPoint(50, 30, "2")
    chart.connect(0, 1)
    chart.plot("test2")

# "exterior": {
#     "label": "Exterior",
#     "style": {"color": [0.855, 0.004, 0.278, 0.8], "marker": "X", "markersize": 15},
#     "xy": (31.06, 32.9),
# },
# "exterior_estimated": {
#     "label": "Estimated (Weather service)",
#     "style": {"color": [0.573, 0.106, 0.318, 0.5], "marker": "x", "markersize": 10},
#     "xy": (36.7, 25.0),
# },
# chart.plot(ax)

# # Append zones:
# zones_conf = {
#     "zones": [
#         {
#             "zone_type": "dbt-rh",
#             "style": {
#                 "edgecolor": [1.0, 0.749, 0.0, 0.8],
#                 "facecolor": [1.0, 0.749, 0.0, 0.2],
#                 "linewidth": 2,
#                 "linestyle": "--",
#             },
#             "points_x": [23, 28],
#             "points_y": [40, 60],
#             "label": "Summer",
#         },
#         {
#             "zone_type": "dbt-rh",
#             "style": {
#                 "edgecolor": [0.498, 0.624, 0.8],
#                 "facecolor": [0.498, 0.624, 1.0, 0.2],
#                 "linewidth": 2,
#                 "linestyle": "--",
#             },
#             "points_x": [18, 23],
#             "points_y": [35, 55],
#             "label": "Winter",
#         },
#     ]
# }
# chart.append_zones(zones_conf)


# # Add Vertical lines
# t_min, t_opt, t_max = 16, 23, 30
# chart.plot_vertical_dry_bulb_temp_line(
#     t_min,
#     {"color": [0.0, 0.125, 0.376], "lw": 2, "ls": ":"},
#     "  TOO COLD ({}°C)".format(t_min),
#     ha="left",
#     loc=0.0,
#     fontsize=14,
# )
# chart.plot_vertical_dry_bulb_temp_line(
#     t_opt, {"color": [0.475, 0.612, 0.075], "lw": 2, "ls": ":"}
# )
# chart.plot_vertical_dry_bulb_temp_line(
#     t_max,
#     {"color": [1.0, 0.0, 0.247], "lw": 2, "ls": ":"},
#     "TOO HOT ({}°C)  ".format(t_max),
#     ha="right",
#     loc=1,
#     reverse=True,
#     fontsize=14,
# )

# Add labelled points and connections between points
