from __future__ import annotations

__all__ = ["InputSolution"]


class InputSolution:
    def __init__(self, key: str, value: float):
        self.__key = key
        self.__value = value

    @property
    def key(self) -> str:
        return self.__key

    @property
    def value(self) -> float:
        return self.__value

    @classmethod
    def temperature(cls, value: float) -> InputSolution:
        """
        The value of the input [K]
        """
        return cls("T", value)

    @classmethod
    def concentration(cls, value: float) -> InputSolution:
        """
        The value of the input [%]
        """
        return cls("X", value)

    @classmethod
    def partialPressure(cls, value: float) -> InputSolution:
        """
        The value of the input [Pa]
        """
        return cls("Pv", value)

    @classmethod
    def pressure(cls, value: float) -> InputSolution:
        """
        The value of the input [Pa]
        """
        return cls("P", value)

    @classmethod
    def enthalpy(cls, value: float) -> InputSolution:
        """
        The value of the input [kJ/kg]
        """
        return cls("H", value)

    @classmethod
    def density(cls, value: float) -> InputSolution:
        """
        density(kg/m3)
        """
        return cls("D", value)

    @classmethod
    def specificHeat(cls, value: float) -> InputSolution:
        """
        cp(kJ/kg/K)
        """
        return cls("Cp", value)
