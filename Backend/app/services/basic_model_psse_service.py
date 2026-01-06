import os
import shutil
from typing import Dict, List, Optional
from app.services.tuning_psse_service import PSSETuningService

class BasicModelService:
    def __init__(self, log_cb=None):
        self.log_cb = log_cb if log_cb else lambda x: print(x)
        self.psspy = None
        self._i = None
        self._f = None

    def _log(self, msg: str):
        self.log_cb(msg)

    def _init_psse(self):
        try:
            import psse35
            import psspy
            import redirect
            redirect.psse2py()
            psspy.psseinit(10000)
            self.psspy = psspy
            self._i = psspy.getdefaultint()
            self._f = psspy.getdefaultreal()
            return True
        except Exception as e:
            self._log(f"Error initializing PSSE: {e}")
            return False

    def disable_generators(self, buses: List[int], ids: List[str]):
        """Disable generators by setting status to 0"""
        for i, bus in enumerate(buses):
            gid = ids[i] if i < len(ids) else "1"
            # machine_chng_4 status is index 0 in intgar
            intgar = [self._i] * 7
            intgar[0] = 0 # Status = 0 (out of service)
            
            ierr = self.psspy.machine_chng_4(bus, gid, intgar, [self._f]*17, "")
            if ierr > 0:
                self._log(f"Warning: Failed to disable generator {gid} at bus {bus} (Error {ierr})")

    def run_bess_alone(self, cfg: Dict):
        sav_path = cfg['sav_path']
        bus_from = cfg['bus_from']
        bus_to = cfg['bus_to']
        p_net = cfg['p_net']
        q_target = 0
        bess_gens = cfg.get('bess_generators') # GeneratorGroup dict

        if not bess_gens:
            self._log("Error: No BESS generators provided.")
            return False

        buses = bess_gens['buses']
        ids = bess_gens['ids']
        reg_buses = bess_gens.get('reg_buses', [])
        if not reg_buses: reg_buses = buses # default to same bus if not provided

        # Initialize PSSE
        if not self._init_psse(): return False
        
        # Load Case
        self._log(f"Loading {sav_path}...")
        self.psspy.case(sav_path)

        # Helper to get current P GEN
        def get_p_gen(bus, gid):
             ierr, p = self.psspy.macdat(bus, gid, 'P')
             return p if ierr == 0 else 0.0

        # Helper to set Pmax/Pmin
        def set_limits(bus, gid, pmax, pmin):
             realar = [self._f] * 17
             realar[4] = pmax
             realar[5] = pmin
             self.psspy.machine_chng_4(bus, gid, [self._i]*7, realar, "")

        # Helper to set P
        def set_p(bus, gid, p):
             realar = [self._f] * 17
             realar[0] = p
             self.psspy.machine_chng_4(bus, gid, [self._i]*7, realar, "")

        tuner = PSSETuningService(sav_path)
        tuner.psspy = self.psspy
        tuner._i = self._i
        tuner._f = self._f
        tuner.logs = []

        self._log("--- Tuning for Discharge (P = +P_net) ---")
        self._log(f"Target P: {p_net} MW, Q: {q_target} Mvar")
        
        ok_p = tuner.tune_p(bus_from, bus_to, buses, ids, p_net)
        if not ok_p: 
             self._log("Error tuning P for Discharge.")
             return False
        
        ok_q = tuner.tune_q(bus_from, bus_to, buses, reg_buses, q_target)
        if not ok_q:
             self._log("Error tuning Q for Discharge.")
             return False

        pmax_map = {}
        for i, bus in enumerate(buses):
            gid = ids[i]
            val = get_p_gen(bus, gid)
            pmax_map[(bus, gid)] = val
            self._log(f"Gen {bus}-{gid}: Set Pmax = {val:.4f}")

        self._log("--- Tuning for Charge (P = -P_net) ---")
        p_charge = -1.0 * p_net
        self._log(f"Target P: {p_charge} MW, Q: {q_target} Mvar")

        ok_p_charge = tuner.tune_p(bus_from, bus_to, buses, ids, p_charge)
        if not ok_p_charge:
             self._log("Error tuning P for Charge.")
             return False
        
        ok_q_charge = tuner.tune_q(bus_from, bus_to, buses, reg_buses, q_target)
        if not ok_q_charge:
             self._log("Error tuning Q for Charge.")
             return False
        
        pmin_map = {}
        for i, bus in enumerate(buses):
            gid = ids[i]
            val = get_p_gen(bus, gid)
            pmin_map[(bus, gid)] = val
            self._log(f"Gen {bus}-{gid}: Set Pmin = {val:.4f}")

        self._log("--- creating _BESS_Charge.sav ---")
        for i, bus in enumerate(buses):
            gid = ids[i]
            pmax = pmax_map[(bus, gid)]
            pmin = pmin_map[(bus, gid)]
            set_limits(bus, gid, pmax, pmin)
            pass
        
        def update_gen(bus, gid, pgen, pmax, pmin):             
            vals = [self._f] * 17
            vals[0] = pgen
            vals[4] = pmax
            vals[5] = pmin
            
            myspy_int = [self._i] * 7
            
            self.psspy.machine_chng_4(bus, gid, myspy_int, vals, "")

        # Create Charge
        for i, bus in enumerate(buses):
            gid = ids[i]
            update_gen(bus, gid, pmin_map[(bus, gid)], pmax_map[(bus, gid)], pmin_map[(bus, gid)])
        
        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        base_name = os.path.splitext(sav_path)[0]
        charge_path = f"{base_name}_BESS_Charge.sav"
        self.psspy.save(charge_path)
        self._log(f"Saved: {charge_path}")

        # --- STEP 4: Create Discharge File ---
        self._log("--- creating _BESS_Discharge.sav ---")
        for i, bus in enumerate(buses):
            gid = ids[i]
            update_gen(bus, gid, pmax_map[(bus, gid)], pmax_map[(bus, gid)], pmin_map[(bus, gid)])
            
        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        discharge_path = f"{base_name}_BESS_Discharge.sav"
        self.psspy.save(discharge_path)
        self._log(f"Saved: {discharge_path}")

        return True
