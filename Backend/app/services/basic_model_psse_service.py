import os
from typing import Dict, List
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
            intgar = [self._i] * 7
            intgar[0] = 0
            ierr = self.psspy.machine_chng_4(bus, gid, intgar, [self._f]*17, "")
            if ierr > 0:
                self._log(f"Warning: Failed to disable generator {gid} at bus {bus} (Error {ierr})")

    def run_bess_alone(self, cfg: Dict):
        sav_path = cfg['sav_path']
        bus_from = cfg['bus_from']
        bus_to = cfg['bus_to']
        p_net = cfg['p_net']
        q_target = 0
        bess_gens = cfg.get('bess_generators')

        if not bess_gens:
            self._log("Error: No BESS generators provided.")
            return False

        buses = bess_gens['buses']
        ids = bess_gens['ids']
        reg_buses = bess_gens.get('reg_buses', [])
        if not reg_buses: reg_buses = buses

        if not self._init_psse(): return False
        
        self._log(f"Loading {sav_path}...")
        self.psspy.case(sav_path)

        def get_p_gen(bus, gid):
            ierr, p = self.psspy.macdat(bus, gid, 'P')
            return p if ierr == 0 else 0.0

        def get_vsched(bus):
            ierr, vs = self.psspy.busdat(bus, 'PU')
            return vs if ierr == 0 else 1.0

        def set_gen(bus, gid, pgen, pmax, pmin):
            vals = [self._f] * 17
            vals[0] = pgen
            vals[4] = pmax
            vals[5] = pmin
            self.psspy.machine_chng_4(bus, gid, [self._i]*7, vals, "")

        def set_vsched(bus, vs):
            self.psspy.plant_chng_4(bus, 0, [self._i, 0], [vs, 100.0])

        tuner = PSSETuningService(sav_path)
        tuner.psspy = self.psspy
        tuner._i = self._i
        tuner._f = self._f
        tuner.logs = []

        # ========== DISCHARGE ==========
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
        
        # Re-tune P after Q adjustment
        self._log("--- Re-tuning P for Discharge ---")
        ok_p2 = tuner.tune_p(bus_from, bus_to, buses, ids, p_net)
        if not ok_p2:
            self._log("Error re-tuning P for Discharge.")
            return False

        # Store Pmax and Vsched for Discharge
        pmax_map = {}
        vsched_discharge = {}
        for i, bus in enumerate(buses):
            gid = ids[i]
            pmax_map[(bus, gid)] = get_p_gen(bus, gid)
            vsched_discharge[bus] = get_vsched(bus)
            self._log(f"Gen {bus}-{gid}: Pmax = {pmax_map[(bus, gid)]:.4f}, Vsched = {vsched_discharge[bus]:.4f}")

        # ========== CHARGE ==========
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
        
        # Re-tune P after Q adjustment
        self._log("--- Re-tuning P for Charge ---")
        ok_p_charge2 = tuner.tune_p(bus_from, bus_to, buses, ids, p_charge)
        if not ok_p_charge2:
            self._log("Error re-tuning P for Charge.")
            return False
        
        # Store Pmin and Vsched for Charge
        pmin_map = {}
        vsched_charge = {}
        for i, bus in enumerate(buses):
            gid = ids[i]
            pmin_map[(bus, gid)] = get_p_gen(bus, gid)
            vsched_charge[bus] = get_vsched(bus)
            self._log(f"Gen {bus}-{gid}: Pmin = {pmin_map[(bus, gid)]:.4f}, Vsched = {vsched_charge[bus]:.4f}")

        base_name = os.path.splitext(sav_path)[0]

        # ========== Create Charge File ==========
        self._log("--- Creating _BESS_Charge.sav ---")
        for i, bus in enumerate(buses):
            gid = ids[i]
            pmax = pmax_map[(bus, gid)]
            pmin = pmin_map[(bus, gid)]
            set_gen(bus, gid, pmin, pmax, pmin)  # Pgen = Pmin
            set_vsched(bus, vsched_charge[bus])  # Use Charge Vsched
        
        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        charge_path = f"{base_name}_BESS_Charge.sav"
        self.psspy.save(charge_path)
        self._log(f"Saved: {charge_path}")

        # ========== Create Discharge File ==========
        self._log("--- Creating _BESS_Discharge.sav ---")
        for i, bus in enumerate(buses):
            gid = ids[i]
            pmax = pmax_map[(bus, gid)]
            pmin = pmin_map[(bus, gid)]
            set_gen(bus, gid, pmax, pmax, pmin)  # Pgen = Pmax
            set_vsched(bus, vsched_discharge[bus])  # Use Discharge Vsched
            
        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        discharge_path = f"{base_name}_BESS_Discharge.sav"
        self.psspy.save(discharge_path)
        self._log(f"Saved: {discharge_path}")

        return True
