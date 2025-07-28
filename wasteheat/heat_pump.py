from pyfluids import HumidAir, InputHumidAir, Fluid, Input
from solution import Solution, InputSolution
from .refrigerant import Refrigerant

__all__ = ["HeatPump"]


class HeatPump:
    def __init__(
        self,
        refrigerant: Refrigerant,
        m_ref: float,
        inlet_evap: HumidAir | Fluid | Solution,
        m_evap: float,
        inlet_cond: HumidAir | Fluid | Solution,
        m_cond: float,
    ):
        self.__refrigerant = refrigerant
        self.__inlet_cond = inlet_cond
        self.__inlet_evap = inlet_evap
        self.__m_ref = m_ref
        self.__m_cond = m_cond
        self.__m_evap = m_evap

        self.__h_cond_in: float = None
        self.__h_evap_in: float = None

        self.__outlet_cond: HumidAir | Fluid | Solution = None
        self.__outlet_evap: HumidAir | Fluid | Solution = None
        self.__Q_cond: float = None
        self.__Q_evap: float = None  # Heat transfer rate in kW

        self.__W_comp: float = None  # Work done by compressor in kW

        self.__COP_h: float = None

    def __get_h(self, fluid):
        """
        Return (cp, T_in) for supported fluid types.
        HumidAir: cp = fluid.Cp_moistair, T = fluid.Tdb
        Fluid: cp = fluid.Cp, T = fluid.T
        Solution: cp = fluid.cp, T = fluid.T
        """
        if isinstance(fluid, HumidAir):
            h = fluid.enthalpy / 1e3
        elif isinstance(fluid, Fluid):
            h = fluid.enthalpy / 1e3
        elif isinstance(fluid, Solution):
            h = fluid.enthalpy
        else:
            raise TypeError("Unsupported fluid type: {}".format(type(fluid)))
        return h

    @property
    def inlet_cond(self) -> HumidAir | Fluid | Solution:
        return self.__inlet_cond

    @property
    def inlet_evap(self) -> HumidAir | Fluid | Solution:
        return self.__inlet_evap

    @property
    def outlet_cond(self) -> HumidAir | Fluid | Solution:
        if self.__outlet_cond is None:
            self.__setOutletCond()
        return self.__outlet_cond

    @property
    def outlet_evap(self) -> HumidAir | Fluid | Solution:
        if self.__outlet_evap is None:
            self.__setOutletEvap()
        return self.__outlet_evap

    @property
    def Q_cond(self) -> float:
        """Heat transfer rate [kW]."""
        if self.__Q_cond is None:
            h3 = (
                self.__refrigerant.h3_subcool
                if self.__refrigerant.h3_subcool is not None
                else self.__refrigerant.h3
            )
            self.__Q_cond = self.__m_ref * (self.__refrigerant.h2 - h3)
        return self.__Q_cond

    @property
    def Q_evap(self) -> float:
        """Heat transfer rate [kW]."""
        if self.__Q_evap is None:
            h1 = (
                self.__refrigerant.h1_overheat
                if self.__refrigerant.h1_overheat is not None
                else self.__refrigerant.h1
            )
            self.__Q_evap = self.__m_ref * (h1 - self.__refrigerant.h4)
        return self.__Q_evap

    @property
    def W_comp(self) -> float:
        """Work done by compressor [kW]."""
        if self.__W_comp is None:
            self.__W_comp = self.Q_cond - self.Q_evap
        return self.__W_comp

    @property
    def COP_h(self) -> float:
        if self.__COP_h is None:
            self.__COP_h = self.Q_cond / self.W_comp
        return self.__COP_h

    def __setOutletCond(self):
        if self.__h_cond_in is None:
            self.__h_cond_in = self.__get_h(self.inlet_cond)

        h_out = self.__h_cond_in + self.Q_cond / self.__m_cond

        self.__outlet_cond = self.__outletType(self.inlet_cond, h_out)

    def __setOutletEvap(self):
        if self.__h_evap_in is None:
            self.__h_evap_in = self.__get_h(self.inlet_evap)

        h_out = self.__h_evap_in - self.Q_evap / self.__m_evap

        self.__outlet_evap = self.__outletType(self.inlet_evap, h_out)

    def __outletType(
        self, inlet_fluid: HumidAir | Fluid | Solution, h_out
    ) -> HumidAir | Fluid | Solution:
        if isinstance(inlet_fluid, HumidAir):
            outlet_fluid = HumidAir().with_state(
                InputHumidAir.pressure(inlet_fluid.pressure),
                InputHumidAir.enthalpy(h_out * 1e3),
                InputHumidAir.humidity(inlet_fluid.humidity),
            )
        elif isinstance(inlet_fluid, Fluid):
            outlet_fluid = inlet_fluid.with_state(
                Input.enthalpy(h_out * 1e3), Input.pressure(inlet_fluid.pressure)
            )
        elif isinstance(inlet_fluid, Solution):
            outlet_fluid = inlet_fluid.withState(
                InputSolution.enthalpy(h_out),
                InputSolution.concentration(inlet_fluid.concentration),
            )

        return outlet_fluid
