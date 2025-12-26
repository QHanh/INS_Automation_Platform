from fastapi import APIRouter, HTTPException
import os
from typing import Literal
from app.schemas.psse_schema import BuildModelRequest, TuningRequest, ReactiveCheckConfig, RunCheckResponse

router = APIRouter()

@router.post("/build-equivalent-model")
async def build_model(request: BuildModelRequest):
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=400, detail=f"File not found: {request.file_path}")
    
    try:
        from app.services.build_model_psse_services.equivalent_psse_service import EquivalentPSSEService
        service = EquivalentPSSEService(request.file_path, request.output_path)
        
        # Single call orchestration matching PSSE.py logic
        result = service.run_build_model()
        
        if "error" in str(result).lower() and "success" not in str(result).lower():
             raise HTTPException(status_code=500, detail=f"Model Generation Failed: {result}")

        # Determine output folder similarly to how service does if not provided
        output_folder = request.output_path if request.output_path else os.path.dirname(request.file_path)
        
        return {
            "message": "Model built successfully",
            "file_path": request.file_path,
            "output_folder": output_folder,
            "sld_file": os.path.join(output_folder, "project.sld"),
            "sav_file": os.path.join(output_folder, "project.sav")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build-detailed-model")
async def build_detailed_model(request: BuildModelRequest):
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=400, detail=f"File not found: {request.file_path}")
    
    try:
        from app.services.build_model_psse_services.detailed_psse_service import DetailedPSSEService
        service = DetailedPSSEService(request.file_path, request.output_path)
        
        result = service.build_detailed_model()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return {
            "message": result["message"],
            "input_file_path": request.file_path,
            "output_folder": service.output_path,
            "raw_file": result["raw_file"],
            "seq_file": result["seq_file"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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