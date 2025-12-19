import os
import re
import pandas as pd
from typing import Dict, Any, List

class PscadResultService:
    """
    The Analyst Agent.
    Responsibilities:
    1. Parse PSCAD output files (.out, .inf).
    2. Extract key metrics (Overshoot, Settling Time, Steady State Error).
    3. Return structured data for the Tuner Agent.
    """

    def parse_result(self, case_directory: str, project_name: str) -> Dict[str, Any]:
        """
        Parses simulation results from the specified directory.
        Assumes standard PSCAD output naming convention: project_name_XX.out
        """
        out_files = [f for f in os.listdir(case_directory) if f.startswith(project_name) and f.endswith(".out")]
        if not out_files:
             return {"error": f"No output files found for {project_name} in {case_directory}"}
        
        # Combine .out files if multiple (PSCAD splits them sometimes)
        # For simplicity, assuming standard format or just taking the first one for now
        # Ideally, we read the .inf file to map columns. 
        
        # TODO: Implement robust .inf parsing to map columns
        # For now, let's look for a generic export CSV if available or just raw parsing.
        
        try:
             # Basic implementation: Read all .out files into one dataframe (assuming time aligned)
             dfs = []
             for f in sorted(out_files):
                 path = os.path.join(case_directory, f)
                 # PSCAD .out files are space separated, sometimes with headers or without
                 # Skipping robust parsing for this skeleton, assuming standard structure
                 df = pd.read_csv(path, sep=r'\s+', header=None) 
                 dfs.append(df)
            
             if not dfs:
                 return {"error": "Empty data output"}

             # Extract basic stats provided we know column layout (which we don't yet without .inf)
             # This is a placeholder for the actual extraction logic
             
             summary = {
                 "max_voltage": 0.0, # Placeholder
                 "settling_time": 0.0, # Placeholder
                 "overshoot": 0.0 # Placeholder
             }
             
             return {"status": "success", "metrics": summary}

        except Exception as e:
            return {"error": str(e)}

    def analyze_metrics(self, metrics: Dict[str, Any], goal: Dict[str, Any]) -> str:
        """
        Generates a natural language summary for the Tuner Agent (LLM).
        """
        if "error" in metrics:
            return f"Analysis Failed: {metrics['error']}"
            
        return f"Simulation complete. Max Voltage: {metrics.get('metrics',{}).get('max_voltage')}. Overshoot: {metrics.get('metrics',{}).get('overshoot')}."
