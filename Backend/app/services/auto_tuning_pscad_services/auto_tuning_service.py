import logging
import os
from typing import TypedDict, Annotated, List, Dict, Any, Union
from langgraph.graph import StateGraph, END

from app.services.auto_tuning_pscad_services.pscad_runner_service import PscadRunnerService
from app.services.auto_tuning_pscad_services.pscad_result_service import PscadResultService

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Define Output Structure for Parser
class TunerDecision(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning for the parameter change")
    suggested_params: Dict[str, float] = Field(description="Dictionary of new parameter values")

# Define State
class TuningState(TypedDict):
    project_path: str
    case_name: str
    goal: Dict[str, Any]
    param_def: Dict[str, Dict[str, Any]] # ParamDef mapping
    
    current_params: Dict[str, float]
    history: List[Dict]
    
    metrics: Dict[str, Any]
    summary: str
    reasoning: str
    
    iteration: int
    max_iterations: int
    status: str
    error: str

class AutoTuningService:
    """
    The Tuner Orchestrator powered by LangGraph & LangChain.
    Nodes: 
    1. Runner: Applies params & runs simulation.
    2. Analyst: Parses output & summarized.
    3. Tuner (AI): Decides new params using Gemini Pro.
    """
    def __init__(self):
        self.runner = PscadRunnerService()
        self.analyst = PscadResultService()
        self.logger = logging.getLogger(__name__)
        
        # Initialize native LangChain Model
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.logger.warning("GEMINI_API_KEY missing.")
            
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.2, # Low temperature for engineering tasks
            google_api_key=api_key,
            convert_system_message_to_human=True
        )
        self.parser = JsonOutputParser(pydantic_object=TunerDecision)

        # Build Graph
        self.app = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(TuningState)
        
        # Add Nodes
        workflow.add_node("runner_node", self.runner_node)
        workflow.add_node("analyst_node", self.analyst_node)
        workflow.add_node("tuner_node", self.tuner_node)
        
        # Set Entry Point
        workflow.set_entry_point("runner_node")
        
        # Add Edges
        # Runner -> Analyst
        workflow.add_edge("runner_node", "analyst_node")
        
        # Analyst -> Tuner
        workflow.add_edge("analyst_node", "tuner_node")
        
        # Tuner -> Loop check
        workflow.add_conditional_edges(
            "tuner_node",
            self.check_continuation,
            {
                "continue": "runner_node",
                "stop": END
            }
        )
        
        return workflow.compile()

    # --- Node Implementations ---
    
    def runner_node(self, state: TuningState) -> Dict:
        """
        Applies current_params to PSCAD and runs simulation.
        """
        print(f"--- Iteration {state['iteration'] + 1} ---")
        print(f"Applying Params: {state['current_params']}")
        
        # 0. Apply Params
        updates = {}
        for p_name, p_val in state['current_params'].items():
            if p_name in state['param_def']:
                comp_id = state['param_def'][p_name]['id']
                real_name = state['param_def'][p_name]['name']
                if comp_id not in updates: updates[comp_id] = {}
                updates[comp_id][real_name] = p_val
        
        if updates:
            self.runner.update_case_parameters(state['case_name'], updates)
            
        # 1. Run Simulation
        print("Running Simulation...")
        try:
            self.runner.run_simulation(state['case_name'])
            return {"status": "simulated"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def analyst_node(self, state: TuningState) -> Dict:
        """
        Parses results and generates summary.
        """
        if state.get("status") == "failed":
            return {} # Pass through failure

        metrics = self.analyst.parse_result(state['project_path'], state['case_name'])
        
        if "error" in metrics:
             return {"status": "failed", "error": metrics['error'], "metrics": metrics}

        summary = self.analyst.analyze_metrics(metrics, state['goal'])
        print(f"Analysis: {summary}")
        
        return {
            "metrics": metrics,
            "summary": summary
        }

    def tuner_node(self, state: TuningState) -> Dict:
        """
        AI decides next steps.
        """
        if state.get("status") == "failed":
             return {}

        prompt_text = (
            f"You are a control systems expert tuning a PSCAD simulation.\n"
            f"Goal: {state['goal']}\n"
            f"Current Output: {state['summary']}\n"
            f"Current Params: {state['current_params']}\n"
            f"History: {state['history']}\n"
            f"Suggest new parameters conservatively.\n"
            f"{self.parser.get_format_instructions()}"
        )
        
        print("Consulting AI...")
        try:
            msg = HumanMessage(content=prompt_text)
            response = self.llm.invoke([msg])
            parsed_result = self.parser.parse(response.content)
            
            new_params = parsed_result.get("suggested_params", {})
            reasoning = parsed_result.get("reasoning", "")
            
            print(f"AI Suggestion: {new_params}")
            print(f"Reasoning: {reasoning}")
            
            # Update history logic
            history_item = {
                "iteration": state['iteration'],
                "params": state['current_params'].copy(),
                "metrics": state['metrics'],
                "reasoning": reasoning
            }
            
            # Prepare next params
            updated_params = state['current_params'].copy()
            updated_params.update(new_params)
            
            return {
                "history": state['history'] + [history_item],
                "current_params": updated_params,
                "reasoning": reasoning,
                "iteration": state['iteration'] + 1,
                "status": "stop" if not new_params else "continue"
            }
            
        except Exception as e:
            print(f"AI Generation Failed: {e}")
            return {"status": "failed", "error": str(e)}

    def check_continuation(self, state: TuningState):
        if state.get("status") == "failed":
            return "stop"
        if state['iteration'] >= state['max_iterations']:
            print("Max iterations reached.")
            return "stop"
        if state['status'] == "stop":
            return "stop"
        
        return "continue"

    # --- Public API ---

    def tune_case(self, project_path: str, case_name: str, goal: Dict, initial_params: Dict, param_def: Dict):
        """
        Invokes the LangGraph workflow.
        """
        initial_state: TuningState = {
            "project_path": project_path,
            "case_name": case_name,
            "goal": goal,
            "param_def": param_def,
            "current_params": initial_params,
            "history": [],
            "metrics": {},
            "summary": "",
            "reasoning": "",
            "iteration": 0,
            "max_iterations": 5,
            "status": "start",
            "error": ""
        }
        
        final_state = self.app.invoke(initial_state)
        return final_state
