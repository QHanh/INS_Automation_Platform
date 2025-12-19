from pydantic import BaseModel
from typing import Optional

class EtapSldRequest(BaseModel):
    cls_file_path: str
    pcs_file_path: str
    mpt_type: str = "XFORM3W"
    create_sld_elements: bool = True
    create_poi_to_mpt_elements: bool = True
    connect_elements: bool = True
