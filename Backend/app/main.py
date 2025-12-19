from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import psse_route, pscad_route, etap_route
import uvicorn

app = FastAPI(title="INS Automation Platform Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(psse_route.router, prefix="/api/psse", tags=["psse"])
app.include_router(pscad_route.router, prefix="/api/pscad", tags=["pscad"])
app.include_router(etap_route.router, prefix="/api/etap", tags=["etap"])

@app.get("/")
async def root():
    return {"message": "Welcome to INS Automation Platform Backend"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
