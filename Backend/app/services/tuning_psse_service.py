import os
import csv

# Default constants
DEFAULT_EPSILON = 0.0000005
DEFAULT_MAX_ITER = 30
DEFAULT_K_LOW = -1.0
DEFAULT_K_HIGH = 1.5
DEFAULT_V_LOW = 0.9
DEFAULT_V_HIGH = 1.1


class PSSETuningService:
    def __init__(self, sav_path: str, log_path: str = None):
        self.sav_path = sav_path
        self.log_path = log_path
        self.logs = []
        self.psspy = None
        self._i = None
        self._f = None

    def _log(self, msg: str):
        self.logs.append(msg)

    def _init_psse(self):
        try:
            import psse35
            import psspy
            import redirect
            
            redirect.psse2py()
            psspy.psseinit(10000)
            
            if not os.path.isfile(self.sav_path):
                return {"success": False, "error": "Invalid or missing .sav file", "logs": self.logs}
            
            psspy.case(self.sav_path)
            self._log("Successfully loaded PSSE model")
            
            self.psspy = psspy
            self._i = psspy.getdefaultint()
            self._f = psspy.getdefaultreal()
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "logs": self.logs}

    def tune_p(self, bus_from: int, bus_to: int, gen_buses: list, gen_ids: list, 
               p_target: float, epsilon: float = DEFAULT_EPSILON, 
               max_iter: int = DEFAULT_MAX_ITER, k_low: float = DEFAULT_K_LOW, 
               k_high: float = DEFAULT_K_HIGH):
        """Tune P (active power) using bisection method"""
        
        psspy = self.psspy
        _i, _f = self._i, self._f
        
        # Get MBASE for each generator
        mbase_list = []
        for i, bus in enumerate(gen_buses):
            ierr, mbase = psspy.macdat(bus, gen_ids[i], 'MBASE')
            if ierr == 0:
                mbase_list.append(mbase)
            else:
                self._log(f"Cannot get MBASE for bus {bus}")
                return False
        self._log(f"MBASE: {mbase_list}")

        def set_pgen_by_ratio(k):
            for i, bus in enumerate(gen_buses):
                gen_id = gen_ids[i]
                p_gen_i = k * mbase_list[i]
                ierr = psspy.machine_chng_4(
                    bus, gen_id,
                    [_i, _i, _i, _i, _i, _i, _i],
                    [p_gen_i, _f, _f, _f, _f, _f, _f, _f, _f, _f, _f, _f, _f, _f, _f, _f, _f],
                    ""
                )
                if ierr != 0:
                    self._log(f"Cannot change PG at bus {bus}, id={gen_id}")

        def get_p_poi():
            psspy.fnsl([1,1,0,0,1,1,0,0])
            ierr, flow = psspy.brnflo(bus_from, bus_to, '1 ')
            if ierr != 0 or flow is None:
                return 0.0
            if isinstance(flow, complex):
                return flow.real
            if isinstance(flow, (list, tuple)) and len(flow) > 0:
                val = flow[0]
                return val.real if isinstance(val, complex) else val
            return 0.0

        log_rows = [("Iteration", "k_factor", "P_POI", "Error")]
        K_LOW, K_HIGH = k_low, k_high
        
        for i in range(1, max_iter + 1):
            k_mid = (K_LOW + K_HIGH) / 2
            set_pgen_by_ratio(k_mid)
            p_now = get_p_poi()
            err = p_now - p_target
            log_rows.append((i, k_mid, p_now, abs(err)))
            self._log(f"Iter {i:02d}: k={k_mid:.4f} | P={p_now:.4f} MW | err={err:+.4f}")

            if abs(err) < epsilon:
                self._log(f"Converged after {i} iterations: P={p_now:.3f} MW, k={k_mid:.4f}")
                break
            if err < 0:
                K_LOW = k_mid
            else:
                K_HIGH = k_mid
        else:
            self._log(f"Did not converge after {max_iter} iterations.")

        # Write log to CSV
        if self.log_path:
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(log_rows)
        
        return True

    def tune_q(self, bus_from: int, bus_to: int, gen_buses: list, reg_bus: list,
               q_target: float, epsilon: float = DEFAULT_EPSILON,
               max_iter: int = DEFAULT_MAX_ITER, v_low: float = DEFAULT_V_LOW,
               v_high: float = DEFAULT_V_HIGH):
        """Tune Q (reactive power) using bisection method"""
        
        psspy = self.psspy
        NODE = 0
        V_LOW, V_HIGH = v_low, v_high

        def set_vsched(vs):
            for i, bus in enumerate(gen_buses):
                ierr = psspy.plant_chng_4(bus, NODE, [reg_bus[i], 0], [vs, 100.0])

        def get_q_poi():
            psspy.fnsl([1,1,0,0,1,1,0,0])
            ierr, flow = psspy.brnflo(bus_from, bus_to, '1 ')
            if ierr != 0 or flow is None:
                return 0.0
            if isinstance(flow, complex):
                return flow.imag
            if isinstance(flow, (list, tuple)) and len(flow) > 0:
                val = flow[0]
                return val.imag if isinstance(val, complex) else val
            return 0.0

        log_rows = [("Iteration", "VSched", "Q_POI")]
        
        for i in range(1, max_iter + 1):
            v_mid = (V_LOW + V_HIGH) / 2
            set_vsched(v_mid)
            q_now = get_q_poi()
            err = q_now - q_target
            log_rows.append((i, v_mid, q_now))
            self._log(f"Iter {i:02d}: VSched={v_mid:.5f} | Q={q_now:.4f} | err={err:+.4f}")

            if abs(err) < epsilon:
                self._log(f"Converged after {i} iterations: Q={q_now:.3f} Mvar, VSched={v_mid:.4f}")
                break
            if q_now > q_target:
                V_HIGH = v_mid
            else:
                V_LOW = v_mid
        else:
            self._log(f"Did not converge after {max_iter} iterations.")

        # Append log to CSV
        if self.log_path:
            with open(self.log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(log_rows)
        
        return True

    def run_tuning(self, mode: str, bus_from: int, bus_to: int, gen_buses: list, 
                   gen_ids: list, reg_bus: list, p_target: float, q_target: float):
        """
        Run tuning based on mode: 'P', 'Q', or 'PQ'
        """
        # Initialize PSSE
        init_result = self._init_psse()
        if not init_result["success"]:
            return init_result

        try:
            if mode == "P":
                self.tune_p(bus_from, bus_to, gen_buses, gen_ids, p_target)
            elif mode == "Q":
                self.tune_q(bus_from, bus_to, gen_buses, reg_bus, q_target)
            elif mode == "PQ":
                self.tune_p(bus_from, bus_to, gen_buses, gen_ids, p_target)
                self.tune_q(bus_from, bus_to, gen_buses, reg_bus, q_target)
            else:
                return {"success": False, "error": f"Invalid mode: {mode}", "logs": self.logs}

            # Save the modified case
            self.psspy.save(self.sav_path)
            self._log(f"Saved file: {self.sav_path}")
            if self.log_path:
                self._log(f"Log CSV: {self.log_path}")
            self._log("Completed")

            return {
                "success": True,
                "message": f"Tuning {mode} completed successfully",
                "sav_path": self.sav_path,
                "log_path": self.log_path,
                "logs": self.logs
            }
        except Exception as e:
            return {"success": False, "error": str(e), "logs": self.logs}
