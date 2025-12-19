import uvicorn
import os
import sys
import multiprocessing
from app.main import app

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Check for worker flag
    if "--dll-worker" in sys.argv:
        from app.services.simulink_to_pscad_services.get_dll_info import run_worker
        run_worker()
        sys.exit(0)
    
    uvicorn.run(app, host="0.0.0.0", port=8123)
