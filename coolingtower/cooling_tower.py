from pyfluids import HumidAir, InputHumidAir, Fluid, FluidsList, Input
from fanpump import Fan
from CoolProp.CoolProp import PropsSI

__all__ = ["CoolingTower"]


class CoolingTower:
    def __init__(
        self,
        inlet_air: HumidAir,
        inlet_water_temperature: float,  # C
        m_water: float,
        LG_or_outlet_air: float | HumidAir,  # kg/s
        target_temp: float = None,
        delta_P: float = 200,
    ):
        self.__inlet_air = inlet_air
        self.__inlet_water = Fluid(FluidsList.Water).with_state(
            Input.temperature(inlet_water_temperature),
            Input.pressure(101325),
        )

        self.__LG: float = None  # ratio of water and air mass flow (L/G)
        self.__m_air: float = None
        self.__m_water: float = m_water

        self.__target_enthalpy: float = None
        self.__outlet_air: HumidAir = None
        self.__outlet_water: Fluid = None

        self.__target_temp: float = target_temp  # C, target water temperature

        self.__approach_temp: float = 3  # C, default approach temperature
        self.__evaperate_rate: float = (
            0.01 / 6.9
        )  # %/C. water evaporated per degree of temperature difference

        self.__m_evap: float = None

        self.__delta_P = delta_P  # Pa
        self.__W: float = None
        self.__COP: float = None

        # self.__m_da: float = None
        # self.__m_a_out: float = None
        # self.__m_w_out: float = None
        if isinstance(LG_or_outlet_air, float):
            self.__LG = LG_or_outlet_air
        elif isinstance(LG_or_outlet_air, HumidAir):
            self.__target_enthalpy = LG_or_outlet_air.enthalpy

    @property
    def inlet_air(self) -> HumidAir:
        return self.__inlet_air

    @property
    def inlet_water(self) -> Fluid:
        return self.__inlet_water

    @property
    def outlet_air(self) -> HumidAir:
        if self.__outlet_air is None:
            self.__setOutletAir()
        return self.__outlet_air

    @property
    def outlet_water(self) -> Fluid:
        if self.__outlet_water is None:
            self.__setOutletWater()
        return self.__outlet_water

    @property
    def m_evap(self):
        if self.__m_evap is None:
            self.__m_evap = (
                self.LG
                * self.__evaperate_rate
                * (self.inlet_water.temperature - self.outlet_water.temperature)
            )
        return self.__m_evap

    @property
    def LG(self) -> float:
        if self.__LG is None:
            self.__setLG()
        return self.__LG

    @property
    def m_G(self) -> float:
        if self.__m_air is None:
            self.__m_air = self.__m_water / self.LG
        return self.__m_air

    @property
    def work(self) -> float:
        """Power consumption [kW]"""
        if self.__W is None:
            self.__setW()
        return self.__W

    @property
    def COP(self) -> float:
        if self.__COP is None:
            self.__setCOP()
        return self.__COP

    # @property
    # def m_a_in(self):
    #     return self.__m_a_in

    # @property
    # def m_a_out(self):
    #     if self.__m_a_out is None:
    #         self.__m_a_out = self.__m_a_in - self.dehumid_mass_flow
    #     return self.__m_a_out

    # @property
    # def m_a_dry(self):
    #     if self.__m_da is None:
    #         self.__m_da = self.__m_a_in / (1 + self.__inlet_air.humidity)
    #     return self.__m_da

    # @property
    # def m_w_in(self):
    #     return self.__m_w_in

    # @property
    # def m_w_out(self):
    #     if self.__m_w_out is None:
    #         self.__m_w_out = self.__m_w_in + self.dehumid_mass_flow
    #     return self.__m_w_out

    def __setOutletAir(self):
        if self.__LG is not None:
            outlet_air_enthalpy = (
                self.__LG
                * self.__inlet_water.specific_heat
                * (self.inlet_water.temperature - self.outlet_water.temperature)
                * (1 + self.__evaperate_rate * self.outlet_water.temperature)
                + self.__inlet_air.enthalpy
            )

            outlet_air_humidity = (
                self.inlet_air.humidity
                + self.__evaperate_rate
                * (self.__inlet_water.temperature - self.outlet_water.temperature)
                * self.__LG
            )
        else:
            outlet_air_enthalpy = self.__target_enthalpy

            outlet_air_humidity = (
                self.inlet_air.humidity
                + self.__evaperate_rate
                * (self.__inlet_water.temperature - self.outlet_water.temperature)
                * self.LG
            )

        self.__outlet_air = HumidAir().with_state(
            InputHumidAir.pressure(101325),
            InputHumidAir.enthalpy(outlet_air_enthalpy),  # Convert kJ/kg to J/kg
            InputHumidAir.humidity(outlet_air_humidity),
        )

    def __setOutletWater(self):
        air_wet_bulb = self.__inlet_air.wet_bulb_temperature
        if (
            self.__target_temp is not None
            and self.__target_temp > air_wet_bulb + self.__approach_temp
        ):
            outlet_water_temperature = self.__target_temp
        else:
            outlet_water_temperature = air_wet_bulb + self.__approach_temp

        # outlet_water_temperature = 30

        self.__outlet_water = Fluid(FluidsList.Water).with_state(
            Input.temperature(outlet_water_temperature),
            Input.pressure(101325),
        )

    def __setLG(self):
        delta_h = self.__target_enthalpy - self.__inlet_air.enthalpy
        delta_T = self.__inlet_water.temperature - self.outlet_water.temperature

        self.__LG = delta_h / (
            self.__inlet_water.specific_heat
            * delta_T
            * (1 + self.__evaperate_rate * self.outlet_water.temperature)
        )

    def __setW(self):
        fan = Fan(self.__inlet_air, 1, self.m_G, self.__delta_P)

        self.__W = fan.actual_work

    def __setCOP(self):
        delta_T = self.__inlet_water.temperature - self.outlet_water.temperature  # °C
        Q_sensible = self.__m_water * self.__inlet_water.specific_heat * delta_T / 1e3

        W_fan_kW = self.work

        self.__COP = Q_sensible / W_fan_kW
