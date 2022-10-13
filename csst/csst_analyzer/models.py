from pydantic import BaseModel

class AverageTransmission(BaseModel):
    reactor: str
    temp: float
    temp_range: float
    transmission: float
    std: float
