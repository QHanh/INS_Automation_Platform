import os
import sys
import math
import time
import shutil
import traceback
from typing import List, Callable, Dict, Any, Optional
import xlsxwriter

try:
    from TOOLs.PSSPY39 import psse35
    from TOOLs.PSSPY39 import pssarrays
    from TOOLs.PSSPY39 import redirect
    from TOOLs.PSSPY39 import dyntools
    from TOOLs.PSSPY39 import bsntools
    from TOOLs.PSSPY39 import psspy
    from TOOLs.PSSPY39 import pssplot
    from psspy import _i, _f
except ImportError:
    print("⚠️ Could not import TOOLs.PSSPY39. PSSE functions will fail.")
    psspy = None
    _i, _f = 0, 0.0
    redirect = None

# --- CONSTANTS ---
NODE = 0
# --- HELPER FUNCTIONS ---

def export_diagram_image(psspy, sav_path, log_cb, image_type=3, quality=100):
    """Export diagram image with same name as .sav file but .png extension"""
    try:
        # Generate image path from sav path
        image_path = os.path.splitext(sav_path)[0] + ".png"
        
        # Set full view to capture entire diagram
        try:
            psspy.setfullviewscale()
        except:
            pass
        
        ierr = psspy.exportimagefile(image_type, image_path, quality)
        
        if os.path.exists(image_path):
            log_cb(f"📸 Exported image: {image_path}")
            return True
        else:
            log_cb(f"⚠️ Failed to export image: {image_path}")
            return False
    except Exception as e:
        log_cb(f"⚠️ Error exporting image: {e}")
        return False

def get_mpt_data(psspy, mpt, log_cb):
    """Lấy thông tin tap của một MPT"""
    mpt_type = mpt.get("mpt_type", "2-WINDING")
    bus_from = mpt.get("mpt_from")
    bus_to = mpt.get("mpt_to")
    bus_3 = mpt.get("mpt_bus_3", 0)
    ckt = "1 "
    
    if mpt_type == "2-WINDING":
        ierr, rmax = psspy.xfrdat(bus_from, bus_to, ckt, 'RMAX')
        ierr, rmin = psspy.xfrdat(bus_from, bus_to, ckt, 'RMIN')
        ierr, ntap = psspy.xfrint(bus_from, bus_to, ckt, 'NTPOSN')
    elif mpt_type == "3-WINDING":
        ierr, rmax = psspy.wnddat(bus_to, bus_from, bus_3, ckt, 'RMAX')
        ierr, rmin = psspy.wnddat(bus_to, bus_from, bus_3, ckt, 'RMIN')
        ierr, ntap = psspy.wndint(bus_to, bus_from, bus_3, ckt, 'NTPOSN')
    else:
        return None
    
    if ierr != 0:
        log_cb(f"❌ Error getting MPT data for {bus_from}-{bus_to}")
        return None
    
    return {
        "rmax": round(rmax, 2),
        "rmin": round(rmin, 2),
        "ntap": ntap,
        "ratio": 1.0,
        "step": round((rmax - rmin) / (ntap - 1), 5) if ntap > 1 else 0
    }

def set_mpt_ratio(psspy, mpt, ratio, _i, _f):
    """Đặt ratio cho một MPT"""
    mpt_type = mpt.get("mpt_type", "2-WINDING")
    bus_from = mpt.get("mpt_from")
    bus_to = mpt.get("mpt_to")
    bus_3 = mpt.get("mpt_bus_3", 0)
    ckt = "1"
    
    if mpt_type == "2-WINDING":
        intgar = [_i] * 16
        realari = [_f] * 21
        ratings = [_f] * 12
        realari[3] = ratio
        ierr, _ = psspy.two_winding_data_6(bus_from, bus_to, ckt, intgar, realari, ratings, "", "")
    elif mpt_type == "3-WINDING":
        intgar = [_i] * 6
        realari = [_f] * 10
        realari[0] = ratio
        ratings = [_f] * 12
        ierr, _ = psspy.three_wnd_winding_data_5(bus_from, bus_to, bus_3, ckt, 1, intgar, realari, ratings)
    
    return ierr

def disconnect_shunts(psspy, shunt_list, log_cb, _i, _f):
    """Disconnect specified Switched Shunts (Cap Banks)"""
    if not shunt_list:
        return
    
    log_cb("🔌 Disconnecting specified SHUNTS (Cap Banks)...")
    for item in shunt_list:
        bus = item["BUS"]
        sid = item["ID"]
        
        mode = 1 # Default
        try:
             ret = psspy.switched_shunt_data_5(bus, sid)
             if isinstance(ret, tuple) and len(ret) == 3:
                 ierr, iarray, rarray = ret
                 if ierr == 0:
                     mode = iarray[8]
        except:
             pass
        
        intgar = [_i] * 21
        intgar[11] = 0
        intgar[8] = mode
        
        realar = [_f] * 12
        
        ierr = psspy.switched_shunt_chng_5(bus, sid, intgar, realar, "")
        
        if ierr == 0:
            log_cb(f"   - Disconnected Shunt {sid} at Bus {bus} (Mode={mode})")
        elif ierr == -1:
             log_cb(f"   - Shunt {sid} at Bus {bus} already disconnected or no change.")
        else:
            log_cb(f"   ⚠️ Failed to disconnect Shunt {sid} at Bus {bus}. Error: {ierr}")

def check_bus_voltages(psspy, log_cb, limit, mode="lag"):
    ierr, [buses] = psspy.abusint(-1, 1, "NUMBER")
    ierr, [voltages] = psspy.abusreal(-1, 1, "PU")
    
    if ierr != 0 or buses is None:
        log_cb("⚠️ Error getting bus voltage data")
        return True, []
    
    violating = []
    for bus, v in zip(buses, voltages):
        if mode == "lag" and v > limit + 1e-6:
            violating.append((bus, round(v, 4)))
        elif mode == "lead" and v < limit - 1e-6:
            violating.append((bus, round(v, 4)))
    
    if violating:
        log_cb(f"⚠️ {len(violating)} bus(es) violating voltage limit ({limit} PU):")
        for bus, v in violating[:5]:  # Show first 5 only
            log_cb(f"   - Bus {bus}: {v} PU")
        if len(violating) > 5:
            log_cb(f"   ... and {len(violating) - 5} more")
    
    return len(violating) == 0, violating

def tune_vsched_for_target_q(psspy, log_cb, cfg, q_target, v_min=0.9, v_max=1.1):
    BUS_FROM, BUS_TO = cfg["BUS_FROM"], cfg["BUS_TO"]
    GEN_BUSES = cfg.get("GEN_BUSES", [])
    REG_BUS = cfg.get("REG_BUS", [])
    
    EPS = 1e-4
    MAX_ITER = 40
    
    def set_vsched(vs):
        for i, bus in enumerate(GEN_BUSES):
            rb = REG_BUS[i] if i < len(REG_BUS) else bus
            psspy.plant_chng_4(bus, NODE, [rb, 0], [vs, 100.0])

    def get_q_poi():
        psspy.fnsl([1,1,0,0,1,1,0,0])
        ierr, flow = psspy.brnflo(BUS_FROM, BUS_TO, '1')
        if ierr != 0 or flow is None:
            return 0.0
        if isinstance(flow, complex): return flow.imag
        if isinstance(flow, (list, tuple)) and len(flow) > 0:
            val = flow[0]
            return val.imag if isinstance(val, complex) else val
        return 0.0

    log_cb(f"🔄 Tuning Vsched to reach Q={q_target:.4f} Mvar...")
    
    current_high = v_max
    current_low = v_min
    
    best_v = (current_low + current_high) / 2
    best_err = 9999.0
    
    for i in range(1, MAX_ITER + 1):
        v_mid = (current_low + current_high) / 2
        set_vsched(v_mid)
        q_now = get_q_poi()
        err = q_now - q_target
        
        if abs(err) < abs(best_err):
            best_v = v_mid
            best_err = err

        if abs(err) < EPS:
            log_cb(f"✅ Tuned: Vsched={v_mid:.5f} -> Q={q_now:.3f} Mvar")
            return q_now, v_mid
        
        if q_now > q_target:
            current_high = v_mid
        else:
            current_low = v_mid
    
    set_vsched(best_v)
    final_q = get_q_poi()
    log_cb(f"⚠️ Tuning finished (limit iter) at: Vsched={best_v:.5f} (Q={final_q:.3f})")
    return final_q, best_v

# --- MEASURE & REPORT ---

def measure_points(psspy, report_points, cfg=None):
    """Do 5 diem P, Q, S, PF"""
    results = []
    
    points = report_points if isinstance(report_points, list) else []
    
    # helper to find gen id
    gen_buses = cfg.get("GEN_BUSES", []) if cfg else []
    gen_ids = cfg.get("GEN_IDS", []) if cfg else []

    for pt in points:
        if hasattr(pt, 'dict'): pt = pt.dict()
        
        f = pt.get("bus_from")
        t = pt.get("bus_to")
        c = "1"
        pt_name = pt.get("name", "")
        bess_id = pt.get("bess_id", "")

        p = 0.0
        q = 0.0

        if pt_name == "Unit at Gen Term":
            gid = "1"
            found_by_bus = False
            
            if f in gen_buses:
                try:
                    indices = [i for i, x in enumerate(gen_buses) if x == f]
                    if indices:
                        idx = indices[0]
                        if idx < len(gen_ids):
                            gid = gen_ids[idx]
                            found_by_bus = True
                except:
                    pass
            
            if not found_by_bus and bess_id.startswith("GEN "):
                try:
                    idx = int(bess_id.replace("GEN ", "")) - 1
                    if 0 <= idx < len(gen_ids):
                        gid = gen_ids[idx]
                except:
                    pass

            ierr_p, p_val = psspy.macdat(f, gid, 'P')
            ierr_q, q_val = psspy.macdat(f, gid, 'Q')
            
            if ierr_p == 0: p = p_val
            if ierr_q == 0: q = q_val
            
        else:
            # Standard branch flow
            ierr, flow = psspy.brnflo(f, t, c)
            if ierr == 0 and flow:
                if isinstance(flow, complex):
                    p, q = flow.real, flow.imag
                elif len(flow) > 0:
                    val = flow[0]
                    p, q = (val.real, val.imag) if isinstance(val, complex) else (val, 0)
        
        s = math.sqrt(p**2 + q**2)
        pf = p/s if s > 1e-6 else 0.0
        
        results.append({
            "bess_id": bess_id,
            "name": pt_name,
            "P": p, "Q": q, "S": s, "pf": pf
        })
    return results

def export_to_excel(cfg, data_map):
    path = cfg.get("EXCEL_PATH", "Report.xlsx")
    workbook = xlsxwriter.Workbook(path)
    
    # Formats
    header_fmt = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'bg_color': '#FFD700'}) 
    sub_header_fmt = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'bg_color': '#FCE4D6'}) 
    cell_fmt = workbook.add_format({'border': 1, 'align': 'center'})
    num_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.0000'})
    
    def write_sheet(sheet_name, cases):
        ws = workbook.add_worksheet(sheet_name)
        if not cases[0] in data_map: return 

        case1_data = data_map[cases[0]]
        case2_data = data_map[cases[1]]
        
        # Helper to group
        def group_data(dlist):
            groups = {}
            for item in dlist:
                 idx = item["bess_id"]
                 if idx not in groups: groups[idx] = []
                 groups[idx].append(item)
            return groups

        bess_groups_1 = group_data(case1_data)
        bess_groups_2 = group_data(case2_data)
        
        start_row = 1
        sorted_idxs = sorted(bess_groups_1.keys())
        
        for idx in sorted_idxs:
            # Block 1
            r, c = start_row, 1
            title1 = f"{cases[0]} {idx}"
            ws.merge_range(r, c, r, c+4, title1, header_fmt)
            r += 1
            
            items1 = bess_groups_1.get(idx, [])
            headers = [i["name"] for i in items1]
            for hi, h in enumerate(headers):
                ws.write(r, c+hi, h, sub_header_fmt)
            ws.write(r, c-1, "", cell_fmt)
            r+=1
            
            labels = ["S (MVA)", "P (MW)", "Q (Mvar)", "pf"]
            keys = ["S", "P", "Q", "pf"]
            for k_idx, key in enumerate(keys):
                ws.write(r + k_idx, c-1, labels[k_idx], sub_header_fmt)
                for col_idx, item in enumerate(items1):
                    ws.write(r + k_idx, c + col_idx, item[key], num_fmt)
            
            # Block 2
            c2 = 10
            title2 = f"{cases[1]} {idx}"
            ws.merge_range(start_row, c2, start_row, c2+4, title2, header_fmt)
            items2 = bess_groups_2.get(idx, [])
            headers2 = [i["name"] for i in items2]
            r2 = start_row + 1
            for hi, h in enumerate(headers2):
                ws.write(r2, c2+hi, h, sub_header_fmt)
            ws.write(r2, c2-1, "", cell_fmt)
            r2+=1
            for k_idx, key in enumerate(keys):
                ws.write(r2 + k_idx, c2-1, labels[k_idx], sub_header_fmt)
                for col_idx, item in enumerate(items2):
                    ws.write(r2 + k_idx, c2 + col_idx, item[key], num_fmt)

            start_row += 8

    write_sheet("Max Reactive", ["Max Lag", "Max Lead"])
    write_sheet("095PF Reactive", ["0.95 Lagging", "0.95 Leading"])
    workbook.close()

# --- CHECK LOGIC ---
def check_max_lag(psspy, log_cb, cfg, _i, _f):
    GEN_BUSES = cfg.get("GEN_BUSES", [])
    GEN_IDS = cfg.get("GEN_IDS", [])
    MPT_LIST = cfg.get("MPT_LIST", [])
    NODE = 0

    for i, bus in enumerate(GEN_BUSES):
        psspy.plant_chng_4(bus, NODE, [bus, 0], [1.1, 100.0])
    psspy.fnsl([1,1,0,0,1,1,0,0])
    
    q_gen_list, q_max_list = [], []
    for i, bus in enumerate(GEN_BUSES):
        gid = GEN_IDS[i] if i < len(GEN_IDS) else "1"
        _, q_gen = psspy.macdat(bus, gid, 'Q')
        _, q_max = psspy.macdat(bus, gid, 'QMAX')
        q_gen_list.append(q_gen)
        q_max_list.append(q_max)
    
    log_cb(f"✅ Q gen: {q_gen_list}")
    log_cb(f"✅ Q max: {q_max_list}")

    v_passed, violating = check_bus_voltages(psspy, log_cb, 1.1, "lag")
    
    if all(abs(qg - qmax) < 1e-6 for qg, qmax in zip(q_gen_list, q_max_list)) and v_passed:
        log_cb("✅ All QGEN equal QMAX and Voltages OK; no adjustment needed.")
        return
            
    mpt_data_list = []
    for idx, mpt in enumerate(MPT_LIST):
        data = get_mpt_data(psspy, mpt, log_cb)
        if data is None: return
        if data["ntap"] <= 1:
            log_cb(f"⚠️ MPT {idx+1}: Number of taps <= 1, cannot adjust.")
            return
        mpt_data_list.append(data)
        log_cb(f"⚙️ MPT {idx+1}: ratio=1, step={data['step']}, rmax={data['rmax']}")

    log_cb("🔄 Adjusting Taps to meet Q and Voltage requirements...")
    
    while True:
        all_at_max = True
        any_adjusted = False
        
        for idx, (mpt, data) in enumerate(zip(MPT_LIST, mpt_data_list)):
            if data["ratio"] < data["rmax"] - 1e-9:
                all_at_max = False
                any_adjusted = True
                data["ratio"] += data["step"]
                if data["ratio"] > data["rmax"]: data["ratio"] = data["rmax"]
                ierr = set_mpt_ratio(psspy, mpt, data["ratio"], _i, _f)
                if ierr != 0:
                    log_cb(f"❌ Error changing ratio for MPT {idx+1}: {ierr}")
                    return
        
        if not any_adjusted and all_at_max:
            log_cb(f"⚠️ All MPT reached RMAX. Conditions might not be met.")
            break
        
        ierr = psspy.fnsl([1,1,0,0,1,1,0,0])
        if ierr != 0:
            log_cb("⚠️ fnsl error when increasing ratio, stopping.")
            break

        q_gen_list = []
        for i, bus in enumerate(GEN_BUSES):
            gid = GEN_IDS[i] if i < len(GEN_IDS) else "1"
            _, q_gen = psspy.macdat(bus, gid, 'Q')
            _, q_max = psspy.macdat(bus, gid, 'QMAX')
            q_gen_list.append(q_gen)
            q_max_list[i] = q_max
            
        ratio_str = ", ".join([f"MPT{i+1}={d['ratio']:.5f}" for i, d in enumerate(mpt_data_list)])
        v_passed, _ = check_bus_voltages(psspy, log_cb, 1.1, "lag")
        
        if all(abs(qg - qmax) < 1e-6 or qg > qmax for qg, qmax in zip(q_gen_list, q_max_list)) and v_passed:
            log_cb(f"✅ Requirements PASSED at {ratio_str}")
            break

    log_cb("✅ Finished max lag check.")

def check_max_lead(psspy, log_cb, cfg, _i, _f):
    GEN_BUSES = cfg.get("GEN_BUSES", [])
    GEN_IDS = cfg.get("GEN_IDS", [])
    MPT_LIST = cfg["MPT_LIST"]
    SHUNT_LIST = cfg.get("SHUNT_LIST", [])
    NODE = 0

    disconnect_shunts(psspy, SHUNT_LIST, log_cb, _i, _f)

    for i, bus in enumerate(GEN_BUSES):
        psspy.plant_chng_4(bus, NODE, [bus, 0], [0.9, 100.0])
    psspy.fnsl([1,1,0,0,1,1,0,0])
    
    q_gen_list, q_min_list = [], []
    for i, bus in enumerate(GEN_BUSES):
        gid = GEN_IDS[i] if i < len(GEN_IDS) else "1"
        _, q_gen = psspy.macdat(bus, gid, 'Q')
        _, q_min = psspy.macdat(bus, gid, 'QMIN')
        q_gen_list.append(q_gen)
        q_min_list.append(q_min)
        
    log_cb(f"✅ Q gen: {q_gen_list}")
    log_cb(f"✅ Q min: {q_min_list}")

    v_passed, violating = check_bus_voltages(psspy, log_cb, 0.9, "lead")

    if all(abs(qg - qmin) < 1e-6 for qg, qmin in zip(q_gen_list, q_min_list)) and v_passed:
        log_cb("✅ All QGEN equal QMIN and Voltages OK; no adjustment needed.")
        return

    mpt_data_list = []
    for idx, mpt in enumerate(MPT_LIST):
        data = get_mpt_data(psspy, mpt, log_cb)
        if data is None: return
        if data["ntap"] <= 1:
            log_cb(f"⚠️ MPT {idx+1}: Number of taps <= 1, cannot adjust.")
            return
        mpt_data_list.append(data)
        log_cb(f"⚙️ MPT {idx+1}: ratio=1, step={data['step']}, rmin={data['rmin']}")

    log_cb("🔄 Adjusting Taps to meet Q and Voltage requirements...")

    while True:
        all_at_min = True
        any_adjusted = False
        
        for idx, (mpt, data) in enumerate(zip(MPT_LIST, mpt_data_list)):
            if data["ratio"] > data["rmin"] + 1e-9:
                all_at_min = False
                any_adjusted = True
                data["ratio"] -= data["step"]
                if data["ratio"] < data["rmin"]: data["ratio"] = data["rmin"]
                ierr = set_mpt_ratio(psspy, mpt, data["ratio"], _i, _f)
                if ierr != 0:
                    log_cb(f"❌ Error changing ratio for MPT {idx+1}: {ierr}")
                    return
        
        if not any_adjusted and all_at_min:
            log_cb(f"⚠️ All MPT reached RMIN. Conditions might not be met.")
            break
        
        ierr = psspy.fnsl([1,1,0,0,1,1,0,0])
        if ierr != 0:
            log_cb("⚠️ fnsl error when decreasing ratio, stopping.")
            break

        q_gen_list = []
        for i, bus in enumerate(GEN_BUSES):
            gid = GEN_IDS[i] if i < len(GEN_IDS) else "1"
            _, q_gen = psspy.macdat(bus, gid, 'Q')
            _, q_min = psspy.macdat(bus, gid, 'QMIN')
            q_gen_list.append(q_gen)
            q_min_list.append(q_min) # Refresher

        ratio_str = ", ".join([f"MPT{i+1}={d['ratio']:.5f}" for i, d in enumerate(mpt_data_list)])
        v_passed, _ = check_bus_voltages(psspy, log_cb, 0.9, "lead")
        
        if all(abs(qg - qmin) < 1e-6 or qg < qmin for qg, qmin in zip(q_gen_list, q_min_list)) and v_passed:
            log_cb(f"✅ Requirements PASSED at {ratio_str}")
            break

    log_cb("✅ Finished max lead check.")

def check_095_lagging(psspy, log_cb, cfg, _i, _f):
    GEN_BUSES = cfg.get("GEN_BUSES", [])
    MPT_LIST = cfg["MPT_LIST"]
    BUS_FROM, BUS_TO = cfg["BUS_FROM"], cfg["BUS_TO"]
    P_NET = cfg.get("P_NET", 0.0)
    
    def get_q():
        ierr, flow = psspy.brnflo(BUS_FROM, BUS_TO, '1')
        if ierr != 0 or flow is None: return 0.0
        if isinstance(flow, complex): return flow.imag
        if isinstance(flow, (list, tuple)) and len(flow) > 0:
            val = flow[0]
            return val.imag if isinstance(val, complex) else val
        return 0.0
    
    p_net = round(P_NET, 1)
    q_095_lagging = p_net * math.tan(math.acos(0.95))
    log_cb(f"P_net={p_net} MW, Q_095_lagging={q_095_lagging:.2f} Mvar")
    
    q_now, vsched_final = tune_vsched_for_target_q(psspy, log_cb, cfg, q_095_lagging, v_min=0.9, v_max=1.1)

    v_passed, violating = check_bus_voltages(psspy, log_cb, 1.1, "lag")
    
    if q_now >= q_095_lagging and v_passed:
        log_cb(f"✅ Achieved immediately: Q={q_now:.2f} >= {q_095_lagging:.2f} and Voltages OK.")
        return
    
    mpt_data_list = []
    for idx, mpt in enumerate(MPT_LIST):
        data = get_mpt_data(psspy, mpt, log_cb)
        if data is None: return
        if data["ntap"] <= 1:
            log_cb(f"⚠️ MPT {idx+1}: Number of taps <= 1, cannot adjust.")
            return
        mpt_data_list.append(data)
        log_cb(f"⚙️ MPT {idx+1}: ratio=1, step={data['step']}, rmax={data['rmax']}")

    log_cb("🔄 Adjusting Taps to meet Q and Voltage requirements...")
    
    while True:
        all_at_max = True
        any_adjusted = False
        
        for idx, (mpt, data) in enumerate(zip(MPT_LIST, mpt_data_list)):
            if data["ratio"] < data["rmax"] - 1e-9:
                all_at_max = False
                any_adjusted = True
                data["ratio"] += data["step"]
                if data["ratio"] > data["rmax"]: data["ratio"] = data["rmax"]
                ierr = set_mpt_ratio(psspy, mpt, data["ratio"], _i, _f)
                if ierr != 0:
                    log_cb(f"❌ Error changing ratio for MPT {idx+1}: {ierr}")
                    return

        if not any_adjusted and all_at_max:
             log_cb(f"⚠️ All MPT reached RMAX. Conditions might not be met.")
             break
        
        ierr = psspy.fnsl([1,1,0,0,1,1,0,0])
        if ierr != 0:
            log_cb("⚠️ fnsl error when increasing ratio, stopping.")
            break
            
        q_now = get_q()
        v_passed, _ = check_bus_voltages(psspy, log_cb, 1.1, "lag")
        
        if q_now >= q_095_lagging and v_passed:
            log_cb(f"✅ Requirements PASSED.")
            break

    log_cb("✅ Finished 0.95 lagging check.")

def check_095_leading(psspy, log_cb, cfg, _i, _f):
    GEN_BUSES = cfg.get("GEN_BUSES", [])
    MPT_LIST = cfg["MPT_LIST"]
    BUS_FROM, BUS_TO = cfg["BUS_FROM"], cfg["BUS_TO"]
    P_NET = cfg.get("P_NET", 0.0)
    SHUNT_LIST = cfg.get("SHUNT_LIST", [])

    def get_q():
        ierr, flow = psspy.brnflo(BUS_FROM, BUS_TO, '1')
        if ierr != 0 or flow is None: return 0.0
        if isinstance(flow, complex): return flow.imag
        if isinstance(flow, (list, tuple)) and len(flow) > 0:
            val = flow[0]
            return val.imag if isinstance(val, complex) else val
        return 0.0

    p_net = round(P_NET, 1)
    q_095_leading = - p_net * math.tan(math.acos(0.95))
    log_cb(f"P_net={p_net} MW, Q_095_leading={q_095_leading:.2f} Mvar")
    
    disconnect_shunts(psspy, SHUNT_LIST, log_cb, _i, _f)
    q_now, vsched_final = tune_vsched_for_target_q(psspy, log_cb, cfg, q_095_leading, v_min=0.9, v_max=1.1)

    v_passed, violating = check_bus_voltages(psspy, log_cb, 0.9, "lead")
    
    if abs(q_now - q_095_leading) < 1e-2 and v_passed:
        log_cb(f"✅ Achieved immediately: Q={q_now:.2f} <= {q_095_leading:.2f} and Voltages OK.")
        return
        
    mpt_data_list = []
    for idx, mpt in enumerate(MPT_LIST):
        data = get_mpt_data(psspy, mpt, log_cb)
        if data is None: return
        if data["ntap"] <= 1:
            log_cb(f"⚠️ MPT {idx+1}: Number of taps <= 1, cannot adjust.")
            return
        mpt_data_list.append(data)
        log_cb(f"⚙️ MPT {idx+1}: ratio=1, step={data['step']}, rmin={data['rmin']}")

    log_cb("🔄 Adjusting Taps to meet Q and Voltage requirements...")
    
    while True:
        all_at_min = True
        any_adjusted = False
        
        for idx, (mpt, data) in enumerate(zip(MPT_LIST, mpt_data_list)):
            if data["ratio"] > data["rmin"] + 1e-9:
                all_at_min = False
                any_adjusted = True
                data["ratio"] -= data["step"]
                if data["ratio"] < data["rmin"]: data["ratio"] = data["rmin"]
                ierr = set_mpt_ratio(psspy, mpt, data["ratio"], _i, _f)
                if ierr != 0:
                    log_cb(f"❌ Error changing ratio for MPT {idx+1}: {ierr}")
                    return

        if not any_adjusted and all_at_min:
            log_cb(f"⚠️ All MPT reached RMIN. Conditions might not be met.")
            break

        ierr = psspy.fnsl([1,1,0,0,1,1,0,0])
        if ierr != 0:
            log_cb("⚠️ fnsl error when decreasing ratio, stopping.")
            break

        q_now = get_q()
        v_passed, _ = check_bus_voltages(psspy, log_cb, 0.9, "lead")
        
        if q_now <= q_095_leading and v_passed:
            log_cb(f"✅ Requirements PASSED.")
            break

    log_cb("✅ Finished 0.95 leading check.")

def run_all_cases(psspy, log_cb, cfg, _i, _f):
    sav_path = cfg["SAV_PATH"]
    base_name = os.path.splitext(sav_path)[0]
    
    log_cb("=== RUNNING MAX LAG ===")
    psspy.case(sav_path)
    check_max_lag(psspy, log_cb, cfg, _i, _f)
    res_max_lag = measure_points(psspy, cfg.get("REPORT_POINTS", []), cfg)
    path_max_lag = f"{base_name}_MaxLag.sav"
    psspy.save(path_max_lag)
    log_cb(f"💾 Saved Max Lag case: {path_max_lag}")
    export_diagram_image(psspy, path_max_lag, log_cb)
    
    log_cb("=== RUNNING 0.95 LAGGING ===")
    psspy.case(sav_path)
    check_095_lagging(psspy, log_cb, cfg, _i, _f)
    res_095_lag = measure_points(psspy, cfg.get("REPORT_POINTS", []), cfg)
    path_095_lag = f"{base_name}_095Lag.sav"
    psspy.save(path_095_lag)
    log_cb(f"💾 Saved 0.95 Lag case: {path_095_lag}")
    export_diagram_image(psspy, path_095_lag, log_cb)

    log_cb("=== RUNNING MAX LEAD ===")
    psspy.case(sav_path)
    check_max_lead(psspy, log_cb, cfg, _i, _f)
    res_max_lead = measure_points(psspy, cfg.get("REPORT_POINTS", []), cfg)
    path_max_lead = f"{base_name}_MaxLead.sav"
    psspy.save(path_max_lead)
    log_cb(f"💾 Saved Max Lead case: {path_max_lead}")
    export_diagram_image(psspy, path_max_lead, log_cb)

    log_cb("=== RUNNING 0.95 LEADING ===")
    psspy.case(sav_path)
    check_095_leading(psspy, log_cb, cfg, _i, _f)
    res_095_lead = measure_points(psspy, cfg.get("REPORT_POINTS", []), cfg)
    path_095_lead = f"{base_name}_095Lead.sav"
    psspy.save(path_095_lead)
    log_cb(f"💾 Saved 0.95 Lead case: {path_095_lead}")
    export_diagram_image(psspy, path_095_lead, log_cb)

    log_cb("📊 Exporting Excel Report...")
    data_map = {
        "Max Lag": res_max_lag,
        "Max Lead": res_max_lead,
        "0.95 Lagging": res_095_lag,
        "0.95 Leading": res_095_lead
    }
    path = os.path.dirname(sav_path)
    excel_path = os.path.join(path, "Reactive_Report.xlsx")
    cfg["EXCEL_PATH"] = excel_path
    export_to_excel(cfg, data_map)
    log_cb(f"✅ Report saved to: {excel_path}")
    log_cb("🏁 ALL TASKS COMPLETED")

def run_check_logic(cfg: Dict, mode: str, log_cb: Callable[[str], None]):
    try:
        if mode == "SAVE_AS":
            src = cfg["SAV_PATH"]
            dst = cfg["SAVE_AS_PATH"]
            shutil.copy(src, dst)
            log_cb(f"💾 Saved successfully to: {dst}")
            return
        
        if redirect: redirect.psse2py()
        if psspy: psspy.psseinit(10000)
        
        if not os.path.isfile(cfg["SAV_PATH"]):
            log_cb("⚠️ Invalid or missing .sav file!")
            return
        
        if psspy: psspy.case(cfg["SAV_PATH"])
        log_cb("✅ PSSE model loaded successfully")
        
        if mode == "RUN_ALL":
            run_all_cases(psspy, log_cb, cfg, _i, _f)
        elif mode == "Max Lag":
            check_max_lag(psspy, log_cb, cfg, _i, _f)
            psspy.save(cfg["SAV_PATH"])
        elif mode == "Max Lead":
            check_max_lead(psspy, log_cb, cfg, _i, _f)
            psspy.save(cfg["SAV_PATH"])
        elif mode == "0.95 Lagging":
            check_095_lagging(psspy, log_cb, cfg, _i, _f)
            psspy.save(cfg["SAV_PATH"])
        elif mode == "0.95 Leading":
            check_095_leading(psspy, log_cb, cfg, _i, _f)
            psspy.save(cfg["SAV_PATH"])
        else:
            log_cb(f"⚠️ Invalid mode: {mode}")
            
    except Exception as e:
        log_cb(f"❌ Error: {e}")
        log_cb(traceback.format_exc())


# ...
