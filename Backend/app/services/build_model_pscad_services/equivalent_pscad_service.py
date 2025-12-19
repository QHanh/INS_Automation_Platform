from lxml import etree
import xml.etree.ElementTree as ET
from xml.dom import minidom
import openpyxl
import re
import sys
import math
import os
from app.classes.pscad_classes.component import PSCAD
from app.classes.cls_data import CLSData

class PSCADService:
    def __init__(self, file_path, output_path=None):
        self.file_path = file_path
        self.output_path = output_path if output_path else os.path.dirname(file_path)
        
        # Use new CLSData class
        self.cls_data = CLSData(self.file_path)
        self.cls_data.load_all()
        self.data = self.cls_data.get_all_data()
        
        self.pscad = PSCAD()
        self.schematic = etree.Element("wrap")
        self.v_lv = {}
        self.v_mv = {}

    def check_v(self):
        v_lv1 = {}
        v_hv1 = {}
        number1 = 1
        number2 = 1
        res_lv = {}
        res_hv = {}
        for key in self.data['1GEN']:
            # CLSData keys: LOW_kV, MV_kV
            v_lv = self.data['1GEN'][key]["LOW_kV"]
            if str(v_lv) not in v_lv1:
                key1 = str(v_lv)
                v_lv1[key1] = f'VLV{number1}'
                number1 += 1
            v_hv = self.data['1GEN'][key]["MV_kV"]
            if str(v_hv) not in v_hv1:
                key2 = str(v_hv)
                v_hv1[key2] = f'VMV{number2}'
                number2 += 1            
        if len(v_lv1) == 1:
            key = list(v_lv1.keys())[0]
            res_lv[key] = "VLV"
        else:
            res_lv = v_lv1
        if len(v_hv1) == 1:
            key = list(v_hv1.keys())[0]
            res_hv[key] = "VMV"
        else:
            res_hv = v_hv1
        return res_lv, res_hv

    def bus(self, x, y, k):
        # 1. Create LV/MV Buses for each Branch
        for i, key in enumerate(self.data['1GEN']):
            # key is branch name e.g. "1", "2"
            
            # LV Bus
            user = self.pscad.create_bus_wire(
                bus_id = 1000000000 + i,
                x = x+54,
                y = y + i * k,
                bus_name = f"BUS_LV{i+1}",
                BaseKV = self.data['1GEN'][key]['LOW_kV']
            )
            self.schematic.append(user)
            
            # MV Bus
            user = self.pscad.create_bus_wire(
                bus_id = 1100000000 + i,
                x = x + 200,
                y = y + i * k,
                bus_name = f"BUS_MV{i+1}",
                BaseKV = self.data['1GEN'][key]['MV_kV']
            )            
            self.schematic.append(user)  
        
        # 2. Build MPT Grouping (mimic PSSE logic)
        equi_data = self.data['4UG']['Equivalent']
        mpt_map = {} # Name_MPT -> list of branch keys
        
        # We need to preserve order, so we rely on processing order of 1GEN/4UG matches?
        # Or simpler: iterate through matched branches
        
        # CLSData uses sheet matching logic.
        # Let's group by Name_MPT found in matches
        
        # Note: 1GEN keys match 4UG keys match Equivalent keys (if they exist).
        # Let's iterate over 1GEN or 4UG Equivalent to build groups.
        
        for branch_key, eq_val in equi_data.items():
            name_mpt = str(eq_val.get('Name_MPT', '1')).strip()
            if name_mpt not in mpt_map:
                mpt_map[name_mpt] = []
            mpt_map[name_mpt].append(branch_key)
            
        # 3. Create MPT MV Buses (Common Bus for grouped branches)
        # Note: In PSCAD equivalent, do we draw one long bus per MPT?
        # Yes: h = 208 + (n_branch-1)*k
        
        current_y_offset = 0 # To stack MPTs visually?
        # The original code used 'tong' which accumulated branch counts.
        
        mpt_keys = sorted(list(mpt_map.keys())) # Ensure deterministic order?
        
        tong = 0
        for i, mpt_name in enumerate(mpt_keys):
            branch_list = mpt_map[mpt_name]
            n_branch = len(branch_list)
            first_branch = branch_list[0]
            
            # MV Bus for MPT
            user = self.pscad.create_bus_wire(
                bus_id = 1200000000 + i,
                x = x + 702,
                y = y + tong * k,
                h = 208 + (n_branch-1) * k,
                bus_name = f"BUS_MPT_MV{i+1}",
                # Use voltage of first branch in group
                BaseKV = self.data['1GEN'][first_branch]['MV_kV']
            )
            self.schematic.append(user)   
            tong += n_branch 

        # 4. Create MPT HV Buses
        # Logic from old code: IF n_mpt == 1 special placement?
        # Else: x + 1044
        
        n_mpt = len(mpt_keys)
        n_total_branches = len(self.data['1GEN'])
        
        for i, mpt_name in enumerate(mpt_keys):
            branch_list = mpt_map[mpt_name]
            first_branch = branch_list[0]
            
            if n_mpt == 1:
                # Centered if single MPT?
                user = self.pscad.create_bus_wire(
                    bus_id = 1300000000 + i,
                    x = x + 1044,
                    y = y + (n_total_branches) * k/2 - 90,
                    bus_name = f"BUS_MPT_HV",
                    BaseKV = self.data['1GEN'][first_branch]['HIGH_kV']
                )            
                self.schematic.append(user)
                break # Only 1
            else:
                # What is 'h' here? Old code had logic.
                # If multiple MPTs, they likely need their own HV buses or one common?
                # Old code: 'break' after loop meant it only drew ONE HV bus?
                # "break" was at line 118.
                # It seems it only supported 1 HV bus logic effectively or drew specific way.
                # Let's assume common HV bus for now or drawn per MPT?
                
                # Re-reading old code:
                # `if n_mpt == 1: ... break`
                # `else: ... break`
                # It effectively only drew the first MPT's HV bus and exited?
                # That implies all connect to one HV bus eventually?
                # Or maybe it supports multiple but the loop implementation was weird.
                # Use PSSE logic: MPTs connect to DUMMY_SUB (Common).
                # Here we draw BUS_MPT_HV.
                
                # Let's stick to the "break" behavior for safety unless Parallel MPTs are fully supported visually.
                # Assuming single Point of Interconnection logic for now.
                
                 user = self.pscad.create_bus_wire(
                    bus_id = 1300000000 + i,
                    x = x + 1044,
                    y = y + (n_total_branches) * k/2 - 90, # Center it roughly?
                    bus_name = f"BUS_MPT_HV",
                    BaseKV = self.data['1GEN'][first_branch]['HIGH_kV']
                )            
                 self.schematic.append(user)
                 break
        
        return 

    def group_resistor_ground(self,x,y,R):
        user = self.pscad.create_resistor(
            x = x, y = y,
            R = R
        )
        self.schematic.append(user)
        user = self.pscad.create_ground(
            x = x , y = y+36,
        )
        self.schematic.append(user)
        user = self.pscad.create_orthogonal_wire(
            x = x, y = y-36,
            h = 46,  # Vertical wire
            flag = True  # True for vertical
        )
        self.schematic.append(user)

    def group_multimeter_ground(self,x,y,P="",Q="",V="",I="",R="1e7",s_base = 1,v_base = 1,a_base = 1, Eabc = ""):
        user = self.pscad.create_multimeter(
            x = x, y = y,
            P = P, Q = Q, V = V, I = I,s_base = s_base, v_base = v_base, a_base = a_base, Eabc = Eabc
        )
        self.schematic.append(user)
        self.group_resistor_ground(x-54,y+36,R="1e7")
        user = self.pscad.create_orthogonal_wire(
            x = x-54, y = y,
            w = 46,  # Horizontal wire
            flag = False  # False for horizontal
        )
        self.schematic.append(user)
        user = self.pscad.create_orthogonal_wire(
            x = x+18, y = y,
            w = 46,  # Horizontal wire
            flag = False  # False for horizontal
        )
        self.schematic.append(user)

        user = self.pscad.create_orthogonal_wire(
            x = x-90, y = y,
            w = 46,
            flag = False
         )
        self.schematic.append(user)

    def group_load_multi(self,x,y,P,Q,V,VMV,i):
        P = P/3
        Q = Q/3
        V = V/math.sqrt(3)
        user = self.pscad.create_fixed_load(x, y, P=P, Q=Q, V=V)
        self.schematic.append(user)

        user = self.pscad.create_orthogonal_wire(x, y-18, w=82)
        self.schematic.append(user)

        user = self.pscad.create_multimeter(x+90, y-18, P = f'P_aux_{i}',Q = f'Q_aux_{i}',V = f'V_aux_{i}',v_base= VMV)
        self.schematic.append(user)

        user = self.pscad.create_orthogonal_wire(x+108, y-18)
        self.schematic.append(user)

    def pi_section_line(self,x,y,k):
        # 4UG Equivalent access for Pi Section
        
        for i, key in enumerate(self.data['1GEN']):
            # Access equivalent data for this branch key
            ug_equiv = self.data['4UG']['Equivalent'].get(key, {})
            
            R = round(float(ug_equiv.get('R1', 0)),6)
            X = round(float(ug_equiv.get('X1', 0)),6)
            B = round(float(ug_equiv.get('B1', 0)),6)
            R0 = round(float(ug_equiv.get('R0', 0)),6)
            X0 = round(float(ug_equiv.get('X0', 0)),6)
            B0 = round(float(ug_equiv.get('B0', 0)),6)

            V = round(self.data['1GEN'][key]['MV_kV'],6)
            V_MV = self.v_mv.get(str(V), "VMV")
            
            user = self.pscad.create_pi_section_line(comp_id=1110000000+i,Vbase= 'VMV', x=x, y=y+i*k,R=R, X=X, B=B, R0=R0, X0=X0, B0=B0)
            self.schematic.append(user)
            # self.group_multimeter_ground(x+162,y+i*k,P=f"P_MV_{i+1}",Q=f"Q_MV_{i+1}",V=f"V_MV_{i+1}",I=f"I_mv_{i+1}",R="1e7")
            self.group_multimeter_ground(x-90,y+i*k,P=f"P_MV_{i+1}",Q=f"Q_MV_{i+1}",V=f"V_MV_{i+1}",I=f"I_MV_{i+1}",R="1e7",v_base=f"{V_MV}")
            user = self.pscad.create_orthogonal_wire(
                x = x-288, y = y+i*k,
                w = 118,  # Horizontal wire
                flag = False  # False for horizontal
            )
            self.schematic.append(user)
            user = self.pscad.create_orthogonal_wire(
                x = x+72, y = y+i*k,
                w = 154,  # Horizontal wire
                flag = False  # False for horizontal
            )
            self.schematic.append(user)

    def group_3xfmr(self, id, x, y, Vector, V3, X12, X23, X31, R12, Sbase, NLL):

        user = self.pscad.create_transformer_3w(
            comp_id = id,
            x = x, y = y,
            Vector = Vector,
            V_W3 = V3,
            R12 = R12,
            X12 = X12,
            X23 = X23,
            X13 = X31,
            Sbase = Sbase,
            NLL = NLL
        )
        self.schematic.append(user)
        if Vector == ["0", "0", "1"] or Vector == ["0", "0", "0"]:
            self.group_resistor_ground(
                x = x, y = y+72, R="1e-7"
            )
            if Vector == ["0", "0", "1"]:
                user = self.pscad.create_orthogonal_wire(
                    x = x, y = y+36,
                    w = 28,  # Horizontal wire
                    flag = False  # False for horizontal
                )
                self.schematic.append(user)
            if Vector == ["0", "0", "0"]:
                user = self.pscad.create_orthogonal_wire(
                    x = x, y = y+36,
                    w = 28,  # Horizontal wire
                    flag = False  # False for horizontal
                )
                self.schematic.append(user)
                user = self.pscad.create_orthogonal_wire(
                    x = x-18, y = y+36,
                    w = 28,  # Horizontal wire
                    flag = False  # False for horizontal
                )
                self.schematic.append(user)
        self.group_resistor_ground(
            x = x-54, y = y+36, R="1e7"
        )

    def group_const_label(self, x, y, value, name):
        user = self.pscad.create_const(x, y+36, value)
        self.schematic.append(user)
        user = self.pscad.create_datalabel(x+54,y+36,name,orient="4")
        self.schematic.append(user)
        user = self.pscad.create_orthogonal_wire(x+36,y+36)
        self.schematic.append(user)

    def group_label_pgb(self, x, y, name, comp_id, unit):
        user = self.pscad.create_datalabel(x, y, name)
        self.schematic.append(user)

        user =  self.pscad.create_orthogonal_wire(x, y, w = 46)
        self.schematic.append(user)

        user = self.pscad.create_pgb_component(comp_id,x+36,y,unit=unit)
        self.schematic.append(user)

    def group_capbank_brk(self, x, y, V, Q, name):
        user = self.pscad.create_capacitive_load(V, x, y, Q)
        self.schematic.append(user)

        user = self.pscad.create_orthogonal_wire(x, y, w=46)
        self.schematic.append(user)

        user = self.pscad.create_breaker3(x+72,y,name = name)
        self.schematic.append(user)

        user = self.pscad.create_orthogonal_wire(x+108,y,w=46)
        self.schematic.append(user)

        user = self.pscad.create_datalabel(x-162,y,name = name)
        self.schematic.append(user)

        user = self.pscad.create_orthogonal_wire(x-162,y)
        self.schematic.append(user)

        user = self.pscad.create_tbreakn(x-108,y)
        self.schematic.append(user)

    def xfmr_3w(self, x, y, k):
        # Build MPT Map
        mpt_map = {}
        equi_data = self.data['4UG']['Equivalent']
        for branch_key, eq_val in equi_data.items():
            name_mpt = str(eq_val.get('Name_MPT', '1')).strip()
            if name_mpt not in mpt_map:
                mpt_map[name_mpt] = []
            mpt_map[name_mpt].append(branch_key)
            
        mpt_keys = sorted(list(mpt_map.keys()))
        
        tong = 0
        for i, mpt_name in enumerate(mpt_keys):
            branch_list = mpt_map[mpt_name]
            n_branch = len(branch_list)
            first_branch = branch_list[0]
            
            # Lookup 3-Winding Data
            # MPT Name is likely the key for 3XFMR dictionary (e.g., "1")
            
            xfmr_data = self.data['3XFMR'].get(mpt_name)
            if not xfmr_data:
                # Fallback or error?
                # Sometimes keys are ints? CLSData usually returns strings from _extract_sheet_index
                xfmr_data = self.data['3XFMR'].get(int(mpt_name), {})
            
            # Extract values
            Vector = xfmr_data.get('Vector', ["0", "0", "1"])
            # CLSData returns string for Vector in load_xfmr_3w_data? 
            # Wait, CLSData: 'Vector': str(sheet['D3'].value) which is e.g. "YNyn..."
            # Old code expected List ["0", "0", "1"]?
            # See old: `Vector = ...` then `if Vector == ...`
            # Wait, `pscad_data_classes.py` converted Vector string to list ["0", "0", "1"]!
            # `CLSData` returns raw string "YNyn0d11".
            # I must replicate the parsing logic here or update CLSData.
            # "YNyn0d11" -> How to map to ["0", "0", "1"]?
            # Old Code:
            # for c in Vector1.lower():
            #   if c == 'y': Vector.append("0")
            #   elif c == 'd': Vector.append("1")
            #
            # I need to implement this parsing here since I am consuming CLSData.
            
            raw_vector = xfmr_data.get('Vector', 'YNyn0d11')
            Vector = []
            for c in raw_vector.lower():
                 if c == 'y': Vector.append("0")
                 elif c == 'd': Vector.append("1")
            # Ensure it has 3 elements if needed? Old code seemed to expect that.
            
            V3 = xfmr_data.get('Tertiary_volt', 35)
            X12 = xfmr_data.get('X12', 0.1)
            X23 = xfmr_data.get('X23', 0.1)
            X31 = xfmr_data.get('X31', 0.1)
            R12 = xfmr_data.get('R12', 0)
            Sbase = xfmr_data.get('MBASE', 100)
            NLL = xfmr_data.get('NLL', 0) 
            
            VMV = self.data['1GEN'][first_branch]['MV_kV']

            self.group_3xfmr(id = 30000000+i,
                x=x, y=y+tong*k+k*(n_branch-1)/2,
                Vector=Vector,
                V3=V3,
                X12=X12,
                X23=X23,
                X31=X31,
                R12=R12,
                Sbase=Sbase,
                NLL=NLL
            )
            self.group_multimeter_ground(
                x=x+144, y=y+tong*k+k*(n_branch-1)/2,
                P=f"P_MPT_HV_{i+1}",
                Q=f"Q_MPT_HV_{i+1}",
                V=f"V_MPT_HV_{i+1}",
                I=f"I_MPT_HV_{i+1}",
                R="1e7",
                v_base="VHV",
                s_base="SMVA",

            )
            Vmv_val = self.v_mv.get(str(VMV), "VMV")
            self.group_multimeter_ground(
                x=x-54, y=y-108+tong*k+k*(n_branch-1)/2,
                P=f"P_MPT_MV_{i+1}",
                Q=f"Q_MPT_MV_{i+1}",
                V=f"V_MPT_MV_{i+1}",
                I=f"I_MPT_MV_{i+1}",
                R="1e7",
                v_base=f"{Vmv_val}",

            )

            user = self.pscad.create_orthogonal_wire(
                x=x, y=y-108+tong*k+k*(n_branch-1)/2,
                h=46, flag = True)
            
            self.schematic.append(user)

            user = self.pscad.create_oltc(x=x, y = y+162+tong*k+k*(n_branch-1)/2,name = f"InitTap_{i+1}")
            self.schematic.append(user)

            user = self.pscad.create_orthogonal_wire(x= x+54,y=y+162+tong*k+k*(n_branch-1)/2,w= 46)
            self.schematic.append(user)

            user = self.pscad.create_orthogonal_wire(x= x-90,y=y+162+tong*k+k*(n_branch-1)/2,w= 46)
            self.schematic.append(user)

            self.group_const_label(x=x, y = y+162+tong*k+k*(n_branch-1)/2,value = 0,name = f"InitTap_{i+1}")

            user = self.pscad.create_datalabel(x=x+90 , y=y+162+tong*k+k*(n_branch-1)/2, name = f"Tap_{i+1}")
            self.schematic.append(user)

            user = self.pscad.create_datalabel(x=x+54 , y=y-18+tong*k+k*(n_branch-1)/2, name = f"Tap_{i+1}")
            self.schematic.append(user)

            user = self.pscad.create_datalabel(x=x-90 , y=y+162+tong*k+k*(n_branch-1)/2, name = f"V_MPT_MV_{i+1}")
            self.schematic.append(user)   

            # Load and Cap Bank Logic
            # P_LOAD from 'User' sheet? 
            # CLSData loads 'User' sheet into '6Add_Model_Setup'? No.
            # CLSData has `load_add_model_setup` which puts it into `6Add_Model_Setup`.
            # Note: The old internal `User` method in pscad_data_classes.py read a "User" sheet (Sheet 0?)
            # or sheet starting with "0user".
            # CLSData does NOT have a "User" sheet loader. It has "6 Add Model Setup".
            # This is a generic "User" sheet vs standard "Add Model Setup".
            # If the user says "I am making a new cls" and refers to "Add Model Setup", I should use that.
            # BUT `equivalent_psse_service.py` uses `6Add_Model_Setup`.
            # So I should use `6Add_Model_Setup`.
            # Structure: `self.data['6Add_Model_Setup']['Load Devices'][bus_name]` -> List of `[P, Q]`.
            
            # Need to map MPT to "Load Devices" bus name?
            # PSSE logic checks: `if 'MPT' in name_bus: ... int(name_bus.split()[-1])`
            # So we look for "Bus MPT 1" or similar in the keys.
            
            # Implementation: Iterate `self.data['6Add_Model_Setup']['Load Devices']` and match index `i+1`.
            
            P_load = 0
            Q_load = 0
            
            add_model = self.data.get('6Add_Model_Setup', {})
            load_devices = add_model.get("Load Devices", {})
            
            target_mpt_suffix = str(i+1) # "1", "2"
            
            for bus_label, vals in load_devices.items():
                # Check if this bus_label corresponds to MPT i+1
                # e.g. "Bus MPT 1"
                 if "MPT" in str(bus_label) and str(target_mpt_suffix) in str(bus_label):
                     # Loop vals
                     for v in vals:
                         P_load += float(v[0])
                         Q_load += float(v[1])
            
            self.group_load_multi(x=x-270 , y=y-36+tong*k,P=P_load,Q=Q_load,V=VMV,VMV = Vmv_val,i=i+1)
            
            # Reactive Devices (Cap Bank)
            Q_bank = 0
            reactive_devices = add_model.get("Reactive Devices", {})
            for bus_label, vals in reactive_devices.items():
                if "MPT" in str(bus_label) and str(target_mpt_suffix) in str(bus_label):
                    for v in vals:
                        Q_bank += float(v)

            self.group_capbank_brk(x=x-288,y=y+tong*k,V=Vmv_val,Q = Q_bank,name = f'BRK_{i+1}')
            tong +=n_branch

    def OH_Line(self,x,y,k):
        n_branch =  len(self.data['1GEN'])
        R1 = self.data['OHLINE']['R1']
        X1 = self.data['OHLINE']['X1']
        B1 = self.data['OHLINE']['B1']
        R0 = self.data['OHLINE']['R0']
        X0 = self.data['OHLINE']['X0']
        B0 = self.data['OHLINE']['B0']

        user = self.pscad.create_pi_section_line(comp_id=1120000000,Vbase='VHV', x=x, y=y + (n_branch) * k/2-90,R=R1, X=X1, B=B1, R0=R0, X0=X0, B0=B0)
        self.schematic.append(user)
        self.group_multimeter_ground(x-90,y=y + (n_branch) * k/2-90,P=f"P_HV",Q=f"Q_HV",V=f"V_HV",R="1e7", v_base="VHV", s_base="SMVA")
        self.group_multimeter_ground(x+162,y=y + (n_branch) * k/2-90,P=f"P_POI",Q=f"Q_POI",V=f"V_POI",R="1e7", v_base="VHV", s_base="SMVA",Eabc = "Eabc")
        self.schematic.append(user)

    def group_2xfmr(self,x,y,i,R1,X1,sbase,NLL,Vector,V1,V2,NGSU):
        user = self.pscad.create_xfmr_2w_scaled(x=x,y=y,R=R1,X=X1,NLL = NLL/sbase/1e6/NGSU,V1=V1,V2=V2,sbase= sbase,
            user_id=20000000+i,
        )
        self.schematic.append(user)
        user = self.pscad.create_datalabel(
            x=x+18, y=y-36,
            name=f"Scale_{i+1}"
        )
        self.schematic.append(user)
        user = self.pscad.create_const(x=x+54, y=y-54,orient="1")
        self.schematic.append(user)

        user = self.pscad.create_orthogonal_wire(
            x=x+72, y=y,
            w=28,  # Horizontal wire
            flag = False  # False for horizontal
        )
        self.schematic.append(user)

        user = self.pscad.create_orthogonal_wire(
            x=x-54, y=y,
            w=28,
            flag= False
        )
        self.schematic.append(user)
        if len(Vector) >= 2:
            if Vector[0] == "1":
                self.group_resistor_ground(x=x+18,y=y+72,R = "1e7")
            if Vector[1] == '1':
                self.group_resistor_ground(x=x,y=y+72,R = "1e7")

    def xfmr_2w(self,x,y,k):
        for i, key in enumerate(self.data["2XFMR"]):
            xfmr_data = self.data["2XFMR"][key]
            R1 = xfmr_data.get('R1', 0)
            X1 = xfmr_data.get('X1', 0.05)
            sbase = xfmr_data.get('MBASE', 100)
            NLL = xfmr_data.get('NLL', 0)
            
            raw_vector = xfmr_data.get('Vector', 'Dy11')
            Vector = []
            for c in raw_vector.lower():
                 if c == 'y': Vector.append("0")
                 elif c == 'd': Vector.append("1")
            
            V1 = xfmr_data.get('MV_kV', 35)
            V2 = xfmr_data.get('LOW_kV', 0.69)
            
            # Calculate NGSU from 4UG Detail Gen_Type count for this branch
            detail_map = self.data['4UG']['Detail'].get(key, {})
            gen_type_dict = detail_map.get('Gen_Type', {})
            NGSU = len(gen_type_dict) 
            if NGSU == 0: NGSU = 1
            
            self.group_2xfmr(x,y+i*k,i,R1,X1,sbase,NLL,Vector,V1,V2,NGSU)

    def invs(self,x,y,k):
        for i, key in enumerate(self.data['1GEN']):
            vlv = self.data['1GEN'][key]['LOW_kV']
            v = self.v_lv.get(str(vlv), "VLV")
            self.group_multimeter_ground(x=x,y=y+k*i,P = f'P_inv_{i+1}',Q = f'Q_inv_{i+1}',V = f'V_inv_{i+1}',I = f'I_inv_{i+1}',R = '1e7', v_base=f'{v}' )

    def group_gain(self,x,y,name,gain_value,id,unit):
        user = self.pscad.create_datalabel(x,y,name )
        self.schematic.append(user)

        user = self.pscad.create_orthogonal_wire(x,y,w=46)
        self.schematic.append(user)

        user = self.pscad.create_gain(x+72,y,gain_value=gain_value)
        self.schematic.append(user)

        self.group_label_pgb(x+126,y,f"{name}_",comp_id=id,unit= unit )

        user = self.pscad.create_orthogonal_wire(x+108,y)
        self.schematic.append(user)

    def table_measurement(self,x,y):
        max_y =0
        for i,key in enumerate(self.data['1GEN']):
            self.group_label_pgb(x,y+54+i*108,f"P_inv_{i+1}",comp_id=91000000+i,unit="MW")
            self.group_label_pgb(x,y+90+i*108,f"Q_inv_{i+1}",comp_id=81000000+i,unit="MVar")
            self.group_label_pgb(x,y+126+i*108,f"V_inv_{i+1}",comp_id=71000000+i,unit="pu")
            max_y = 126+i*108
           
        self.group_gain(x+126,y+54,name = "P_HV",gain_value="SMVA",id = 92000000,unit="MW")
        self.group_gain(x+126,y+90,name = "Q_HV",gain_value="SMVA",id = 92000001,unit="MVar")
        self.group_label_pgb(x+252,y+126, "V_HV",comp_id = 92000002,unit="pu")
        self.group_gain(x+126,y+162,name = "P_POI",gain_value="SMVA",id = 92000003,unit="MW")
        self.group_gain(x+126,y+198,name = "Q_POI",gain_value="SMVA",id = 92000004,unit="MVar")
        self.group_label_pgb(x+252,y+234,"V_POI",comp_id = 92000005,unit="pu")

        self.group_label_pgb(x+252,y+270,"F_POI",comp_id = 92000006,unit="Hz")
        self.group_label_pgb(x+252,y+306,"Pcmd",comp_id = 92000007,unit="pu")
        self.group_label_pgb(x+252,y+342,"Qcmd",comp_id = 92000008,unit="pu")
        if max_y < 342 :
            max_y = 342

        number_wire = 4

        x1 = [0,396,396,0]
        y1 = [max_y+72,max_y+72,0,0]
        user = self.pscad.create_orthogonal_wire(x-36,y-36,x1 = x1,y1=y1,number_wire=number_wire)
        self.schematic.append(user)

        user = self.pscad.create_sticky(x-18,y-18,h = 36 , w = 360 )
        self.schematic.append(user)

    def table_parameter(self,x,y):
        y1 = 0
        for i,key in enumerate(self.v_lv):
            self.group_const_label(x,y+i*36,key,self.v_lv[key])
            y1 =  y+i*36+36

        y2 = 0 
        for i,key in enumerate(self.v_mv):
            self.group_const_label(x,y1+i*36,key,self.v_mv[key])
            y2 =  y1+i*36+36      
        
        for key in self.data['1GEN']:
            VHV = self.data['1GEN'][key]["HIGH_kV"]
            break
        self.group_const_label(x,y2,VHV,"VHV") 
        
        y2= y2+36
        y3 =0 
        
        # Scale parameters (NGSU)
        for i, key in enumerate(self.data['1GEN']):
             detail_map = self.data['4UG']['Detail'].get(key, {})
             gen_type_dict = detail_map.get('Gen_Type', {})
             NGSU = len(gen_type_dict) 
             if NGSU == 0: NGSU = 1
             
             self.group_const_label(x,y2+i*36,NGSU,f"Scale_{i+1}") 
             y3 = y2+i*36 - y
        
        SMVA = 0
        for i,key in enumerate(self.data['1GEN']):
             detail_map = self.data['4UG']['Detail'].get(key, {})
             gen_count = len(detail_map.get('Gen_Type', {}))
             mbase = self.data['1GEN'][key]['MBASE']
             SMVA += mbase * gen_count
             
        SMVA = round(SMVA,5)
        self.group_const_label(x+162,y,value = SMVA,name = "SMVA")
        self.group_const_label(x+162,y+36,value = 50,name = "nMVA")
        self.group_const_label(x+162,y+72,value = 10,name = "XdivR")
        self.group_const_label(x+162,y+108,value = 60,name = "Freq_ref")

        x1 = [0,306,306,0]
        y1 = [y3+108,y3+108,0,0]
        number_wire = 4
        user = self.pscad.create_orthogonal_wire(x-54,y-36,number_wire=number_wire,x1=x1,y1=y1)
        self.schematic.append(user)

        user = self.pscad.create_sticky(x-36,y-18,h = 36 , w = 270,text="Parameters" )
        self.schematic.append(user)

    def Eabc_Freq(self,x,y):
        user = self.pscad.create_datatap(x,y,index = 1,z = 480)
        self.schematic.append(user)        

        user = self.pscad.create_datatap(x,y+36,index = 2,z = 490)
        self.schematic.append(user)    

        user = self.pscad.create_datatap(x,y+72,index = 3,z = 520)
        self.schematic.append(user)   

        user = self.pscad.create_orthogonal_wire(x-18,y-54,flag=True,h =118)
        self.schematic.append(user) 

        for key in self.data['1GEN']:
            Vhv = self.data['1GEN'][key]['HIGH_kV']
            break
        user = self.pscad.create_pllblk(x+72,y+54,vrated=Vhv)
        self.schematic.append(user) 

        user = self.pscad.create_datalabel(x-18,y-54,name = 'Eabc')
        self.schematic.append(user) 

        user = self.pscad.create_datalabel(x+144,y+54,name = 'F_POI')
        self.schematic.append(user) 

    def grap(self,x,y):

        for i,key in enumerate(self.data['1GEN']):
            grap_id = []
            link_id = []
            grap_id.append(9999900000+i)
            grap_id.append(9999800000+i)
            grap_id.append(9999700000+i)
            link_id.append(91000000+i)
            link_id.append(81000000+i)
            link_id.append(71000000+i)
            user = self.pscad.create_graph_frame(x=x+i*450,y=y,frame_id=99900000+i,h=558,graph_id=grap_id,link_id=link_id)
            self.schematic.append(user)
            x1 = x+i*450


        grap_id = []
        link_id = []            
        grap_id.append(9899900000)
        grap_id.append(9899800000)
        grap_id.append(9899700000)
        link_id.append(92000003)
        link_id.append(92000004)
        link_id.append(92000005)  
        user = self.pscad.create_graph_frame(x=x1+450,y=y,frame_id=99800000,h=558,graph_id=grap_id,link_id=link_id)      
        self.schematic.append(user)

        grap_id = []
        link_id = []    
        grap_id.append(9799900000)
        grap_id.append(9799900000)
        link_id.append(92000007)
        link_id.append(92000008)
        user = self.pscad.create_graph_frame(x=x1+450*2,y=y,frame_id=99700000,h=558,graph_id=grap_id,link_id=link_id)      
        self.schematic.append(user)   

        grap_id = []
        link_id = []    
        grap_id.append(9699900000)
        link_id.append(92000006)
        user = self.pscad.create_graph_frame(x=x1+450*3,y=y,frame_id=99600000,graph_id=grap_id,link_id=link_id)      
        self.schematic.append(user)        

    def network(self):
        x=1800
        y=900
        k= 396
        self.v_lv,self.v_mv = self.check_v()
        # print(self.v_mv)

        self.invs(x,y+36,k)
        self.bus(x,y,k)
        self.xfmr_2w(x+108,y+36,k)
        self.pi_section_line(x+486,y+36,k)
        self.xfmr_3w(x+846,y+144,k)
        self.OH_Line(x+1224,y+36,k)
        self.table_measurement(x+2448,y)
        self.table_parameter(x+2988,y)
        self.Eabc_Freq(x+2088,y)
        self.grap(x+1908,y+846)

    def change_IBR(self):
        schematic = etree.Element("wrap")
        x= 738
        y= 306
        for key in self.data['1GEN']:
            VHV = self.data['1GEN'][key]['HIGH_kV']
            break
        SMVA = 0
        for i,key in enumerate(self.data['1GEN']):
             detail_map = self.data['4UG']['Detail'].get(key, {})
             gen_count = len(detail_map.get('Gen_Type', {}))
             mbase = self.data['1GEN'][key]['MBASE']
             SMVA += mbase * gen_count
             
        SMVA  = round(SMVA,5)
        user = self.pscad.create_const(x,y,value = VHV)
        schematic.append(user)

        user = self.pscad.create_orthogonal_wire(x+36,y,w= 46)
        schematic.append(user)

        user = self.pscad.create_datalabel(x+72,y,name = "VHV",orient="0")
        schematic.append(user)

        user = self.pscad.create_const(x+144,y,value = SMVA)
        schematic.append(user)

        user = self.pscad.create_orthogonal_wire(x+180,y,w= 46)
        schematic.append(user)


        user = self.pscad.create_datalabel(x+216,y,name = "SMVA",orient="0")
        schematic.append(user)

        return  schematic

    def insert_schematic_into_text(self, schematic_element, xml_text, defn_name="IBR_Name"):

        added_blocks = "\n".join([
            etree.tostring(e, encoding="unicode", pretty_print=True)
            for e in schematic_element
        ])

        pattern = fr'(<Definition[^>]+name="{defn_name}"[^>]*?>.*?<schematic[^>]*>)(.*?)(</schematic>)'
        match = re.search(pattern, xml_text, re.DOTALL)

 
        head, body, tail = match.groups()
        new_body = body + "\n" + added_blocks
        full_new_schematic = head + new_body + tail

        new_text = xml_text[:match.start()] + full_new_schematic + xml_text[match.end():]

        return new_text

    def build_equivalent_model(self):
        try:
            # Use template from templates directory
            # Go up 3 levels: build_model_pscad_services -> services -> app -> Backend
            template_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates", "form_final.pscx")
            template_path = os.path.abspath(template_path)
            
            if not os.path.exists(template_path):
                 return {"error": f"Template file not found: {template_path}"}

            with open(template_path, "r", encoding="utf-8") as f:
                xml_text = f.read()

            self.network()
            xml_text = self.insert_schematic_into_text(
                schematic_element=self.schematic,
                xml_text=xml_text,
                defn_name="IBR_Name"
            )

            schematic = self.change_IBR()
            xml_text = self.insert_schematic_into_text(
                schematic_element=schematic,
                xml_text=xml_text,
                defn_name="Main"
            )

            new_file = os.path.join(self.output_path, "main_network.pscx")
            with open(new_file, "w", encoding="utf-8") as f:
                f.write(xml_text)
            
            return {"message": "PSCAD model built successfully", "output_file": new_file}

        except Exception as e:
            return {"error": str(e)}

