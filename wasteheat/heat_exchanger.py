from pyfluids import HumidAir, InputHumidAir, Fluid, Input
from solution import Solution, InputSolution


__all__ = ["HeatExchanger"]


class HeatExchanger:
    def __init__(
        self,
        inlet_hot: HumidAir | Fluid | Solution,
        m_hot: float,
        inlet_cold: HumidAir | Fluid | Solution,
        m_cold: float,
        efficiency_rate: float = 0.80,
    ):

        self.__inlet_hot = inlet_hot
        self.__inlet_cold = inlet_cold
        self.__m_hot = m_hot
        self.__m_cold = m_cold
        self.__efficiency_rate = efficiency_rate

        self.__cp_hot: float = None
        self.__cp_cold: float = None
        self.__T_hot_in: float = None
        self.__T_cold_in: float = None

        self.__outlet_hot: HumidAir | Fluid | Solution = None
        self.__outlet_cold: HumidAir | Fluid | Solution = None
        self.__Q = None  # Heat transfer rate in kW

    def __get_cp_T(self, fluid):
        """
        Return (cp, T_in) for supported fluid types.
        HumidAir: cp = fluid.Cp_moistair, T = fluid.Tdb
        Fluid: cp = fluid.Cp, T = fluid.T
        Solution: cp = fluid.cp, T = fluid.T
        """
        if isinstance(fluid, HumidAir):
            cp = fluid.specific_heat
            T = fluid.temperature
        elif isinstance(fluid, Fluid):
            cp = fluid.specific_heat
            T = fluid.temperature
        elif isinstance(fluid, Solution):
            cp = fluid.specific_heat * 1e3
            T = fluid.temperature.toC
        else:
            raise TypeError("Unsupported fluid type: {}".format(type(fluid)))
        return cp, T

    @property
    def inlet_hot(self) -> HumidAir | Fluid | Solution:
        return self.__inlet_hot

    @property
    def inlet_cold(self) -> HumidAir | Fluid | Solution:
        return self.__inlet_cold

    @property
    def outlet_hot(self) -> HumidAir | Fluid | Solution:
        if self.__outlet_hot is None:
            self.__setOutletHotCold()
        return self.__outlet_hot

    @property
    def outlet_cold(self) -> HumidAir | Fluid | Solution:
        if self.__outlet_cold is None:
            self.__setOutletHotCold()
        return self.__outlet_cold

    @property
    def m_hot(self) -> float:
        return self.__m_hot

    @property
    def m_cold(self) -> float:
        return self.__m_cold

    @property
    def heat_transfer_rate(self) -> float:
        """Heat transfer rate [kW]."""
        if self.__Q is None:
            self.__setOutletHotCold()
        return self.__Q

    def __setOutletHotCold(self):
        if self.__cp_hot is None or self.__T_hot_in is None:
            self.__cp_hot, self.__T_hot_in = self.__get_cp_T(self.inlet_hot)

        if self.__cp_cold is None or self.__T_cold_in is None:
            self.__cp_cold, self.__T_cold_in = self.__get_cp_T(self.inlet_cold)

        C_h = self.__m_hot * self.__cp_hot
        C_c = self.__m_cold * self.__cp_cold
        C_min = min(C_h, C_c)
        delta_T = self.__T_hot_in - self.__T_cold_in

        self.__Q = self.__efficiency_rate * C_min * delta_T

        T_hot_out = self.__T_hot_in - self.__Q / C_h
        T_cold_out = self.__T_cold_in + self.__Q / C_c

        self.__outlet_hot = self.__outletType(self.inlet_hot, T_hot_out)
        self.__outlet_cold = self.__outletType(self.inlet_cold, T_cold_out)

    def __outletType(
        self, inlet_fluid: HumidAir | Fluid | Solution, T_out
    ) -> HumidAir | Fluid | Solution:
        if isinstance(inlet_fluid, HumidAir):
            outlet_fluid = HumidAir().with_state(
                InputHumidAir.pressure(inlet_fluid.pressure),
                InputHumidAir.temperature(T_out),
                InputHumidAir.humidity(inlet_fluid.humidity),
            )
        elif isinstance(inlet_fluid, Fluid):
            outlet_fluid = inlet_fluid.with_state(
                Input.temperature(T_out), Input.pressure(inlet_fluid.pressure)
            )
        elif isinstance(inlet_fluid, Solution):
            outlet_fluid = inlet_fluid.withState(
                InputSolution.temperature(T_out + 273.15),
                InputSolution.concentration(inlet_fluid.concentration),
            )

        return outlet_fluid
