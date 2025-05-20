import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI


class Refrigerant:
    def __init__(self, fluid_name, T_evap_C, T_cond_C, overheat=5, subcool=5):
        self.ref_name = fluid_name
        # Saturation temperature bounds (K)
        self.T_triple = PropsSI("Ttriple", self.ref_name)
        self.T_crit = PropsSI("Tcrit", self.ref_name)

        self.T_evap = T_evap_C + 273.15  # Convert to K
        self.T_cond = T_cond_C + 273.15  # Convert to K

        self.cycleStates(overheat, subcool)

    def saturationCurve(self, num_points=300):
        """Return saturation enthalpy (kJ/kg) and pressure (MPa) arrays."""
        self.T_start = 273.15
        T_low = max(self.T_triple, self.T_start)  # avoid below triple point
        T_sat = np.linspace(T_low, self.T_crit, num_points)

        h_f = PropsSI("H", "T", T_sat, "Q", 0, self.ref_name) / 1000  # liquid
        h_g = PropsSI("H", "T", T_sat, "Q", 1, self.ref_name) / 1000  # vapor
        p_sat = PropsSI("P", "T", T_sat, "Q", 0, self.ref_name) / 1e6

        return h_f, h_g, p_sat

    def cycleStates(self, overheat, subcool):
        """Compute cycle state enthalpies (kJ/kg) and pressures (MPa)."""
        # Saturation pressures
        self.P_evap = PropsSI("P", "T", self.T_evap, "Q", 0, self.ref_name)
        self.P_cond = PropsSI("P", "T", self.T_cond, "Q", 0, self.ref_name)

        # Point 1
        mode, val = ("P", self.P_evap) if overheat else ("Q", 1)
        self.h1 = (
            PropsSI("H", "T", self.T_evap + overheat, mode, val, self.ref_name) / 1000
        )

        self.s1 = PropsSI("S", "T", self.T_evap + overheat, mode, val, self.ref_name)

        # Point 2
        self.h2 = PropsSI("H", "P", self.P_cond, "S", self.s1, self.ref_name) / 1000

        # Point 3
        mode, val = ("P", self.P_cond) if overheat else ("Q", 0)
        self.h3 = (
            PropsSI("H", "T", self.T_cond - subcool, mode, val, self.ref_name) / 1000
        )

        # Point 4
        self.h4 = self.h3

    def __isentropicComp(self, num_iso=50):
        # Isentropic compression path
        P_iso = np.logspace(np.log10(self.P_evap), np.log10(self.P_cond), num_iso)
        h_iso = [
            PropsSI("H", "P", P, "S", self.s1, self.ref_name) / 1000 for P in P_iso
        ]

        return P_iso, h_iso

    def plotPH_Diagram(self):
        """Plot p-h diagram for the given Refrigerant instance."""
        # Get saturation curves
        h_f, h_g, P_sat = self.saturationCurve()
        # Get cycle data
        P_iso, h_iso = self.__isentropicComp()

        # Plot saturation lines
        # plt.figure(figsize=(6, 5))
        plt.plot(h_f, P_sat, linewidth=1.5, zorder=1)
        plt.plot(h_g, P_sat, linewidth=1.5, zorder=1)

        # Refrigeration cycle path
        h_cycle = [self.h2, self.h3, self.h4, self.h1]
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
            label=f"Evap @ {self.T_evap-273.15:.0f}°C",
            zorder=1,
        )
        plt.axhline(
            self.P_cond / 1e6,
            color="orange",
            linestyle="--",
            label=f"Cond @ {self.T_cond-273.15:.0f}°C",
            zorder=1,
        )

        # Axes settings
        plt.yscale("log")
        plt.xlabel("Enthalpy (kJ/kg)")
        plt.ylabel("Pressure (MPa)")
        plt.title(f"{self.ref_name} p-h Diagram")
        plt.legend(loc="upper left")
        plt.grid(True, which="both", linestyle="--", linewidth=0.5, zorder=0)
        plt.tight_layout()
        # plt.show()


if __name__ == "__main__":
    T_evap = 30
    T_cond = 55

    refrigerant = Refrigerant("R134A", T_evap, T_cond)
    refrigerant.plotPH_Diagram()

    refrigerant2 = Refrigerant("R410A", T_evap, T_cond)
    refrigerant2.plotPH_Diagram()

    plt.show()
