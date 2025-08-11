from sdac import SolidDesiccantSystem
from wasteheat import HeatExchanger, HeatPump, Refrigerant
from coolingtower import CoolingTower
from pyfluids import HumidAir, InputHumidAir, Fluid, FluidsList, Input
from fanpump import Fan, Pump

__all__ = ["SD_HP"]


class SD_HP:
    """
    SolidDesiccantSystem with HeatPump
    """

    def __init__(
        self,
        CT_outlet_air: HumidAir = None,
        air: HumidAir = None,
        inlet_water_temp: float = 55,
        target_temp: float = 30,
        hx_on: bool = True,
    ):
        # 是否啟用熱交換器迴路
        self.__hx_on = hx_on

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
        self.__m_air_reg = 1.3

        # 冷凝/蒸發溫度與製冷劑
        self.__T_evap = 40
        self.__T_cond = 55
        self.__refrigerant = Refrigerant("R134A", self.__T_evap, self.__T_cond)
        self.__m_ref = 0.067 if hx_on else 0.1192
        self.__HP: HeatPump = None

        self.__CT: CoolingTower = None
        self.__LG: float = self.__m_water / self.__m_air
        self.__CT_outlet_air: HumidAir = CT_outlet_air

        self.__target_temp: float = target_temp

        self.__ads: SolidDesiccantSystem = None
        self.__reg: SolidDesiccantSystem = None

        self.__pump: Pump = None
        self.__fan_ads: Fan = None
        self.__fan_reg: Fan = None

        self.__CoolHX: HeatExchanger = None
        self.__CoolHX_water = Fluid(FluidsList.Water).with_state(
            Input.pressure(101325), Input.temperature(22)
        )

        self.__total_work: float = None

        self.__hp_in_air: HumidAir = None

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
    def HP(self) -> HeatPump:
        if self.__HP is None:
            self.__setHeatPump()
        return self.__HP

    @property
    def ads(self) -> SolidDesiccantSystem:
        if self.__ads is None:
            self.__setSolidDesSystem()
        return self.__ads

    @property
    def reg(self) -> SolidDesiccantSystem:
        if self.__reg is None:
            self.__setSolidDesSystem()
        return self.__reg

    @property
    def CT(self) -> CoolingTower:
        if self.__CT is None:
            self.__setCoolingTower()
        return self.__CT

    @property
    def pump(self) -> Pump:
        if self.__pump is None:
            self.__setPump()
        return self.__pump

    @property
    def CoolHX(self) -> HeatExchanger:
        if self.__CoolHX is None:
            self.__CoolHX = HeatExchanger(
                self.ads.outlet_air, self.__m_air, self.__CoolHX_water, 1
            )
        return self.__CoolHX

    @property
    def work_total(self) -> float:
        if self.__total_work is None:
            self.__total_work = (
                self.CT.work
                + self.pump.work
                + self.HP.W_comp
                + self.fan_ads.actual_work
                + self.fan_reg.actual_work
            )
        return self.__total_work

    @property
    def fan_ads(self) -> Fan:
        if self.__fan_ads is None:
            self.__fan_ads = Fan(self.__air, self.__m_air, self.__m_air, 50)
        return self.__fan_ads

    @property
    def fan_reg(self) -> Fan:
        if self.__fan_reg is None:
            self.__fan_reg = Fan(self.__air, self.__m_air_reg, self.__m_air_reg, 50)
        return self.__fan_reg

    def __setHeatPump(self):
        self.__HP = HeatPump(
            self.__refrigerant,
            self.__m_ref,
            self.__water,
            self.__m_water,
            self.__air,
            self.__m_air,
        )

    def __setSolidDesSystem(self, iterations: int = 1000):
        # 初始除濕與再生系統
        ads = SolidDesiccantSystem(self.__air, self.__m_air, 0)

        Q = 20.493519919167444 if self.__hx_on else self.HP.Q_cond
        print(self.HP.Q_cond)
        reg_air = HumidAir().with_state(
            InputHumidAir.pressure(101325),  # Pa
            InputHumidAir.enthalpy(self.__air.enthalpy + Q / self.__m_air * 1e3),
            InputHumidAir.humidity(self.__air.humidity),
        )
        reg = SolidDesiccantSystem(reg_air, self.__m_air_reg, ads.current_moisture)

        if self.__hx_on:
            for _ in range(iterations):
                if _ > 300:
                    HX_cycle = HeatExchanger(
                        ads.outlet_air, self.__m_air, self.__air, self.__m_air, 0.3
                    )

                    self.__hp_in_air = HumidAir().with_state(
                        InputHumidAir.pressure(101325),  # Pa
                        InputHumidAir.enthalpy(HX_cycle.outlet_cold.enthalpy),
                        InputHumidAir.humidity(HX_cycle.outlet_cold.humidity),
                    )

                    reg_air = HumidAir().with_state(
                        InputHumidAir.pressure(101325),  # Pa
                        InputHumidAir.enthalpy(
                            HX_cycle.outlet_cold.enthalpy
                            + self.HP.Q_cond / self.__m_air * 1e3
                        ),
                        InputHumidAir.humidity(HX_cycle.outlet_cold.humidity),
                    )

                ads = SolidDesiccantSystem(
                    self.__air, self.__m_air, reg.current_moisture
                )

                reg = SolidDesiccantSystem(
                    reg_air, self.__m_air_reg, ads.current_moisture
                )

            ads.setOutletAir(HX_cycle.outlet_hot)

        else:
            for _ in range(iterations):
                ads = SolidDesiccantSystem(
                    self.__air, self.__m_air, reg.current_moisture
                )

                reg = SolidDesiccantSystem(
                    reg_air, self.__m_air_reg, ads.current_moisture
                )

        self.__ads = ads
        self.__reg = reg

    def __setCoolingTower(self):
        """
        建立冷卻塔，並回傳 CoolingTower 物件
        """
        if self.__CT_outlet_air is None:
            self.__CT = CoolingTower(
                self.CoolHX.outlet_hot,
                self.HP.outlet_evap.temperature,
                self.__m_water,
                self.__LG,
                self.__target_temp,
            )
        else:
            self.__CT = CoolingTower(
                self.CoolHX.outlet_hot,
                self.HP.outlet_evap.temperature,
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
        print(
            "熱泵入口空氣溫度 (°C)：",
            self.__hp_in_air.temperature if self.__hx_on else self.__air.temperature,
        )
        print("熱泵出口空氣溫度 (°C)：", self.reg.inlet_air.temperature)
        print(
            "熱泵入口空氣相對濕度 (%)：",
            (
                self.__hp_in_air.relative_humidity
                if self.__hx_on
                else self.__air.relative_humidity
            ),
        )
        print("熱泵出口空氣相對濕度 (%)：", self.reg.inlet_air.relative_humidity)
        print("除濕轉輪吸附入口空氣溫度 (°C)：", self.ads.inlet_air.temperature)
        print("除濕轉輪吸附出口空氣溫度 (°C)：", self.ads.outlet_air.temperature)
        print(
            "除濕轉輪吸附入口空氣相對濕度 (%)：", self.ads.inlet_air.relative_humidity
        )
        print(
            "除濕轉輪吸附出口空氣相對濕度 (%)：", self.ads.outlet_air.relative_humidity
        )
        print("除濕轉輪再生入口空氣溫度 (°C)：", self.reg.inlet_air.temperature)
        print("除濕轉輪再生出口空氣溫度 (°C)：", self.reg.outlet_air.temperature)
        print(
            "除濕轉輪再生入口空氣相對濕度 (%)：", self.reg.inlet_air.relative_humidity
        )
        print(
            "除濕轉輪再生出口空氣相對濕度 (%)：", self.reg.outlet_air.relative_humidity
        )

    def work_report(self):
        print("冷卻水塔功耗 kW：", self.CT.work, self.CT.work / self.work_total)
        print("冷卻水泵功耗：", self.pump.work, self.pump.work / self.work_total)
        print("熱泵功耗：", self.HP.W_comp, self.HP.W_comp / self.work_total)
        print(
            "除濕轉輪吸附風扇功耗 kW：",
            self.fan_ads.actual_work,
            self.fan_ads.actual_work / self.work_total,
        )
        print(
            "除濕轉輪再生風扇功耗：",
            self.fan_reg.actual_work,
            self.fan_reg.actual_work / self.work_total,
        )


if __name__ == "__main__":
    sim = SD_HP(hx_on=False)
    sim.report()

    print(sim.CT.work)
