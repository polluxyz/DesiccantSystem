import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI

__all__ = ["Refrigerant"]


class Refrigerant:
    def __init__(
        self, fluid_name, T_evap_C, T_cond_C, overheat=5, subcool=5, entropy_eff=0.74
    ):
        self.__ref_name = fluid_name
        # Saturation temperature bounds (K)
        self.__T_triple = PropsSI("Ttriple", self.__ref_name)
        self.__T_crit = PropsSI("Tcrit", self.__ref_name)

        self.__T_evap = T_evap_C + 273.15  # Convert to K
        self.__T_cond = T_cond_C + 273.15  # Convert to K

        self.__P_evap: float = None
        self.__P_cond: float = None

        self.__overheat = overheat
        self.__subcool = subcool
        self.__entropy_eff = entropy_eff

        self.__h1: float = None
        self.__h1_overheat: float = None
        self.__s1: float = None
        self.__h2: float = None
        self.__h2s: float = None
        self.__h3: float = None
        self.__h3_subcool: float = None
        self.__h4: float = None

    @property
    def name(self):
        return self.__ref_name

    @property
    def T_evap(self):
        """Evaporator temperature [K]."""
        return self.__T_evap

    @property
    def T_cond(self):
        """Condenser temperature [K]."""
        return self.__T_cond

    @property
    def P_evap(self):
        """Evaporator pressure [Pa]."""
        if self.__P_evap is None:
            self.__cycleStates()
        return self.__P_evap

    @property
    def P_cond(self):
        """Condenser pressure [Pa]."""
        if self.__P_cond is None:
            self.__cycleStates()
        return self.__P_cond

    @property
    def h1(self):
        """[kJ/kg]"""
        if self.__h1 is None:
            self.__cycleStates()
        return self.__h1

    @property
    def h1_overheat(self):
        if self.__h1_overheat is None and self.__overheat:
            self.__cycleStates()
        return self.__h1_overheat

    @property
    def h2(self):
        if self.__h2 is None:
            self.__cycleStates()
        return self.__h2

    @property
    def h2s(self):
        if self.__h2s is None:
            self.__cycleStates()
        return self.__h2s

    @property
    def h3(self):
        if self.__h3 is None:
            self.__cycleStates()
        return self.__h3

    @property
    def h3_subcool(self):
        if self.__h3_subcool is None and self.__subcool:
            self.__cycleStates()
        return self.__h3_subcool

    @property
    def h4(self):
        if self.__h4 is None:
            self.__cycleStates()
        return self.__h4

    def saturationCurve(self, num_points=300):
        """Return saturation enthalpy (kJ/kg) and pressure (MPa) arrays."""
        T_start = 273.15
        T_low = max(self.__T_triple, T_start)  # avoid below triple point
        T_sat = np.linspace(T_low, self.__T_crit, num_points)

        h_f = PropsSI("H", "T", T_sat, "Q", 0, self.__ref_name) / 1000  # liquid
        h_g = PropsSI("H", "T", T_sat, "Q", 1, self.__ref_name) / 1000  # vapor
        p_sat = PropsSI("P", "T", T_sat, "Q", 0, self.__ref_name) / 1e6

        return h_f, h_g, p_sat

    def __cycleStates(self):
        """Compute cycle state enthalpies (kJ/kg) and pressures (MPa)."""
        # Saturation pressures
        self.__P_evap = PropsSI("P", "T", self.__T_evap, "Q", 0, self.__ref_name)
        self.__P_cond = PropsSI("P", "T", self.__T_cond, "Q", 0, self.__ref_name)

        # Point 1
        self.__h1 = PropsSI("H", "T", self.__T_evap, "Q", 1, self.__ref_name) / 1000

        if self.__overheat:
            self.__h1_overheat = (
                PropsSI(
                    "H",
                    "T",
                    self.__T_evap + self.__overheat,
                    "P",
                    self.__P_evap,
                    self.__ref_name,
                )
                / 1000
            )

            mode, val = ("P", self.__P_evap)
        else:
            mode, val = ("Q", 1)

        self.__s1 = PropsSI(
            "S", "T", self.__T_evap + self.__overheat, mode, val, self.__ref_name
        )

        # Point 2
        self.__h2s = (
            PropsSI("H", "P", self.__P_cond, "S", self.__s1, self.__ref_name) / 1000
        )

        if self.__h1_overheat is not None:
            h1 = self.__h1_overheat
        else:
            h1 = self.__h1

        self.__h2 = h1 + (self.__h2s - self.__h1) / self.__entropy_eff

        # Point 3
        self.__h3 = PropsSI("H", "T", self.__T_cond, "Q", 0, self.__ref_name) / 1000

        self.__h3_subcool = (
            PropsSI(
                "H",
                "T",
                self.__T_cond - self.__subcool,
                "P",
                self.__P_cond,
                self.__ref_name,
            )
            / 1000
        )

        # Point 4
        if self.__subcool:
            self.__h4 = self.__h3_subcool
        else:
            self.__h4 = self.__h3

    def __isentropicComp(self, num_iso=50):
        # Isentropic compression path
        P_iso = np.logspace(np.log10(self.P_evap), np.log10(self.P_cond), num_iso)
        h_iso = [
            PropsSI("H", "P", P, "S", self.__s1, self.__ref_name) / 1000 for P in P_iso
        ]

        return P_iso, h_iso

    def plotPH_Diagram(self):

        # === 全域 Matplotlib 設定為 Times New Roman + 刻度、外框、字型大小、粗體 ===
        plt.rcParams["font.family"] = "serif"
        plt.rcParams["font.serif"] = ["Times New Roman"]
        plt.rcParams["mathtext.fontset"] = "stix"
        plt.rcParams["mathtext.rm"] = "Times New Roman"

        plt.rcParams.update(
            {
                "xtick.direction": "in",
                "ytick.direction": "in",
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
        """Plot p-h diagram for the given Refrigerant instance."""
        # Get saturation curves
        h_f, h_g, P_sat = self.saturationCurve()
        # Get cycle data
        P_iso, h_iso = self.__isentropicComp()

        # === 全域設定為 Times New Roman ===
        plt.rcParams["font.family"] = "serif"
        plt.rcParams["font.serif"] = ["Times New Roman"]
        # 如果有數學字型，讓它也用 Times
        plt.rcParams["mathtext.fontset"] = "stix"
        plt.rcParams["mathtext.rm"] = "Times New Roman"
        # ======================================

        plt.rcParams.update(
            {
                # 刻度線向內，並在上／右也顯示
                "xtick.direction": "in",
                "ytick.direction": "in",
                "xtick.top": True,
                "ytick.right": True,
                # 外框（spines）線寬
                "axes.linewidth": 2,
                # 全域字重，已讓所有文字粗體
                "font.weight": "bold",
                "axes.labelweight": "bold",
                "axes.titleweight": "bold",
                # 放大刻度數字與軸標籤
                "xtick.labelsize": 14,  # 刻度數字大小
                "ytick.labelsize": 14,
                "axes.labelsize": 16,  # 兩軸標題大小
            }
        )

        # Plot saturation lines
        # plt.figure(figsize=(6, 5))
        plt.plot(h_f, P_sat, linewidth=1.5, zorder=1, color="black")
        plt.plot(h_g, P_sat, linewidth=1.5, zorder=1, color="black")

        # Refrigeration cycle path
        h1 = self.h1_overheat if self.__overheat else self.h1
        h3 = self.h3_subcool if self.__subcool else self.h3

        h_cycle = [self.h2s, h3, self.h4, h1]
        P_cycle = [
            p / 1e6 for p in (self.P_cond, self.P_cond, self.P_evap, self.P_evap)
        ]
        plt.plot(h_cycle, P_cycle, "-o", color="red", label="Ref. Cycle", linewidth=2)

        # 繪出等熵壓縮線（轉換成 MPa 後畫出來）
        plt.plot(h_iso, np.array(P_iso) / 1e6, linestyle="-", color="red", linewidth=2)

        # Annotate points
        for i, (h, p) in enumerate(zip(h_cycle, P_cycle), start=0):
            label = f"{(i+1)%4+1}"
            plt.annotate(
                label,
                xy=(h, p),  # 參考座標點
                xytext=(-3, 3),  # 文字相對座標點往上 5 points
                textcoords="offset points",
                ha="right",  # 水平置中
                va="bottom",  # 垂直底部對齊
                fontweight="bold",
                fontsize=12,
            )

        plt.axhline(
            self.P_evap / 1e6,
            color="blue",
            linestyle="--",
            label=f"Evap @ {self.__T_evap-273.15:.0f}°C",
            zorder=1,
        )
        plt.axhline(
            self.P_cond / 1e6,
            color="orange",
            linestyle="--",
            label=f"Cond @ {self.__T_cond-273.15:.0f}°C",
            zorder=1,
        )

        # Axes settings
        plt.yscale("log")
        plt.xlabel("Enthalpy (kJ/kg)")
        plt.ylabel("Pressure (MPa)")
        # plt.title(f"{self.__ref_name} p-h Diagram")
        plt.legend(loc="upper left", frameon=False)
        plt.grid(True, which="both", linestyle="--", linewidth=0.5, zorder=0)
        plt.tight_layout()
        plt.savefig(
            "ph_diagram.png",  # 檔名，可含路徑
            dpi=300,  # 解析度
            format="png",  # 檔案格式
            bbox_inches="tight",  # 緊貼邊界，不留多餘空白
            transparent=True,
        )  # 背景透明
