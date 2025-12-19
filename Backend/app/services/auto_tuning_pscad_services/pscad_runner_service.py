import os
import sys
import logging
import time
from typing import Dict, Any

# Ensure we can import from TOOLs
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

try:
    from TOOLs import mhi
    from TOOLs.mhi import pscad
except ImportError:
    print("Warning: TOOLs library not found. PSCAD runner may fail.")

class PscadRunnerService:
    """
    Dedicated Runner for Auto-Tuning.
    Executes simulations and updates parameters in real-time.
    """
    def __init__(self):
        self.pscad_app = None
        self.logger = logging.getLogger(__name__)

    def _launch_pscad(self):
        """Finds and launches the best available PSCAD version.
           (Duplicated logic from setup service to remain independent)
        """
        if self.pscad_app:
            return self.pscad_app

        versions = mhi.pscad.versions()
        vers = [(ver, x64) for ver, x64 in versions if ver != 'Alpha' and ver != 'Beta' and x64]
        if not vers:
            vers = versions
            
        versions_v5 = [val for val in vers if val[0].startswith('5')]
        
        if versions_v5:
             version, x64 = versions_v5[0]
        elif vers:
             version, x64 = sorted(vers)[-1]
        else:
             raise Exception("No suitable PSCAD version found.")

        fortrans = mhi.pscad.fortran_versions()
        vers = [ver for ver in fortrans if 'GFortran' not in ver]
        if vers:
            fortran = sorted(vers)[-1]
            settings = {'fortran_version': fortran}
            self.pscad_app = mhi.pscad.launch(minimize=True, version=version, x64=x64, settings=settings)
        else:
            self.pscad_app = mhi.pscad.launch(minimize=True, version=version, x64=x64)
            
        return self.pscad_app

    def run_simulation(self, project_name: str):
        """
        Runs the specified PSCAD project (Serial Mode).
        """
        pscad = self._launch_pscad()
        project = pscad.project(project_name)
        
        if not project:
            raise Exception(f"Project '{project_name}' not found loaded in PSCAD.")
            
        print(f"Starting simulation for {project_name}...")
        project.run()
        print(f"Simulation {project_name} finished.")

    def run_simulation_batch(self, project_names: List[str], set_name: str = "AutoTuningSet"):
        """
        Runs a batch of projects in parallel using a Simulation Set.
        """
        pscad = self._launch_pscad()
        
        # 1. Create or Get Simulation Set
        try:
            sim_set = pscad.simulation_set(set_name)
        except Exception:
            # Likely doesn't exist, create it
            sim_set = pscad.create_simulation_set(set_name)
            
        if not sim_set:
            # Double check creation
            sim_set = pscad.create_simulation_set(set_name)

        # 2. Clear existing tasks in set to be safe
        # Note: API remove_tasks takes *tasks. We need to list them first.
        current_tasks = sim_set.list_tasks()
        if current_tasks:
            # remove_tasks expects names or objects. passing names.
            # *current_tasks unpacks the list into arguments
            sim_set.remove_tasks(*current_tasks)

        # 3. Add projects to set
        # Using *project_names to unpack list as arguments
        sim_set.add_tasks(*project_names)
        
        # 4. Run the set
        print(f"Starting parallel simulation for set '{set_name}' with {len(project_names)} cases...")
        try:
            sim_set.run()
            print(f"Simulation set '{set_name}' finished.")
        except Exception as e:
            self.logger.error(f"Simulation Set run failed: {e}")
            raise e

    def update_case_parameters(self, project_name: str, updates: Dict[int, Dict[str, Any]]):
        """
        Updates parameters for specific components in a loaded project.
        updates: Dict where key=ComponentID, value=Dict of parameters to set.
        Example: { 123456: { "R": 10.5 } }
        """
        pscad = self._launch_pscad()
        project = pscad.project(project_name)
        
        if not project:
            return False
            
        for comp_id, params in updates.items():
            try:
                cmp = project.component(comp_id)
                if cmp:
                    cmp.parameters(**params)
                else:
                    self.logger.warning(f"Component {comp_id} not found for update.")
            except Exception as e:
                self.logger.error(f"Failed to update component {comp_id}: {e}")
                
        return True
