from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class BuildPSCADModelRequest(BaseModel):
    file_path: str
    output_path: Optional[str] = None

class PSCADComponent(BaseModel):
    id: int
    parameters: Dict[str, Any]

class PSCADCase(BaseModel):
    new_filename: str
    components: List[PSCADComponent]

class PSCADCreateCaseRequest(BaseModel):
    project_path: str
    original_filename: str
    cases: List[PSCADCase]

class SimulinkToPscadRequest(BaseModel):
    simulink_folder: str
    output_path: Optional[str] = None
