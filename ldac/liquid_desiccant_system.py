from solution import Solution, InputSolution
from pyfluids import HumidAir, InputHumidAir
from CoolProp.CoolProp import PropsSI

__all__ = ["LiquidDesiccantSystem"]


class LiquidDesiccantSystem:
    def __init__(
        self,
        solution_type: Solution,
        inlet_air: HumidAir,
        inlet_solution: Solution,
        air_mass_flow: float,  # kg/s
        solution_mass_flow: float,  # kg/s
        dehumid_eff: float,  # efficiency of dehumidifier (0-1)
    ):
        self.__solution_type = solution_type
        self.__inlet_air = inlet_air
        self.__inlet_solution = inlet_solution
        self.__m_a_in = air_mass_flow
        self.__m_s_in = solution_mass_flow
        self.__dehumid_eff = dehumid_eff

        self.__outlet_air: HumidAir = None
        self.__outlet_solution: Solution = None

        self.__m_da: float = None
        self.__m_a_out: float = None
        self.__m_s_out: float = None

        self.__w_dehumid: float = None
        self.__m_dehumid: float = None

    @property
    def inlet_air(self) -> HumidAir:
        return self.__inlet_air

    @property
    def inlet_solution(self) -> Solution:
        return self.__inlet_solution

    @property
    def outlet_air(self) -> HumidAir:
        if self.__outlet_air is None:
            self.__setOutletAir()
        return self.__outlet_air

    @property
    def outlet_solution(self) -> Solution:
        if self.__outlet_solution is None:
            self.__setOutletSolution()
        return self.__outlet_solution

    @property
    def m_a_in(self):
        return self.__m_a_in

    @property
    def m_a_out(self):
        if self.__m_a_out is None:
            self.__m_a_out = self.__m_a_in - self.dehumid_mass_flow
        return self.__m_a_out

    @property
    def m_a_dry(self):
        if self.__m_da is None:
            self.__m_da = self.__m_a_in / (1 + self.__inlet_air.humidity)
        return self.__m_da

    @property
    def m_s_in(self):
        return self.__m_s_in

    @property
    def m_s_out(self):
        if self.__m_s_out is None:
            self.__m_s_out = self.__m_s_in + self.dehumid_mass_flow
        return self.__m_s_out

    @property
    def dehumid_humidity(self):
        if self.__w_dehumid is None:
            self.__setDehimidProperties()
        return self.__w_dehumid

    @property
    def dehumid_mass_flow(self):
        if self.__m_dehumid is None:
            self.__setDehimidProperties()
        return self.__m_dehumid

    def __setOutletAir(self):
        if self.__w_dehumid is None or self.__m_dehumid is None:
            self.__setDehimidProperties()

        w_a_out = self.__inlet_air.humidity - self.__w_dehumid

        Q_heat = self.__sensibleHeatTransfer()  # kW
        hfg = self.__waterEvapEnthalpy(self.__inlet_solution.temperature)  # kJ/kg
        h_a_out = (
            self.__m_a_in * self.__inlet_air.enthalpy / 1e3
            - self.dehumid_mass_flow * hfg
            - Q_heat
        ) / self.m_a_out

        self.__outlet_air = HumidAir().with_state(
            InputHumidAir.pressure(101325),
            InputHumidAir.enthalpy(h_a_out * 1e3),  # Convert kJ/kg to J/kg
            InputHumidAir.humidity(w_a_out),
        )

    def __setDehimidProperties(self):
        w_a_out = self.__dehumidAirHumidity()
        self.__w_dehumid = self.__inlet_air.humidity - w_a_out
        self.__m_dehumid = self.m_a_dry * self.__w_dehumid

    def __setOutletSolution(self):
        x_out = self.__m_s_in * self.inlet_solution.concentration / self.m_s_out

        Q_heat = self.__sensibleHeatTransfer()  # kW
        hfg = self.__waterEvapEnthalpy(self.__inlet_solution.temperature)  # kJ/kg
        h_s_out = (
            self.__m_s_in * self.__inlet_solution.enthalpy
            + self.dehumid_mass_flow * hfg
            + Q_heat
        ) / self.m_s_out

        self.__outlet_solution = self.__solution_type.withState(
            InputSolution.concentration(x_out), InputSolution.enthalpy(h_s_out)
        )

    def __dehumidAirHumidity(self) -> float:
        w_in = self.__inlet_air.humidity
        w_eq = self.__inlet_solution.humidity
        return w_in - (w_in - w_eq) * self.__dehumid_eff

    def __dehumidAirTemperature(self) -> float:
        T_a_in = self.__inlet_air.temperature
        T_s_in = self.__inlet_solution.temperature.toC
        return T_a_in - (T_a_in - T_s_in) * self.__dehumid_eff

    def __waterEvapEnthalpy(self, T):
        # Calculate the enthalpy of water at given temperature and pressure
        h_f = PropsSI("H", "T", T, "Q", 0, "water") / 1e3  # Convert to kJ/kg
        h_g = PropsSI("H", "T", T, "Q", 1, "water") / 1e3  # Convert to kJ/kg
        return h_g - h_f  # kJ/kg

    def __sensibleHeatTransfer(self):
        T_eq = self.__dehumidAirTemperature()
        cp_air = 1.006  # kJ/kg/K
        return self.m_a_dry * cp_air * (self.__inlet_air.temperature - T_eq)  # kW
