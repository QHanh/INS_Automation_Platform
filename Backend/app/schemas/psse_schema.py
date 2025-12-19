from pydantic import BaseModel
from typing import Optional, List

class BuildModelRequest(BaseModel):
    file_path: str
    output_path: Optional[str] = None


class TuningRequest(BaseModel):
    sav_path: str
    log_path: Optional[str] = None
    bus_from: int
    bus_to: int
    gen_buses: List[int]
    gen_ids: List[str]
    reg_bus: List[int]
    p_target: float
    q_target: float
