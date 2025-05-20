__all__ = ["Temperature"]


class Temperature(float):
    def __new__(cls, kelvin: float):
        return super().__new__(cls, kelvin)

    @property
    def toC(self) -> float:
        return float(self) - 273.15
