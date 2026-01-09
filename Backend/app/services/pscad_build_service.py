import sys
import os

# Add libs to path
LIBS_PATH = os.path.join(os.path.dirname(__file__), "build_model_libs")
if LIBS_PATH not in sys.path:
    sys.path.append(LIBS_PATH)

try:
    import PSCAD_Model
except ImportError as e:
    print(f"Error importing PSCAD model: {e}")

class PscadBuildService:
    def __init__(self):
        pass

    def build_equivalent_model(self, excel_path: str, template_path: str = None):
        """
        Build PSCAD equivalent model.
        If template_path is not provided, uses the default template in Backend/templates/form_final.pscx
        """
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"File not found: {excel_path}")
            
        if not template_path:
            # Calculate default template path
            # Current file: Backend/app/services/pscad_build_service.py
            service_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(service_dir))
            template_path = os.path.join(backend_dir, "templates", "form_final.pscx")
            
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
            
        try:
             original_cwd = os.getcwd()
             os.chdir(os.path.dirname(excel_path))
             
             try:
                 # PSCAD_Model.PSCAD_Model(excel_path).main(template_path)
                 instance = PSCAD_Model.PSCAD_Model(excel_path)
                 instance.main(template_path)
                 result = {"success": True, "message": "PSCAD equivalent model built successfully"}
             finally:
                 os.chdir(original_cwd)
                 
             return result
        except Exception as e:
             return {"success": False, "message": str(e)}
