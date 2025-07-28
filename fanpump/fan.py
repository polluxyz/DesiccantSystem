from pyfluids import HumidAir, InputHumidAir

__all__ = ["Fan"]


class Fan:
    def __init__(
        self,
        air: HumidAir,
        design_mass_flow: float,
        actual_mass_flow: float,
        delta_P: float,
    ):
        self.__air: HumidAir = air
        self.__design_mass_flow: float = design_mass_flow
        self.__actual_mass_flow: float = actual_mass_flow
        self.__delta_P: float = delta_P

        self.__design_work: float | None = None
        self.__actual_work: float | None = None

        self.__PLR: float | None = None
        self.__fan_eff: float = 0.5

    @property
    def design_work(self):
        """[kW]"""
        if self.__design_work is None:
            self.__setDesignWork()
        return self.__design_work

    @property
    def actual_work(self):
        """[kW]"""
        if self.__actual_work is None:
            self.__setActualWork()
        return self.__actual_work

    @property
    def PLR(self):
        if self.__PLR is None:
            self.__PLR = self.__actual_mass_flow / self.__design_mass_flow
        return self.__PLR

    def __setDesignWork(self):
        volumetric_flow_rate = self.__design_mass_flow / self.__air.density

        self.__design_work = (
            volumetric_flow_rate * self.__delta_P / self.__fan_eff / 1e3
        )

    def __setActualWork(self):
        # 確保 design_work 已經計算過
        Pd = self.design_work

        # 計算部分負載比
        plr = self.PLR

        # ASHRAE 90.1 G3 Method 2 部分負載曲線
        frac = -0.0013 + 0.1470 * plr + 0.9506 * plr**2 - 0.0998 * plr**3

        # 實際軸功率 (kW)
        self.__actual_work = Pd * frac
