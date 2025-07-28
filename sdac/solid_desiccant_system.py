from pyfluids import HumidAir, InputHumidAir
import math
from enum import Enum

__all__ = ["SolidDesiccantSystem"]


class SolidDesiccantSystem:
    def __init__(
        self,
        inlet_air: HumidAir,
        m_air: float,
        moisture: float = 0,
        func_percentage: float = 0.5,
    ):
        self.__percentage: float = (
            func_percentage  # percantage of adsorption or regeneration part
        )

        self.__EMC: float = None  # Equilibrium Moisture Content
        self.__adsorption_rate: float = None  # kg/s

        self.__previous_moisture: float = moisture
        self.__current_moisture: float = None

        self.__inlet_air: HumidAir = inlet_air
        self.__outlet_air: HumidAir = None

        self.__m_air: float = m_air

        self.__density: float = 500  # kg/m3
        self.__radius: float = 0.4
        self.__width: float = 0.4
        self.__velocity: float = self.__radius**2 * math.pi * self.__width
        self.__mass: float = self.__density * self.__velocity

        self.__q: float = None

    @property
    def inlet_air(self) -> HumidAir:
        return self.__inlet_air

    @property
    def outlet_air(self) -> HumidAir:
        if self.__outlet_air is None:
            self.__setOutletAir()
        return self.__outlet_air

    @property
    def EMC(self) -> float:
        if self.__EMC is None:
            self.__getEMC()
        return self.__EMC

    @property
    def q(self) -> float:
        if self.__q is None:
            self.__getEMC()
        return self.__q

    @property
    def adsorption_rate(self) -> float:
        if self.__adsorption_rate is None:
            self.__getAdsorptionRate()
        return self.__adsorption_rate

    @property
    def current_moisture(self) -> float:
        if self.__current_moisture is None:
            self.__current_moisture = (
                self.__previous_moisture + self.adsorption_rate / self.__mass
            )
        return self.__current_moisture

    def __getEMC(self):
        air = self.__inlet_air

        m0 = 0.39  # kg water per kg adsorbent
        a = 1.192
        delta_Q_kJ_per_kg = 1469  # kJ per kg of H2O
        M_H2O = 0.018015  # kg/mol
        b = 1.1178e-4

        R = 8.314462618  # J/(mol·K)

        T = air.temperature + 273.15  # K

        # 把 ΔQ 轉成 J/mol
        delta_Q_J_per_mol = delta_Q_kJ_per_kg * 1e3 * M_H2O

        # 平衡常數 K
        K = b * math.exp(a * delta_Q_J_per_mol / (R * T))

        # 相對壓力 RH
        RH = air.relative_humidity / 100

        # S 形等溫線
        q = K * RH**a / (1 + (K - 1) * RH**a)

        # 平衡含水量 (kg H2O per kg adsorbent)
        self.__EMC = m0 * q

        self.__q = q

    def __getAdsorptionRate(self):
        air = self.__inlet_air

        a1 = 1.05e-11  # m2/s
        a2 = 28299  # J/mol
        d = 1.5e-6  # m

        R = 8.314462618  # J/(mol·K)

        T = air.temperature + 273.15  # K

        Ds = a1 * math.exp(-a2 / (R * T))

        self.__adsorption_rate = (
            (60 / d**2)
            * Ds
            * (self.EMC - self.__previous_moisture)
            * self.__mass
            * self.__percentage
        )

    def __setOutletAir(self):
        delta_enthalpy = 53  # kJ/mol
        water_molar_mass = 0.01801524  # kg/mol

        w_out = self.__inlet_air.humidity - min(
            self.adsorption_rate / self.__m_air, self.__inlet_air.humidity
        )

        h_out = (
            self.__inlet_air.enthalpy
            + self.adsorption_rate * delta_enthalpy
            # / water_molar_mass
            * 1e3 / self.__m_air
        )

        self.__outlet_air = HumidAir().with_state(
            InputHumidAir.pressure(101325),
            InputHumidAir.humidity(w_out),
            InputHumidAir.enthalpy(h_out),
        )

    def setOutletAir(self, air: HumidAir):
        self.__outlet_air = air
