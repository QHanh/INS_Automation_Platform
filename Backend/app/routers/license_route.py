from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.license_service import verify_license

router = APIRouter()

class LicenseVerifyRequest(BaseModel):
    file_path: str

@router.post("/verify")
async def verify_license_endpoint(request: LicenseVerifyRequest):
    try:
        try:
            with open(request.file_path, "r", encoding="utf-8") as f:
                token = f.read().strip()
        except FileNotFoundError:
            raise HTTPException(status_code=400, detail="License file not found.")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not read license file.")
            
        payload = verify_license.verify_license_token(token)
        return {"success": True, "payload": payload}
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
