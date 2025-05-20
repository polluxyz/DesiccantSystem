from __future__ import annotations

from ..input import *
from .solution_list import SolutionList
from ..unit_converter import *


__all__ = ["Solution"]


class Solution:
    def __init__(self, name: str | SolutionList):
        # judge the input type str or SolutionList
        if isinstance(name, str):
            try:
                name = name.lower()
                enum = SolutionList[name]
            except KeyError:
                raise ValueError(f"Unknown solution type: {name!r}")
        elif isinstance(name, SolutionList):
            enum = name
        else:
            raise TypeError("name must be a str or SolutionList")

        self.__sol_list = enum
        self.__sol_type = enum.sol_cls

        """Base class of fluids."""
        self._inputs: list[InputSolution] = []
        self.__concentration: float | None = None
        self.__density: float | None = None
        self.__enthalpy: float | None = None
        self.__humidity: float | None = None
        self.__max_pressure: float | None = None
        self.__max_temperature: float | None = None
        self.__min_pressure: float | None = None
        self.__min_temperature: float | None = None
        self.__partial_pressure: float | None = None
        self.__pressure: float | None = 101325
        self.__specific_heat: float | None = None
        self.__temperature: float | None = None

    @property
    def concentration(self) -> float:
        """Concentration [%]."""
        if self.__concentration is None:
            self.__concentration = self._keyedOutputs("X")
        return self.__concentration

    @property
    def density(self) -> float:
        """Density [kg/m3]."""
        if self.__density is None:
            self.__density = self._keyedOutputs("D")
        return self.__density

    @property
    def enthalpy(self) -> float:
        """Enthalpy [kJ/kg]."""
        if self.__enthalpy is None:
            self.__enthalpy = self._keyedOutputs("H")
        return self.__enthalpy

    @property
    def humidity(self) -> float:
        """Absolute humidity ratio [kg/kg]."""
        if self.__humidity is None:
            self.__humidity = self._keyedOutputs("W")
        return self.__humidity

    @property
    def partial_pressure(self) -> float:
        """Partial pressure of water vapor [Pa]."""
        if self.__partial_pressure is None:
            self.__partial_pressure = self._keyedOutputs("Pv")
        return self.__partial_pressure

    @property
    def pressure(self) -> float:
        """Absolute pressure [Pa]."""
        if self.__pressure is None:
            self.__pressure = self._keyedOutputs("P")
        return self.__pressure

    @property
    def specific_heat(self) -> float:
        """Specific heat [kJ/kg/K]."""
        if self.__specific_heat is None:
            self.__specific_heat = self._keyedOutputs("Cp")
        return self.__specific_heat

    @property
    def temperature(self) -> Temperature:
        """Temperature [K]."""
        if self.__temperature is None:
            k = self._keyedOutputs("T")
            self.__temperature = Temperature(k)
        return self.__temperature

    def factory(self) -> Solution:
        """
        Return a fresh Solution instance of the same type,
        with no inputs or cached outputs.
        """
        return Solution(self.__sol_list)

    def withState(
        self, first_input: InputSolution, second_input: InputSolution
    ) -> Solution:
        """
        Returns a new fluid instance with a defined state.

        :param first_input: First input property.
        :param second_input: Second input property.
        :return: A new solution instance with a defined state.
        :raises ValueError: If input is invalid.
        """
        solution = self.factory()

        solution.update(first_input, second_input)
        return solution

    def update(self, first_input: InputSolution, second_input: InputSolution):
        """
        Updates the state of the fluid.

        :param first_input: First input property.
        :param second_input: Second input property.
        :raises ValueError: If input is invalid.
        """
        if first_input.key == second_input.key:
            raise ValueError("Need to define 2 unique inputs!")

        self.reset()

        self._inputs = [first_input, second_input]

    # noinspection DuplicatedCode
    def reset(self):
        """Resets all non-trivial properties."""
        self._inputs.clear()
        self.__density = None
        self.__enthalpy = None
        self.__humidity = None
        self.__partial_pressure = None
        self.__specific_heat = None
        self.__temperature = None

    def _keyedOutputs(self, key: str):
        cashed_input = next((i for i in self._inputs if i.key == key), None)

        value = (
            cashed_input.value
            if cashed_input is not None
            else self.__sol_type().state(
                key,
                self._inputs[0].key,
                self._inputs[0].value,
                self._inputs[1].key,
                self._inputs[1].value,
            )
        )

        return value
