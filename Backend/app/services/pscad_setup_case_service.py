import os
import sys
import time
import shutil
import logging
import re
from typing import List, Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from TOOLs import mhi
    from TOOLs.mhi import pscad
    from TOOLs import fileUtils as utils
except ImportError:
    print("Warning: TOOLs library not found. PSCAD automation may fail.")

class PSCADCreateCaseService:
    def __init__(self):
        self.pscad_app = None
        self.logger = logging.getLogger(__name__)

    def _launch_pscad(self):
        """Finds and launches the best available PSCAD version."""
        if self.pscad_app:
            return self.pscad_app

        versions = mhi.pscad.versions()
        # Filter versions (Alpha, Beta, 32-bit removal logic from original script)
        vers = [(ver, x64) for ver, x64 in versions if ver != 'Alpha' and ver != 'Beta' and x64]
        if not vers:
            # Fallback if filtering removes everything, though unlikely if installed properly
            vers = versions
            
        # Select version 5 if available
        versions_v5 = [val for val in vers if val[0].startswith('5')]
        
        if versions_v5:
             version, x64 = versions_v5[0]
        elif vers:
             version, x64 = sorted(vers)[-1]
        else:
             raise Exception("No suitable PSCAD version found.")

        # Fortran compiler selection
        fortrans = mhi.pscad.fortran_versions()
        vers = [ver for ver in fortrans if 'GFortran' not in ver]
        if vers:
            fortran = sorted(vers)[-1]
            settings = {'fortran_version': fortran}
            self.pscad_app = mhi.pscad.launch(minimize=True, version=version, x64=x64, settings=settings)
        else:
            self.pscad_app = mhi.pscad.launch(minimize=True, version=version, x64=x64)
            
        return self.pscad_app

    def create_cases(self, project_path: str, original_filename: str, cases_data: List[Any]):
        """
        Creates/Sets up a list of PSCAD cases.
        project_path: Common project directory for all cases
        original_filename: Common base file name
        cases_data: List of objects (Pydantic models) with new_filename, parameters
        """
        pscad = self._launch_pscad()
        results = []

        working_dir = project_path
        source_file_path = os.path.join(working_dir, original_filename)
        
        if not os.path.exists(source_file_path):
             return [{"case": working_dir, "status": "Failed", "error": f"Source file not found: {source_file_path}"}]

        for case in cases_data:
            try:
                new_filename = case.new_filename
                components = case.components # List of PSCADComponent

                new_file_path = os.path.join(working_dir, new_filename)

                shutil.copy2(source_file_path, new_file_path)

                # 2. Load Workspace (if any .pswx exists, load first found)
                try:
                    workspace_files = [f for f in os.listdir(working_dir) if f.endswith(".pswx")]
                    if workspace_files:
                        pscad.load(os.path.join(working_dir, workspace_files[0]))
                except Exception as e:
                    print(f"Workspace load warning: {e}")

                # 3. Unload existing cases to free memory/avoid conflicts
                projects = pscad.projects()
                for prj in projects:
                    if prj['type'] == 'Case':
                        pscad.project(prj['name']).unload()
                        time.sleep(1)

                # 4. Load New Case
                pscad.load(new_file_path)
                
                projects = pscad.projects()
                project_name = os.path.splitext(new_filename)[0]
                project = pscad.project(project_name)
                
                if not project:
                     cases_list = [prj['name'] for prj in projects if prj['type'] == 'Case']
                     if cases_list:
                         project = pscad.project(cases_list[-1])
                
                if not project:
                    raise Exception("Could not get project reference after loading.")

                # 5. Apply Parameters
                for comp_obj in components:
                    iid = comp_obj.id
                    parameters = comp_obj.parameters # Dict
                    
                    try:
                        cmp = project.component(iid)
                        if cmp:
                            cmp.parameters(**parameters)
                        else:
                            print(f"Component ID {iid} not found in {project_name}")
                    except Exception as e:
                         print(f"Error setting param for ID {iid}: {e}")

                project.save()
                
                results.append({"case": new_filename, "status": "Success", "file": new_file_path})
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                results.append({"case": new_filename, "status": "Failed", "error": str(e)})

        # Don't quit PSCAD automatically? Or should we?
        # Original script does not call quit().
        return results
