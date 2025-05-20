from abc import ABC, abstractmethod


class AbstractSolution(ABC):

    @abstractmethod
    def __init__(self):
        self._properties: dict[str, float | None] = {
            "Cp": None,
            "D": None,
            "H": None,
            "Pv": None,
            "T": None,
            "W": None,
            "X": None,
        }

    def state(self, purpose: str, key1: str, value1: float, key2: str, value2: float):
        if key1 == key2:
            raise ValueError("Properties must be different")

        if self._properties[key1] is None:
            self._properties[key1] = value1
        if self._properties[key2] is None:
            self._properties[key2] = value2

        if self._properties[purpose] is not None:
            return self._properties[purpose]

        # try key1 key2
        method = getattr(self, f"_state_{key1}_{key2}", None)
        if method is None:
            # try to swap key, value
            method = getattr(self, f"_state_{key2}_{key1}", None)
            if method is None:
                raise ValueError(f"No handler for keys ({key1}, {key2})")
            # swap value
            result = method(purpose, value2, value1)
        else:
            result = method(purpose, value1, value2)

        self._properties[purpose] = result
        return result
