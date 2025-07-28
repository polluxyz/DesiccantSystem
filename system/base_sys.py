from coolingtower import CoolingTower
from pyfluids import HumidAir, InputHumidAir, Fluid, FluidsList, Input
from fanpump import Pump

__all__ = ["BaseSys"]


class BaseSys:
    """
    LiquidDesiccantSystem with HeatPump
    """

    def __init__(
        self,
        CT_outlet_air: HumidAir = None,
        air: HumidAir = None,
        inlet_water_temp: float = 55,
        target_temp: float = 30,
    ):

        # 初始水、空氣條件
        self.__water = Fluid(FluidsList.Water).with_state(
            Input.pressure(101325), Input.temperature(inlet_water_temp)
        )
        self.__m_water = 1.1  # 水質量流率 (kg/s)
        if air is None:
            self.__air = HumidAir().with_state(
                InputHumidAir.pressure(101325),
                InputHumidAir.temperature(30),
                InputHumidAir.relative_humidity(75),
            )
        else:
            self.__air = air
        self.__m_air = 1  # 空氣質量流率 (kg/s)

        self.__CT: CoolingTower = None

        self.__LG: float = self.__m_water / self.__m_air
        self.__CT_outlet_air: HumidAir = CT_outlet_air

        self.__target_temp: float = target_temp

        self.__pump: Pump = None

        self.__total_work: float = None

    @property
    def water(self):
        return self.__water

    @property
    def air(self):
        return self.__air

    @property
    def m_water(self):
        return self.__m_water

    @property
    def m_air(self):
        return self.__m_air

    @property
    def CT(self) -> CoolingTower:
        if self.__CT is None:
            self.__setCoolingTower()
        return self.__CT

    @property
    def pump(self) -> CoolingTower:
        if self.__pump is None:
            self.__setPump()
        return self.__pump

    @property
    def work_total(self) -> CoolingTower:
        if self.__total_work is None:
            self.__total_work = self.CT.work + self.pump.work
        return self.__total_work

    def __setCoolingTower(self):
        """
        建立冷卻塔，並回傳 CoolingTower 物件
        """
        if self.__CT_outlet_air is None:
            self.__CT = CoolingTower(
                self.__air,
                self.__water.temperature,
                self.__m_water,
                self.__LG,
                self.__target_temp,
            )
        else:
            self.__CT = CoolingTower(
                self.__air,
                self.__water.temperature,
                self.__m_water,
                self.__CT_outlet_air,
                self.__target_temp,
            )

    def __setPump(self):
        self.__pump = Pump(self.__water, self.m_water, 20)

    def report(self):
        """
        輸出最終溫度與濕度狀態
        """
        print("冷卻水塔入口空氣溫度 (°C)：", self.CT.inlet_air.temperature)
        print("冷卻水塔出口空氣溫度 (°C)：", self.CT.outlet_air.temperature)
        print("冷卻水塔入口空氣相對濕度 (%)：", self.CT.inlet_air.relative_humidity)
        print("冷卻水塔出口空氣相對濕度 (%)：", self.CT.outlet_air.relative_humidity)
        print("冷卻水塔入水溫度 (°C)：", self.CT.inlet_water.temperature)
        print("冷卻水塔出水溫度 (°C)：", self.CT.outlet_water.temperature)

    def work_report(self):
        print("冷卻水塔功耗 kW：", self.CT.work, self.CT.work / self.work_total)
        print("冷卻水泵功耗：", self.pump.work, self.pump.work / self.work_total)


if __name__ == "__main__":
    sim = BaseSys()
    sim.report()

    # print(sim.CT.work, sim.pump.work)
    # print(sim.CT.outlet_air.temperature, sim.CT.outlet_air.relative_humidity)
    # print(sim.CT.outlet_air.enthalpy - sim.CT.inlet_air.enthalpy)
