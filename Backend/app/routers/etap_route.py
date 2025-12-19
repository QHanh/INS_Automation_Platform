from fastapi import APIRouter, HTTPException
import os
from app.schemas.etap_schema import EtapSldRequest

router = APIRouter()

@router.post("/create-bess-sld")
async def create_bess_sld(request: EtapSldRequest):
    if not os.path.exists(request.cls_file_path):
        raise HTTPException(status_code=400, detail=f"CLS file not found: {request.cls_file_path}")
    if not os.path.exists(request.pcs_file_path):
        raise HTTPException(status_code=400, detail=f"PCS file not found: {request.pcs_file_path}")
    
    try:
        from app.services.build_model_etap_services.etap_bess_sld_service import EtapBessSldService
        service = EtapBessSldService(
            cls_file_path=request.cls_file_path,
            pcs_file_path=request.pcs_file_path,
            mpt_type=request.mpt_type
        )
        
        results = service.generate_sld(
            create_sld_elements=request.create_sld_elements,
            create_poi_to_mpt=request.create_poi_to_mpt_elements,
            connect_elements=request.connect_elements
        )
        
        failures = [k for k, v in results.items() if not v.get("success")]
        if failures:
             return {
                 "status": "partial_success",
                 "message": "Some steps failed.",
                 "details": results
             }
        
        return {
            "status": "success",
            "message": "SLD generation commands sent to ETAP successfully.",
            "details": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-pv-sld")
async def create_pv_sld(request: EtapSldRequest):
    if not os.path.exists(request.cls_file_path):
        raise HTTPException(status_code=400, detail=f"CLS file not found: {request.cls_file_path}")
    if not os.path.exists(request.pcs_file_path):
        raise HTTPException(status_code=400, detail=f"PCS file not found: {request.pcs_file_path}")
    
    try:
        from app.services.build_model_etap_services.etap_pv_sld_service import EtapPvSldService
        service = EtapPvSldService(
            cls_file_path=request.cls_file_path,
            pcs_file_path=request.pcs_file_path,
            mpt_type=request.mpt_type
        )
        
        results = service.generate_sld(
            create_sld_elements=request.create_sld_elements,
            create_poi_to_mpt=request.create_poi_to_mpt_elements,
            connect_elements=request.connect_elements
        )
        
        failures = [k for k, v in results.items() if not v.get("success")]
        if failures:
             return {
                 "status": "partial_success",
                 "message": "Some steps failed.",
                 "details": results
             }
        
        return {
            "status": "success",
            "message": "SLD generation commands sent to ETAP successfully.",
            "details": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-wt-sld")
async def create_wt_sld(request: EtapSldRequest):
    if not os.path.exists(request.cls_file_path):
        raise HTTPException(status_code=400, detail=f"CLS file not found: {request.cls_file_path}")
    if not os.path.exists(request.pcs_file_path):
        raise HTTPException(status_code=400, detail=f"PCS file not found: {request.pcs_file_path}")
    
    try:
        from app.services.build_model_etap_services.etap_wt_sld_service import EtapWtSldService
        service = EtapWtSldService(
            cls_file_path=request.cls_file_path,
            pcs_file_path=request.pcs_file_path,
            mpt_type=request.mpt_type
        )
        
        results = service.generate_sld(
            create_sld_elements=request.create_sld_elements,
            create_poi_to_mpt=request.create_poi_to_mpt_elements,
            connect_elements=request.connect_elements
        )
        
        failures = [k for k, v in results.items() if not v.get("success")]
        if failures:
             return {
                 "status": "partial_success",
                 "message": "Some steps failed.",
                 "details": results
             }
        
        return {
            "status": "success",
            "message": "SLD generation commands sent to ETAP successfully.",
            "details": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
