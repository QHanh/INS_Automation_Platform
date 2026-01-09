import sys
import os

# Add libs to path
LIBS_PATH = os.path.join(os.path.dirname(__file__), "build_model_libs")
if LIBS_PATH not in sys.path:
    sys.path.append(LIBS_PATH)

try:
    import PSSE_Model
    import PSSE_Model_Detail
except ImportError as e:
    print(f"Error importing PSSE models: {e}")

class PsseBuildService:
    def __init__(self):
        pass

    def build_equivalent_model(self, excel_path: str):
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"File not found: {excel_path}")
        
        try:
            # Change CWD to the input file directory so outputs are generated there (common behavior expectation)
            original_cwd = os.getcwd()
            os.chdir(os.path.dirname(excel_path))
            
            try:
                # PSSE_Model.PSSE_model(excel_path).main()
                # Note: Assuming the class name inside the module is PSSE_model or similar based on user provided main.py
                instance = PSSE_Model.PSSE_model(excel_path)
                instance.main()
                result = {"success": True, "message": "Equivalent model built successfully"}
            finally:
                os.chdir(original_cwd)
                
            return result
        except Exception as e:
            return {"success": False, "message": str(e)}

    def build_detailed_model(self, excel_path: str):
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"File not found: {excel_path}")
            
        try:
            original_cwd = os.getcwd()
            os.chdir(os.path.dirname(excel_path))
            
            try:
                # PSSE_Model_Detail.detail_model(excel_path)
                PSSE_Model_Detail.detail_model(excel_path)
                result = {"success": True, "message": "Detailed model built successfully"}
            finally:
                os.chdir(original_cwd)
            
            return result
        except Exception as e:
            return {"success": False, "message": str(e)}
