from ldac import LiquidDesiccantSystem
from wasteheat import HeatExchanger, HeatPump, Refrigerant
from coolingtower import CoolingTower
from pyfluids import HumidAir, InputHumidAir, Fluid, FluidsList, Input
from solution import Solution, InputSolution
from fanpump import Fan, Pump

__all__ = ["LD_HX"]


class LD_HX:
    """
    LiquidDesiccantSystem with HeatExchanger
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
        self.__hx_on: bool = hx_on

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

        self.__HX: HeatExchanger = None

        # 吸附溶液初始設定
        X = 0.8  # 溶液質量分率
        T = 30  # 入口溫度 (°C)
        self.__sol_type = Solution("ILD")
        self.__init_solution = self.__sol_type.withState(
            InputSolution.temperature(T + 273.15),
            InputSolution.concentration(X),
        )
        self.__m_sol = 2  # 溶液質量流率 (kg/s)

        self.__CT: CoolingTower = None
        self.__CT_sol: CoolingTower = None
        self.__LG: float = self.__m_water / self.__m_air
        self.__CT_outlet_air: HumidAir = CT_outlet_air

        self.__target_temp: float = target_temp

        self.__abs: LiquidDesiccantSystem = None
        self.__reg: LiquidDesiccantSystem = None

        self.__pump: Pump = None
        self.__pump_abs: Pump = None
        self.__pump_reg: Pump = None
        self.__fan_abs: Fan = None
        self.__fan_reg: Fan = None

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
    def HX(self) -> HeatExchanger:
        if self.__HX is None:
            self.__setLiqDesSystem()
        return self.__HX

    @property
    def abs(self) -> LiquidDesiccantSystem:
        if self.__abs is None:
            self.__setLiqDesSystem()
        return self.__abs

    @property
    def reg(self) -> LiquidDesiccantSystem:
        if self.__reg is None:
            self.__setLiqDesSystem()
        return self.__reg

    @property
    def CT(self) -> CoolingTower:
        if self.__CT is None:
            self.__setCoolingTower()
        return self.__CT

    @property
    def CT_sol(self) -> CoolingTower:
        if self.__CT_sol is None:
            self.__setLiqDesSystem()
        return self.__CT_sol

    @property
    def pump(self) -> Pump:
        if self.__pump is None:
            self.__setPump()
        return self.__pump

    @property
    def pump_abs(self) -> Pump:
        if self.__pump_abs is None:
            self.__setPump_abs()
        return self.__pump_abs

    @property
    def pump_reg(self) -> Pump:
        if self.__pump_reg is None:
            self.__setPump_reg()
        return self.__pump_reg

    @property
    def fan_abs(self) -> Fan:
        if self.__fan_abs is None:
            self.__fan_abs = Fan(self.__air, self.__m_air, self.__m_air, 50)
        return self.__fan_abs

    @property
    def fan_reg(self) -> Fan:
        if self.__fan_reg is None:
            self.__fan_reg = Fan(self.__air, self.__m_air, self.__m_air, 50)
        return self.__fan_reg

    @property
    def work_total(self) -> float:
        if self.__total_work is None:
            self.__total_work = (
                self.CT.work
                + self.pump.work
                + self.CT_sol.work
                + self.fan_abs.actual_work
                + self.fan_reg.actual_work
                + self.pump_abs.work
                + self.pump_reg.work
            )
        return self.__total_work

    def __coolingSolSys(self, sys: LiquidDesiccantSystem) -> Solution:
        """
        無熱交換器模式：直接對再生溶液與除濕出水進行處理
        """
        water = Fluid(FluidsList.Water).with_state(
            Input.pressure(101325), Input.temperature(25)
        )
        m_water_sol_CT = 1.01

        HX = HeatExchanger(sys.outlet_solution, sys.m_s_out, water, m_water_sol_CT)
        sol_out = sys.inlet_solution.withState(
            InputSolution.temperature(HX.outlet_hot.temperature),
            InputSolution.concentration(HX.outlet_hot.concentration),
        )

        self.__CT_sol = CoolingTower(
            self.__air, HX.outlet_cold.temperature, m_water_sol_CT, self.__LG, 25
        )
        return sol_out

    def __coolingSolHx(self, hx: HeatExchanger) -> Solution:
        """
        有熱交換器模式：使用傳入的 HeatExchanger 對吸附與再生環進行處理
        """
        water = Fluid(FluidsList.Water).with_state(
            Input.pressure(101325), Input.temperature(25)
        )
        m_water_sol_HX_CT = 0.651

        HX = HeatExchanger(hx.outlet_hot, hx.m_hot, water, m_water_sol_HX_CT)
        sol_out = hx.inlet_hot.withState(
            InputSolution.temperature(HX.outlet_hot.temperature),
            InputSolution.concentration(HX.outlet_hot.concentration),
        )

        self.__CT_sol = CoolingTower(
            self.__air, HX.outlet_cold.temperature, m_water_sol_HX_CT, self.__LG, 25
        )
        return sol_out

    def __setLiqDesSystem(self, iterations: int = 1000):
        # 初始除濕與再生系統
        abs = LiquidDesiccantSystem(
            self.__sol_type,
            self.__air,
            self.__init_solution,
            self.__m_air,
            self.__m_sol,
            0.64,
        )

        self.__HX = HeatExchanger(
            self.__water, self.__m_water, abs.outlet_solution, abs.m_s_out
        )

        reg = LiquidDesiccantSystem(
            self.__sol_type,
            self.__air,
            self.__HX.outlet_cold,
            self.__m_air,
            self.__HX.m_cold,
            0.64,
        )

        if self.__hx_on:
            for _ in range(iterations):
                HX_cycle = HeatExchanger(
                    reg.outlet_solution,
                    reg.m_s_out,
                    abs.outlet_solution,
                    abs.m_s_out,
                )
                abs_sol = self.__coolingSolHx(HX_cycle)
                abs = LiquidDesiccantSystem(
                    self.__sol_type,
                    self.__air,
                    abs_sol,
                    self.__m_air,
                    reg.m_s_out,
                    0.64,
                )

                self.__HX = HeatExchanger(
                    self.__water, self.__m_water, HX_cycle.outlet_cold, abs.m_s_out
                )

                reg = LiquidDesiccantSystem(
                    self.__sol_type,
                    self.__air,
                    self.__HX.outlet_cold,
                    self.__m_air,
                    self.__HX.m_cold,
                    0.64,
                )
        else:
            for _ in range(iterations):
                abs_sol = self.__coolingSolSys(reg)
                abs = LiquidDesiccantSystem(
                    self.__sol_type,
                    self.__air,
                    abs_sol,
                    self.__m_air,
                    reg.m_s_out,
                    0.64,
                )

                self.__HX = HeatExchanger(
                    self.__water, self.__m_water, abs.outlet_solution, abs.m_s_out
                )

                reg = LiquidDesiccantSystem(
                    self.__sol_type,
                    self.__air,
                    self.__HX.outlet_cold,
                    self.__m_air,
                    self.__HX.m_cold,
                    0.64,
                )
        self.__abs = abs
        self.__reg = reg

    def __setCoolingTower(self):
        """
        建立冷卻塔，並回傳 CoolingTower 物件
        """
        if self.__CT_outlet_air is None:
            self.__CT = CoolingTower(
                self.abs.outlet_air,
                self.__HX.outlet_hot.temperature,
                self.__m_water,
                self.__LG,
                self.__target_temp,
            )
        else:
            self.__CT = CoolingTower(
                self.abs.outlet_air,
                self.__HX.outlet_hot.temperature,
                self.__m_water,
                self.__CT_outlet_air,
                self.__target_temp,
            )

    def __setPump(self):
        self.__pump = Pump(self.__water, self.m_water, 20)

    def __setPump_abs(self):
        self.__pump_abs = Pump(self.abs.outlet_solution, self.abs.m_s_out, 5)

    def __setPump_reg(self):
        self.__pump_reg = Pump(self.reg.outlet_solution, self.reg.m_s_out, 5)

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
        print("離子溶液吸收入口空氣溫度 (°C)：", self.abs.inlet_air.temperature)
        print("離子溶液吸收出口空氣溫度 (°C)：", self.abs.outlet_air.temperature)
        print(
            "離子溶液吸收入口空氣相對濕度 (%)：", self.abs.inlet_air.relative_humidity
        )
        print(
            "離子溶液吸收出口空氣相對濕度 (%)：", self.abs.outlet_air.relative_humidity
        )
        print("離子溶液再生入口空氣溫度 (°C)：", self.reg.inlet_air.temperature)
        print("離子溶液再生出口空氣溫度 (°C)：", self.reg.outlet_air.temperature)
        print(
            "離子溶液再生入口空氣相對濕度 (%)：", self.reg.inlet_air.relative_humidity
        )
        print(
            "離子溶液再生出口空氣相對濕度 (%)：", self.reg.outlet_air.relative_humidity
        )

    def sol_report(self):
        """
        輸出最終溫度與濕度狀態
        """
        print(
            "離子溶液吸收入口溶液溫度 (°C)：", self.abs.inlet_solution.temperature.toC
        )
        print(
            "離子溶液吸收出口溶液溫度 (°C)：", self.abs.outlet_solution.temperature.toC
        )
        print("離子溶液吸收入口溶液濃度 (%)：", self.abs.inlet_solution.concentration)
        print("離子溶液吸收出口溶液濃度 (%)：", self.abs.outlet_solution.concentration)
        print(
            "離子溶液再生入口溶液溫度 (°C)：", self.reg.inlet_solution.temperature.toC
        )
        print(
            "離子溶液再生出口溶液溫度 (°C)：", self.reg.outlet_solution.temperature.toC
        )
        print("離子溶液再生入口溶液濃度 (%)：", self.reg.inlet_solution.concentration)
        print("離子溶液再生出口溶液濃度 (%)：", self.reg.outlet_solution.concentration)
        print("熱交換器入口溶液溫度 (°C)：", self.HX.inlet_cold.temperature.toC)
        print("熱交換器出口溶液溫度 (°C)：", self.HX.outlet_cold.temperature.toC)
        print("熱交換器入口溶液濃度 (%)：", self.HX.inlet_cold.concentration)
        print("熱交換器出口溶液濃度 (%)：", self.HX.outlet_cold.concentration)
        print("溶液冷卻水塔入水溫度 (°C)：", self.CT_sol.inlet_water.temperature)
        print("溶液冷卻水塔出水溫度 (°C)：", self.CT_sol.outlet_water.temperature)

    def work_report(self):
        print("冷卻水塔功耗 kW：", self.CT.work, self.CT.work / self.work_total)
        print("冷卻水泵功耗：", self.pump.work, self.pump.work / self.work_total)
        print(
            "液態吸收冷卻水塔功耗 kW：",
            self.CT_sol.work,
            self.CT_sol.work / self.work_total,
        )
        print(
            "離子溶液吸收風扇功耗 kW：",
            self.fan_abs.actual_work,
            self.fan_abs.actual_work / self.work_total,
        )
        print(
            "離子溶液再生風扇功耗：",
            self.fan_reg.actual_work,
            self.fan_reg.actual_work / self.work_total,
        )
        print(
            "離子溶液吸收水泵功耗 kW：",
            self.pump_abs.work,
            self.pump_abs.work / self.work_total,
        )
        print(
            "離子溶液再生水泵功耗：",
            self.pump_reg.work,
            self.pump_reg.work / self.work_total,
        )


if __name__ == "__main__":
    sim = LD_HX(hx_on=True)
    sim.report()

    print(sim.CT_sol.work, sim.CT.work)
