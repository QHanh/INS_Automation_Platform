import uvicorn
import os
import sys
import multiprocessing
from app.main import app

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    multiprocessing.freeze_support()
    uvicorn.run(app, host="0.0.0.0", port=8123)
