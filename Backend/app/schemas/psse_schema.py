from pydantic import BaseModel
from typing import Optional, List

class BuildModelRequest(BaseModel):
    file_path: str

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

class MptItem(BaseModel):
    mpt_type: str = "2-WINDING"
    mpt_from: int
    mpt_to: int
    mpt_bus_3: Optional[int] = 0

class ShuntItem(BaseModel):
    BUS: int
    ID: str

class ReportPointItem(BaseModel):
    bess_id: str
    name: str
    bus_from: int
    bus_to: int
    
class ReactiveCheckConfig(BaseModel):
    SAV_PATH: str
    MPT_LIST: List[MptItem]
    SHUNT_LIST: List[ShuntItem] = []
    REG_BUS: List[int]
    GEN_BUSES: List[int]
    GEN_IDS: List[str] = []
    BUS_FROM: int = 0
    BUS_TO: int = 0
    P_NET: float = 0.0
    LOG_PATH: Optional[str] = None
    REPORT_POINTS: List[ReportPointItem]

class RunCheckResponse(BaseModel):
    status: str
    message: str
    log: List[str]

class GeneratorGroup(BaseModel):
    buses: List[int]
    ids: List[str]
    reg_buses: List[int] = []

class BasicModelRequest(BaseModel):
    sav_path: str
    project_type: str = "BESS" # BESS, PV, HYBRID
    bus_from: int
    bus_to: int
    p_net: float
    q_target: float = 0.0
    bess_generators: Optional[GeneratorGroup] = None
    pv_generators: Optional[GeneratorGroup] = None
    log_path: Optional[str] = None
