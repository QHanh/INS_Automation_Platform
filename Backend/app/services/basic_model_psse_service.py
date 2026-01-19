import os
import math
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

        def get_mbase(bus, gid):
            ierr, mbase = self.psspy.macdat(bus, gid, 'MBASE')
            return mbase if ierr == 0 else 100.0

        def set_gen(bus, gid, pgen, pmax, pmin, qmax=None, qmin=None):
            vals = [self._f] * 17
            vals[0] = pgen
            if qmax is not None:
                vals[2] = qmax
            if qmin is not None:
                vals[3] = qmin
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

        # Calculate Qmax and Qmin based on Mbase and Pmax
        # Formula: Qmax = sqrt(Mbase^2 - Pmax^2), Qmin = -Qmax
        qmax_map = {}
        qmin_map = {}
        for i, bus in enumerate(buses):
            gid = ids[i]
            mbase = get_mbase(bus, gid)
            pmax = abs(pmax_map[(bus, gid)])
            if mbase >= pmax:
                qmax = math.sqrt(mbase**2 - pmax**2)
            else:
                qmax = 0.0
                self._log(f"Warning: Mbase ({mbase:.2f}) < Pmax ({pmax:.2f}) for Gen {bus}-{gid}")
            qmax_map[(bus, gid)] = qmax
            qmin_map[(bus, gid)] = -qmax
            self._log(f"Gen {bus}-{gid}: Mbase = {mbase:.2f}, Qmax = {qmax:.4f}, Qmin = {-qmax:.4f}")

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
            qmax = qmax_map[(bus, gid)]
            qmin = qmin_map[(bus, gid)]
            set_gen(bus, gid, pmin, pmax, pmin, qmax, qmin)  # Pgen = Pmin
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
            qmax = qmax_map[(bus, gid)]
            qmin = qmin_map[(bus, gid)]
            set_gen(bus, gid, pmax, pmax, pmin, qmax, qmin)  # Pgen = Pmax
            set_vsched(bus, vsched_discharge[bus])  # Use Discharge Vsched
            
        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        discharge_path = f"{base_name}_BESS_Discharge.sav"
        self.psspy.save(discharge_path)
        self._log(f"Saved: {discharge_path}")

        return True

    def run_pv_alone(self, cfg: Dict):
        """
        Run PV Alone tuning:
        - Tune P to P_net, Q to 0
        - Pmax = Pgen after tuning
        - Pmin = 0
        - Qmax = sqrt(Mbase^2 - Pmax^2)
        - Qmin = -Qmax
        """
        sav_path = cfg['sav_path']
        bus_from = cfg['bus_from']
        bus_to = cfg['bus_to']
        p_net = cfg['p_net']
        q_target = 0
        pv_gens = cfg.get('pv_generators')

        if not pv_gens:
            self._log("Error: No PV generators provided.")
            return False

        buses = pv_gens['buses']
        ids = pv_gens['ids']
        reg_buses = pv_gens.get('reg_buses', [])
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

        def get_mbase(bus, gid):
            ierr, mbase = self.psspy.macdat(bus, gid, 'MBASE')
            return mbase if ierr == 0 else 100.0

        def set_gen(bus, gid, pgen, pmax, pmin, qmax=None, qmin=None):
            vals = [self._f] * 17
            vals[0] = pgen
            if qmax is not None:
                vals[2] = qmax
            if qmin is not None:
                vals[3] = qmin
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

        # ========== TUNE P and Q ==========
        self._log("--- Tuning for PV (P = P_net, Q = 0) ---")
        self._log(f"Target P: {p_net} MW, Q: {q_target} Mvar")
        
        ok_p = tuner.tune_p(bus_from, bus_to, buses, ids, p_net)
        if not ok_p: 
            self._log("Error tuning P for PV.")
            return False
        
        ok_q = tuner.tune_q(bus_from, bus_to, buses, reg_buses, q_target)
        if not ok_q:
            self._log("Error tuning Q for PV.")
            return False
        
        # Re-tune P after Q adjustment
        self._log("--- Re-tuning P for PV ---")
        ok_p2 = tuner.tune_p(bus_from, bus_to, buses, ids, p_net)
        if not ok_p2:
            self._log("Error re-tuning P for PV.")
            return False

        # Store Pmax (= Pgen after tuning) and Vsched
        pmax_map = {}
        vsched_map = {}
        for i, bus in enumerate(buses):
            gid = ids[i]
            pmax_map[(bus, gid)] = get_p_gen(bus, gid)
            vsched_map[bus] = get_vsched(bus)
            self._log(f"Gen {bus}-{gid}: Pmax = {pmax_map[(bus, gid)]:.4f}, Vsched = {vsched_map[bus]:.4f}")

        # Calculate Qmax and Qmin based on Mbase and Pmax
        # Formula: Qmax = sqrt(Mbase^2 - Pmax^2), Qmin = -Qmax
        qmax_map = {}
        qmin_map = {}
        for i, bus in enumerate(buses):
            gid = ids[i]
            mbase = get_mbase(bus, gid)
            pmax = abs(pmax_map[(bus, gid)])
            if mbase >= pmax:
                qmax = math.sqrt(mbase**2 - pmax**2)
            else:
                qmax = 0.0
                self._log(f"Warning: Mbase ({mbase:.2f}) < Pmax ({pmax:.2f}) for Gen {bus}-{gid}")
            qmax_map[(bus, gid)] = qmax
            qmin_map[(bus, gid)] = -qmax
            self._log(f"Gen {bus}-{gid}: Mbase = {mbase:.2f}, Qmax = {qmax:.4f}, Qmin = {-qmax:.4f}")

        base_name = os.path.splitext(sav_path)[0]

        # ========== Create PV SAV File ==========
        self._log("--- Creating _PV.sav ---")
        for i, bus in enumerate(buses):
            gid = ids[i]
            pmax = pmax_map[(bus, gid)]
            pmin = 0.0  # PV Pmin = 0
            qmax = qmax_map[(bus, gid)]
            qmin = qmin_map[(bus, gid)]
            set_gen(bus, gid, pmax, pmax, pmin, qmax, qmin)  # Pgen = Pmax
            set_vsched(bus, vsched_map[bus])
        
        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        pv_path = f"{base_name}_PV.sav"
        self.psspy.save(pv_path)
        self._log(f"Saved: {pv_path}")

        return True

    def run_hybrid(self, cfg: Dict):
        """
        Run HYBRID (PV + BESS) tuning - generates 5 SAV files:
        1. PV + BESS Discharge
        2. PV + BESS Charge
        3. PV Only (BESS disabled)
        4. BESS Discharge Only (PV disabled)
        5. BESS Charge Only (PV disabled)
        """
        sav_path = cfg['sav_path']
        bus_from = cfg['bus_from']
        bus_to = cfg['bus_to']
        p_net = cfg['p_net']
        q_target = 0
        
        pv_gens = cfg.get('pv_generators')
        bess_gens = cfg.get('bess_generators')

        if not pv_gens:
            self._log("Error: No PV generators provided for HYBRID.")
            return False
        if not bess_gens:
            self._log("Error: No BESS generators provided for HYBRID.")
            return False

        pv_buses = pv_gens['buses']
        pv_ids = pv_gens['ids']
        pv_reg_buses = pv_gens.get('reg_buses', pv_buses)

        bess_buses = bess_gens['buses']
        bess_ids = bess_gens['ids']
        bess_reg_buses = bess_gens.get('reg_buses', bess_buses)

        # Combined lists for when both PV and BESS are active
        all_buses = pv_buses + bess_buses
        all_ids = pv_ids + bess_ids
        all_reg_buses = pv_reg_buses + bess_reg_buses

        if not self._init_psse(): return False

        def get_p_gen(bus, gid):
            ierr, p = self.psspy.macdat(bus, gid, 'P')
            return p if ierr == 0 else 0.0

        def get_vsched(bus):
            ierr, vs = self.psspy.busdat(bus, 'PU')
            return vs if ierr == 0 else 1.0

        def get_mbase(bus, gid):
            ierr, mbase = self.psspy.macdat(bus, gid, 'MBASE')
            return mbase if ierr == 0 else 100.0

        def set_gen(bus, gid, pgen, pmax, pmin, qmax=None, qmin=None):
            vals = [self._f] * 17
            vals[0] = pgen
            if qmax is not None:
                vals[2] = qmax
            if qmin is not None:
                vals[3] = qmin
            vals[4] = pmax
            vals[5] = pmin
            self.psspy.machine_chng_4(bus, gid, [self._i]*7, vals, "")

        def set_vsched(bus, vs):
            self.psspy.plant_chng_4(bus, 0, [self._i, 0], [vs, 100.0])

        def calc_qmax(bus, gid, pmax_val):
            mbase = get_mbase(bus, gid)
            pmax_abs = abs(pmax_val)
            if mbase >= pmax_abs:
                qmax = math.sqrt(mbase**2 - pmax_abs**2)
            else:
                qmax = 0.0
                self._log(f"Warning: Mbase ({mbase:.2f}) < Pmax ({pmax_abs:.2f}) for Gen {bus}-{gid}")
            return qmax

        base_name = os.path.splitext(sav_path)[0]
        tuner = PSSETuningService(sav_path)

        # ========================================================================
        # CASE 1 & 2: PV + BESS (Discharge / Charge)
        # ========================================================================
        self._log("=" * 60)
        self._log("CASE 1 & 2: PV + BESS Combined")
        self._log("=" * 60)
        
        self.psspy.case(sav_path)
        tuner.psspy = self.psspy
        tuner._i = self._i
        tuner._f = self._f
        tuner.logs = []

        # --- Tune for DISCHARGE (P = +P_net) ---
        self._log("--- Tuning for PV + BESS Discharge ---")
        self._log(f"Target P: {p_net} MW, Q: {q_target} Mvar")
        
        ok = tuner.tune_p(bus_from, bus_to, all_buses, all_ids, p_net)
        if not ok: 
            self._log("Error tuning P for PV+BESS Discharge.")
            return False
        ok = tuner.tune_q(bus_from, bus_to, all_buses, all_reg_buses, q_target)
        if not ok:
            self._log("Error tuning Q for PV+BESS Discharge.")
            return False
        self._log("--- Re-tuning P for PV + BESS Discharge ---")
        ok = tuner.tune_p(bus_from, bus_to, all_buses, all_ids, p_net)
        if not ok:
            self._log("Error re-tuning P for PV+BESS Discharge.")
            return False

        # Store discharge values
        pmax_all = {}
        vsched_discharge = {}
        for i, bus in enumerate(all_buses):
            gid = all_ids[i]
            pmax_all[(bus, gid)] = get_p_gen(bus, gid)
            vsched_discharge[bus] = get_vsched(bus)
            self._log(f"Gen {bus}-{gid}: Pmax = {pmax_all[(bus, gid)]:.4f}, Vsched = {vsched_discharge[bus]:.4f}")

        # --- Tune for CHARGE (P = -P_net), only BESS changes sign ---
        self._log("--- Tuning for PV + BESS Charge ---")
        # For charge: PV still at P_net, BESS at -P_net (charging)
        # Total flow = PV_P - BESS_P (BESS absorbing)
        # We tune BESS to charge while PV still generates
        p_charge_bess = -1.0 * p_net
        self._log(f"Target BESS P: {p_charge_bess} MW")

        ok = tuner.tune_p(bus_from, bus_to, bess_buses, bess_ids, p_charge_bess)
        if not ok:
            self._log("Error tuning P for BESS Charge.")
            return False
        ok = tuner.tune_q(bus_from, bus_to, all_buses, all_reg_buses, q_target)
        if not ok:
            self._log("Error tuning Q for PV+BESS Charge.")
            return False
        self._log("--- Re-tuning P for BESS Charge ---")
        ok = tuner.tune_p(bus_from, bus_to, bess_buses, bess_ids, p_charge_bess)
        if not ok:
            self._log("Error re-tuning P for BESS Charge.")
            return False

        # Store charge values (for BESS Pmin)
        pmin_bess = {}
        vsched_charge = {}
        for i, bus in enumerate(bess_buses):
            gid = bess_ids[i]
            pmin_bess[(bus, gid)] = get_p_gen(bus, gid)
            vsched_charge[bus] = get_vsched(bus)
            self._log(f"BESS Gen {bus}-{gid}: Pmin = {pmin_bess[(bus, gid)]:.4f}, Vsched = {vsched_charge[bus]:.4f}")

        # Calculate Qmax/Qmin for all generators
        qmax_all = {}
        qmin_all = {}
        for i, bus in enumerate(all_buses):
            gid = all_ids[i]
            qmax_all[(bus, gid)] = calc_qmax(bus, gid, pmax_all[(bus, gid)])
            qmin_all[(bus, gid)] = -qmax_all[(bus, gid)]
            self._log(f"Gen {bus}-{gid}: Qmax = {qmax_all[(bus, gid)]:.4f}, Qmin = {qmin_all[(bus, gid)]:.4f}")

        # --- Save CASE 1: PV + BESS Discharge ---
        self._log("--- Creating _HYBRID_PV_BESS_Discharge.sav ---")
        self.psspy.case(sav_path)
        # Set PV generators
        for i, bus in enumerate(pv_buses):
            gid = pv_ids[i]
            pmax = pmax_all[(bus, gid)]
            set_gen(bus, gid, pmax, pmax, 0.0, qmax_all[(bus, gid)], qmin_all[(bus, gid)])
            set_vsched(bus, vsched_discharge[bus])
        # Set BESS generators (Discharge: Pgen = Pmax)
        for i, bus in enumerate(bess_buses):
            gid = bess_ids[i]
            pmax = pmax_all[(bus, gid)]
            pmin = pmin_bess[(bus, gid)]
            set_gen(bus, gid, pmax, pmax, pmin, qmax_all[(bus, gid)], qmin_all[(bus, gid)])
            set_vsched(bus, vsched_discharge[bus])
        
        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        self.psspy.save(f"{base_name}_HYBRID_PV_BESS_Discharge.sav")
        self._log(f"Saved: {base_name}_HYBRID_PV_BESS_Discharge.sav")

        # --- Save CASE 2: PV + BESS Charge ---
        self._log("--- Creating _HYBRID_PV_BESS_Charge.sav ---")
        self.psspy.case(sav_path)
        # Set PV generators (same as discharge)
        for i, bus in enumerate(pv_buses):
            gid = pv_ids[i]
            pmax = pmax_all[(bus, gid)]
            set_gen(bus, gid, pmax, pmax, 0.0, qmax_all[(bus, gid)], qmin_all[(bus, gid)])
            set_vsched(bus, vsched_discharge[bus])
        # Set BESS generators (Charge: Pgen = Pmin)
        for i, bus in enumerate(bess_buses):
            gid = bess_ids[i]
            pmax = pmax_all[(bus, gid)]
            pmin = pmin_bess[(bus, gid)]
            set_gen(bus, gid, pmin, pmax, pmin, qmax_all[(bus, gid)], qmin_all[(bus, gid)])
            set_vsched(bus, vsched_charge[bus])
        
        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        self.psspy.save(f"{base_name}_HYBRID_PV_BESS_Charge.sav")
        self._log(f"Saved: {base_name}_HYBRID_PV_BESS_Charge.sav")

        # ========================================================================
        # CASE 3: PV Only (BESS disabled)
        # ========================================================================
        self._log("=" * 60)
        self._log("CASE 3: PV Only (BESS Disabled)")
        self._log("=" * 60)
        
        self.psspy.case(sav_path)
        tuner.psspy = self.psspy
        tuner.logs = []

        # Disable BESS generators
        self._log("Disabling BESS generators...")
        self.disable_generators(bess_buses, bess_ids)

        # Tune PV
        self._log(f"--- Tuning PV to P_net = {p_net} MW ---")
        ok = tuner.tune_p(bus_from, bus_to, pv_buses, pv_ids, p_net)
        if not ok:
            self._log("Error tuning P for PV Only.")
            return False
        ok = tuner.tune_q(bus_from, bus_to, pv_buses, pv_reg_buses, q_target)
        if not ok:
            self._log("Error tuning Q for PV Only.")
            return False
        self._log("--- Re-tuning P for PV Only ---")
        ok = tuner.tune_p(bus_from, bus_to, pv_buses, pv_ids, p_net)
        if not ok:
            self._log("Error re-tuning P for PV Only.")
            return False

        # Store PV values
        pmax_pv = {}
        vsched_pv = {}
        for i, bus in enumerate(pv_buses):
            gid = pv_ids[i]
            pmax_pv[(bus, gid)] = get_p_gen(bus, gid)
            vsched_pv[bus] = get_vsched(bus)
        
        # Set PV generators
        for i, bus in enumerate(pv_buses):
            gid = pv_ids[i]
            pmax = pmax_pv[(bus, gid)]
            qmax = calc_qmax(bus, gid, pmax)
            set_gen(bus, gid, pmax, pmax, 0.0, qmax, -qmax)
            set_vsched(bus, vsched_pv[bus])
            self._log(f"PV Gen {bus}-{gid}: Pmax = {pmax:.4f}, Qmax = {qmax:.4f}")

        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        self.psspy.save(f"{base_name}_HYBRID_PV_Only.sav")
        self._log(f"Saved: {base_name}_HYBRID_PV_Only.sav")

        # ========================================================================
        # CASE 4 & 5: BESS Only (PV disabled) - Discharge / Charge
        # ========================================================================
        self._log("=" * 60)
        self._log("CASE 4 & 5: BESS Only (PV Disabled)")
        self._log("=" * 60)
        
        self.psspy.case(sav_path)
        tuner.psspy = self.psspy
        tuner.logs = []

        # Disable PV generators
        self._log("Disabling PV generators...")
        self.disable_generators(pv_buses, pv_ids)

        # --- Tune BESS Discharge ---
        self._log(f"--- Tuning BESS Discharge to P_net = {p_net} MW ---")
        ok = tuner.tune_p(bus_from, bus_to, bess_buses, bess_ids, p_net)
        if not ok:
            self._log("Error tuning P for BESS Discharge Only.")
            return False
        ok = tuner.tune_q(bus_from, bus_to, bess_buses, bess_reg_buses, q_target)
        if not ok:
            self._log("Error tuning Q for BESS Discharge Only.")
            return False
        self._log("--- Re-tuning P for BESS Discharge Only ---")
        ok = tuner.tune_p(bus_from, bus_to, bess_buses, bess_ids, p_net)
        if not ok:
            self._log("Error re-tuning P for BESS Discharge Only.")
            return False

        # Store BESS Discharge values
        pmax_bess_only = {}
        vsched_bess_disch = {}
        for i, bus in enumerate(bess_buses):
            gid = bess_ids[i]
            pmax_bess_only[(bus, gid)] = get_p_gen(bus, gid)
            vsched_bess_disch[bus] = get_vsched(bus)
            self._log(f"BESS Gen {bus}-{gid}: Pmax = {pmax_bess_only[(bus, gid)]:.4f}")

        # --- Tune BESS Charge ---
        self._log(f"--- Tuning BESS Charge to P = {-p_net} MW ---")
        ok = tuner.tune_p(bus_from, bus_to, bess_buses, bess_ids, -p_net)
        if not ok:
            self._log("Error tuning P for BESS Charge Only.")
            return False
        ok = tuner.tune_q(bus_from, bus_to, bess_buses, bess_reg_buses, q_target)
        if not ok:
            self._log("Error tuning Q for BESS Charge Only.")
            return False
        self._log("--- Re-tuning P for BESS Charge Only ---")
        ok = tuner.tune_p(bus_from, bus_to, bess_buses, bess_ids, -p_net)
        if not ok:
            self._log("Error re-tuning P for BESS Charge Only.")
            return False

        # Store BESS Charge values
        pmin_bess_only = {}
        vsched_bess_chg = {}
        for i, bus in enumerate(bess_buses):
            gid = bess_ids[i]
            pmin_bess_only[(bus, gid)] = get_p_gen(bus, gid)
            vsched_bess_chg[bus] = get_vsched(bus)
            self._log(f"BESS Gen {bus}-{gid}: Pmin = {pmin_bess_only[(bus, gid)]:.4f}")

        # Calculate Qmax/Qmin for BESS only
        qmax_bess_only = {}
        for i, bus in enumerate(bess_buses):
            gid = bess_ids[i]
            qmax_bess_only[(bus, gid)] = calc_qmax(bus, gid, pmax_bess_only[(bus, gid)])
            self._log(f"BESS Gen {bus}-{gid}: Qmax = {qmax_bess_only[(bus, gid)]:.4f}")

        # --- Save CASE 4: BESS Discharge Only ---
        self._log("--- Creating _HYBRID_BESS_Discharge.sav ---")
        self.psspy.case(sav_path)
        self.disable_generators(pv_buses, pv_ids)
        
        for i, bus in enumerate(bess_buses):
            gid = bess_ids[i]
            pmax = pmax_bess_only[(bus, gid)]
            pmin = pmin_bess_only[(bus, gid)]
            qmax = qmax_bess_only[(bus, gid)]
            set_gen(bus, gid, pmax, pmax, pmin, qmax, -qmax)
            set_vsched(bus, vsched_bess_disch[bus])

        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        self.psspy.save(f"{base_name}_HYBRID_BESS_Discharge.sav")
        self._log(f"Saved: {base_name}_HYBRID_BESS_Discharge.sav")

        # --- Save CASE 5: BESS Charge Only ---
        self._log("--- Creating _HYBRID_BESS_Charge.sav ---")
        self.psspy.case(sav_path)
        self.disable_generators(pv_buses, pv_ids)
        
        for i, bus in enumerate(bess_buses):
            gid = bess_ids[i]
            pmax = pmax_bess_only[(bus, gid)]
            pmin = pmin_bess_only[(bus, gid)]
            qmax = qmax_bess_only[(bus, gid)]
            set_gen(bus, gid, pmin, pmax, pmin, qmax, -qmax)
            set_vsched(bus, vsched_bess_chg[bus])

        self.psspy.fnsl([1,1,0,0,1,1,0,0])
        self.psspy.save(f"{base_name}_HYBRID_BESS_Charge.sav")
        self._log(f"Saved: {base_name}_HYBRID_BESS_Charge.sav")

        self._log("=" * 60)
        self._log("HYBRID completed - 5 files generated!")
        self._log("=" * 60)

        return True
