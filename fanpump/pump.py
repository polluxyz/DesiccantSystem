from pyfluids import Fluid
from solution import Solution

__all__ = ["Pump"]


class Pump:
    def __init__(
        self,
        fluid: Fluid | Solution,
        mass_flow: float,
        head: float,
        pump_eff: float = 0.6,
    ):
        self.__fluid: Fluid | Solution = fluid
        self.__mass_flow: float = mass_flow  # m/s
        self.__head: float = head  # m
        self.__g = 9.80665

        self.__work: float | None = None

        self.__pump_eff: float = pump_eff

    @property
    def work(self):
        """[kW]"""
        if self.__work == None:
            self.__setWork()
        return self.__work

    def __setWork(self):
        self.__work = self.__mass_flow * self.__g * self.__head / self.__pump_eff / 1e3
