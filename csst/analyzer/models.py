from typing import List, ClassVar

from pydantic import BaseModel


class AverageTransmission(BaseModel):
    reactor: str
    temp: float
    temp_range: float
    transmissions: List[float]
    average_transmission: float
    std: float

    INSOLUBLE_BELOW_TRANSMISSION: ClassVar[float] = 10
    SOLUBLE_ABOVE_TRANSMISSION: ClassVar[float] = 85
    SOLUBLE: ClassVar[str] = "soluble"
    PARTIAL: ClassVar[str] = "partially_soluble"
    INSOLUBLE: ClassVar[str] = "insoluble"

    def get_solubility_based_on_average(self):
        if self.average_transmission <= self.INSOLUBLE_BELOW_TRANSMISSION:
            return self.INSOLUBLE
        elif self.average_transmission >= self.SOLUBLE_ABOVE_TRANSMISSION:
            return self.SOLUBLE
        else:
            return self.PARTIAL
