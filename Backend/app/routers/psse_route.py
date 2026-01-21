from fastapi import APIRouter, HTTPException
import os
import traceback
from typing import Literal
from app.schemas.psse_schema import BuildModelRequest, TuningRequest, ReactiveCheckConfig, RunCheckResponse, BasicModelRequest

router = APIRouter()

@router.post("/build-equivalent-model")
async def build_model(request: BuildModelRequest):
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=400, detail=f"File not found: {request.file_path}")
    
    try:
        from app.services.psse_build_service import PsseBuildService
        service = PsseBuildService()
        result = service.build_equivalent_model(request.file_path)
        
        if not result["success"]:
            error_detail = {
                "error": result["message"],
                "traceback": result.get("traceback", ""),
                "file_path": request.file_path
            }
            raise HTTPException(status_code=500, detail=error_detail)

        # Determine output folder (assumed to be same as input file dir for now)
        output_folder = os.path.dirname(request.file_path)
        
        return {
            "message": result["message"],
            "file_path": request.file_path,
            "output_folder": output_folder,
            "sld_file": os.path.join(output_folder, "project.sld"),
            "sav_file": os.path.join(output_folder, "project.sav")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "file_path": request.file_path
        }
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/build-detailed-model")
async def build_detailed_model(request: BuildModelRequest):
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=400, detail=f"File not found: {request.file_path}")
    
    try:
        from app.services.psse_build_service import PsseBuildService
        service = PsseBuildService()
        result = service.build_detailed_model(request.file_path)
        
        if not result["success"]:
            error_detail = {
                "error": result["message"],
                "traceback": result.get("traceback", ""),
                "file_path": request.file_path
            }
            raise HTTPException(status_code=500, detail=error_detail)
        
        return {
            "message": result["message"],
            "input_file_path": request.file_path,
            "output_folder": os.path.dirname(request.file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "file_path": request.file_path
        }
        raise HTTPException(status_code=500, detail=error_detail)

@router.post("/tune/{mode}")
async def tune_psse(mode: Literal["P", "Q", "PQ"], request: TuningRequest):
    """
    Tune PSSE model for P, Q, or PQ.
    
    - **mode**: 'P' for active power, 'Q' for reactive power, 'PQ' for both
    - **request**: TuningRequest with required parameters
    """
    if not os.path.exists(request.sav_path):
        raise HTTPException(status_code=400, detail=f"SAV file not found: {request.sav_path}")
    
    if len(request.gen_buses) != len(request.gen_ids):
        raise HTTPException(status_code=400, detail="gen_buses and gen_ids must have the same length")
    
    if len(request.gen_buses) != len(request.reg_bus):
        raise HTTPException(status_code=400, detail="gen_buses and reg_bus must have the same length")
    
    try:
        from app.services.tuning_psse_service import PSSETuningService
        service = PSSETuningService(request.sav_path, request.log_path)
        result = service.run_tuning(
            mode=mode,
            bus_from=request.bus_from,
            bus_to=request.bus_to,
            gen_buses=request.gen_buses,
            gen_ids=request.gen_ids,
            reg_bus=request.reg_bus,
            p_target=request.p_target,
            q_target=request.q_target
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/basic-model")
async def create_basic_model(request: BasicModelRequest):
    """
    Generate Basic Model SAV files (Charge/Discharge etc.)
    """
    def log_cb(msg):
        print(f"[BasicModel] {msg}")
    
    from app.services.basic_model_psse_service import BasicModelService
    service = BasicModelService(log_cb=log_cb)
    
    cfg = request.dict()
    
    # Check project type
    if request.project_type == "BESS":
        success = service.run_bess_alone(cfg)
    elif request.project_type == "PV":
        success = service.run_pv_alone(cfg)
    elif request.project_type == "HYBRID":
        success = service.run_hybrid(cfg)
    else:
        return {"success": False, "message": f"Project type {request.project_type} not supported. Use BESS, PV, or HYBRID."}
        
    if success:
         return {"success": True, "message": "Basic Model generation completed."}
    else:
         return {"success": False, "message": "Failed to generate Basic Model. Check logs."}

@router.post("/check-reactive", response_model=RunCheckResponse)
async def check_reactive(config: ReactiveCheckConfig):
    from app.services import check_reactive_psse_service
    logs = []
    def log_callback(msg: str):
        logs.append(msg)
        print(msg) 

    try:
        cfg_dict = config.dict()
        check_reactive_psse_service.run_check_logic(cfg_dict, "RUN_ALL", log_callback)
        
        return RunCheckResponse(
            status="success",
            message="Completed check reactive sequence.",
            log=logs
        )
    except Exception as e:
        return RunCheckResponse(
            status="error",
            message=str(e),
            log=logs
        )