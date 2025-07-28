from CoolProp.CoolProp import PropsSI

from .abstract_solution import AbstractSolution

__all__ = ["ILD"]


class ILD(AbstractSolution):
    def __init__(self):
        super().__init__()

    def _state_T_X(self, purpose: str, T: float, X: float):
        if purpose == "Cp":
            return self.__getCp_T_X(T, X)
        elif purpose == "D":
            return self.__getD_T_X(T, X)
        elif purpose == "H":
            return self.__getH_T_X(T, X)
        elif purpose == "Pv":
            return self.__getPv_T_X(T, X)
        elif purpose == "W":
            return self.__getW_T_X(T, X)
        else:
            raise ValueError(f"Unknown purpose: {purpose}")

    def _state_H_X(self, purpose: str, H: float, X: float):
        if purpose == "T":
            return self.__getT_H_X(H, X)
        elif self._properties["T"] is None:
            self.__getT_H_X(H, X)

        T = self._properties["T"]
        if purpose == "Cp":
            return self.__getCp_T_X(T, X)
        elif purpose == "D":
            return self.__getD_T_X(T, X)
        elif purpose == "Pv":
            return self.__getPv_T_X(T, X)
        elif purpose == "W":
            return self.__getW_T_X(T, X)
        else:
            raise ValueError(f"Unknown purpose: {purpose}")

    def __getPv_T_X(self, T, X):
        a0, a1, a2, a3 = 12.10, -28.01, 50.34, -24.63
        b0, b1, b2, b3 = 1212.67, 772.37, 614.59, 493.33

        A = a0 + a1 * X + a2 * X**2 + a3 * X**3
        B = b0 + b1 * X + b2 * X**2 + b3 * X**3

        P_mbar = 10 ** (A - B / T)
        P_Pa = P_mbar * 100

        self._properties["Pv"] = P_Pa
        return P_Pa

    def __getW_T_X(self, T, X):
        Pa = 101325
        if self._properties["Pv"] is None:
            self._properties["Pv"] = self.__getPv_T_X(T, X)
        Pv = self._properties["Pv"]

        if Pv >= Pa:
            raise ValueError("Pv should less than Pa")

        w = 0.62198 * Pv / (Pa - Pv)

        self._properties["W"] = w
        return w

    def __getD_T_X(self, T, X):
        a0 = 804.28 + 1.585 * T - 0.0031 * T**2
        a1 = 1036.04 - 4.42 * T + 0.0057 * T**2
        a2 = -403.62 + 1.745 * T - 0.0021 * T**2

        d = a0 + a1 * X + a2 * X**2

        self._properties["D"] = d
        return d

    def __getH_T_X(self, T, X):
        T_ref = 0

        h = X * (0.00238 * (T**2 - T_ref**2) - 4.01 * (T - T_ref)) + 4.21 * (T - T_ref)

        self._properties["H"] = h
        return h

    def __getCp_T_X(self, T, X):
        cp = (0.00476 * T - 4.01) * X + 4.21

        self._properties["Cp"] = cp
        return cp

    def __getT_H_X(self, H, X):
        T_ref = 0
        T = 237.15  # start test temperature

        tol = 1e-6
        max_iter = 1000

        for _ in range(max_iter):
            h = X * (0.00238 * (T**2 - T_ref**2) - 4.01 * (T - T_ref)) + 4.21 * (
                T - T_ref
            )
            # residual
            f = h - H
            if abs(f) < tol:
                break
            # Dirivative = Cp(T,X)
            cp = self.__getCp_T_X(T, X)
            # refresh
            T -= f / cp

        self._properties["T"] = T
        return T  # Kelvin


if __name__ == "__main__":

    # 範例：X = 0.70 (70 wt.%), T = 298.15 K (25 °C)
    x = 0.8
    T = 20
    T += 273.15  # Convert to Kelvin

    t = ILD().state("Pv", "X", x, "T", T)
    print(t)
