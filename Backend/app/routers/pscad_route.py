from fastapi import APIRouter, HTTPException
import os
from app.schemas.pscad_schema import BuildPSCADModelRequest, PSCADCreateCaseRequest

router = APIRouter()

@router.post("/build-equivalent-model")
async def build_equivalent_model(request: BuildPSCADModelRequest):
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=400, detail=f"File not found: {request.file_path}")
    
    try:
        from app.services.build_model_pscad_services.equivalent_pscad_service import PSCADService
        service = PSCADService(request.file_path, request.output_path)
        result = service.build_equivalent_model()
        
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])
             
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-cases")
async def create_pscad_cases(request: PSCADCreateCaseRequest):
    """
    Setup automation for multiple PSCAD cases (Copy & Parameter Update).
    """
    try:
        from app.services.pscad_setup_case_service import PSCADCreateCaseService
        service = PSCADCreateCaseService()
        results = service.create_cases(request.project_path, request.original_filename, request.cases)
        return {"message": "Batch creation completed", "results": results}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
