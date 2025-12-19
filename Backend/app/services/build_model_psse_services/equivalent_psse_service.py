import os
import sys
import psse35
import psspy
from psspy import _i, _f, _s
from app.classes.cls_data import CLSData

class EquivalentPSSEService:
    def __init__(self, file_path, output_path=None):
        # Initialize PSSE environment
        self.sys_path_PSSE = r'C:\Program Files\PTI\PSSE35\35.4\PSSPY39'
        self.os_path_PSSE = r'C:\Program Files\PTI\PSSE35\35.4\PSSBIN'
        
        if self.sys_path_PSSE not in sys.path:
            sys.path.append(self.sys_path_PSSE)
            
        os.environ['PATH'] += ";" + self.os_path_PSSE
        os.environ['PATH'] += ";" + self.sys_path_PSSE
        
        self.file_path = file_path
        self.output_path = output_path
        
        # Initialize PSSE
        ierr = psspy.psseinit(50)
        psspy.newcase_2(basemva=100, basefreq=60)
        psspy.newdiagfile()
        
        # Load Data using CLSData
        self.cls_data = CLSData(self.file_path)
        self.cls_data.load_all()
        self.data = self.cls_data.get_all_data()
        
    def _grow_diagram(self, sld, x, y):        
        psspy.growdiagram_2(1,1,[sld],x,y,[0,0,0,0,0,0,0,0,0,0,0,0,0])  
        return  
    
    def _create_low_side_bus(self, x, y, k, number_gen_ech_branch, branch, gen_number, gen_type_count):
        total_y = 0
        gen_number1 = gen_number
        
        # TR_SEC buses (Generator side)
        for type_gen in gen_type_count.keys():
             # Retrieve data safely
            gen_imp = self.data['5GEN_IMP'].get(str(type_gen), {})
            if not gen_imp: # Try iterating if keys are ints
                 gen_imp = self.data['5GEN_IMP'].get(int(type_gen), {})

            gen_data_sheet = self.data['1GEN'].get(str(type_gen), {})
            if not gen_data_sheet:
                 gen_data_sheet = self.data['1GEN'].get(int(type_gen), {})

            Rsource = gen_imp.get('Rsource', 0)
            Xsource = gen_imp.get('Xsource', 0.1)
            R0 = gen_imp.get('R0', 0)
            X0 = gen_imp.get('X0', 0.1)
            R1 = gen_imp.get('R1', 0)
            X1 = gen_imp.get('X1', 0.1)
            R2 = gen_imp.get('R2', 0)
            X2 = gen_imp.get('X2', 0.1)
            Rg = gen_imp.get('Rg', 0)
            Xg = gen_imp.get('Xg', 0)
            Xsub = gen_imp.get('Xsub', 0.1)
            Xsyn = gen_imp.get('Xsyn', 1.0)
            Xtrans = gen_imp.get('Xtrans', 0.2)
            
            MBASE = gen_data_sheet.get('MBASE', 100) * gen_type_count[type_gen]
            low_kv = gen_data_sheet.get('LOW_kV', 0.69)
            mv_kv = gen_data_sheet.get('MV_kV', 35)
            
            frombus = 10000 * gen_number1 + 1
            bus_name = f"GSU{gen_number1}_SEC"
            
            psspy.bus_data_4(frombus,0,[2,1,1,1],[low_kv,1.0,0.0,1.1,0.9,1.1,0.9],bus_name)
            psspy.plant_data_4(frombus,0,[999997,0],[1,100.0])
            psspy.machine_data_4(frombus,r"""1""",[1,1,0,0,0,1,0],[0.0,0.0,9999.0,-9999.0,9999.0,-9999.0,MBASE,Rsource,Xsource,0.0,0.0,1.0,1.0,1.0,1.0,1.0,1.0],"")
            psspy.seq_machine_data_4(frombus,r"""1""",_i,[R1,Xsub,R2,X2,R0,X0,Xtrans,Xsyn,Rg,Xg,_f])
            
            sld = f"BU {frombus}"
            self._grow_diagram(sld,x,y)         
            gen_number1 += 1
            y -= k
            total_y += y
            
        ## PRI (GSU High Side Bus)
        bus_name = f"GSU{branch}_PRI"
        tobus = 10000 + 1000 * int(branch)
        sld = f"BU {tobus}"
        psspy.bus_data_4(tobus,0,[1,1,1,1],[mv_kv,1.0,0.0,1.1,0.9,1.1,0.9],bus_name)
        
        y_new = total_y / (number_gen_ech_branch) if number_gen_ech_branch > 0 else 0
        
        gen_number2 = gen_number
        for type_gen in gen_type_count.keys():
            xfmr_data = self.data['2XFMR'].get(str(type_gen), {})
            if not xfmr_data:
                xfmr_data = self.data['2XFMR'].get(int(type_gen), {})

            R1 = xfmr_data.get('R1', 0)
            X1 = xfmr_data.get('X1', 0.05)
            R0 = xfmr_data.get('R0', 0)
            X0 = xfmr_data.get('X0', 0.05)
            NLL = xfmr_data.get('NLL', 0) * gen_type_count[type_gen]
            IEXT = xfmr_data.get('Iext', 0)
            Rmax = xfmr_data.get('Rmax', 1.1)
            Rmin = xfmr_data.get('Rmin', 0.9)
            Tap = xfmr_data.get('Tap', 1)
            Vector = xfmr_data.get('Vector', 'Dy11')
            MBASE = xfmr_data.get('MBASE', 100) * gen_type_count[type_gen]
            low_kv = xfmr_data.get('LOW_kV', 0.69)
            mv_kv = xfmr_data.get('MV_kV', 35)
            Code = xfmr_data.get('Code', 0)

            frombus = 10000 * gen_number2 + 1
            
            psspy.two_winding_data_6(tobus,frombus,r"""1""",[1,tobus,1,0,0,0,int(Tap),0,tobus,0,0,1,0,1,2,2],[R1,X1,MBASE,1.0,mv_kv,0,1.0,low_kv,1.0,1.0,1.0,1.0,NLL,IEXT,Rmax,Rmin,1.1,0.9,0.0,0.0,0.0],[MBASE,MBASE,MBASE,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"",Vector)
            psspy.two_winding_chng_6(tobus,frombus,r"""1""",[_i,_i,_i,_i,_i,_i,_i,_i,_i,_i,_i,_i,_i,_i,_i,1],[_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f],[_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f],_s,_s)
            psspy.seq_two_winding_data_3(tobus,frombus,r"""1""",[Code,2,2],[_f,_f,R0,X0,_f,_f,_f,_f,_f,_f])
            
            gen_number2 += 1
            
        self._grow_diagram(sld, x+2, y_new+k)

        return y, gen_number1

    def _create_high_side_bus(self, x, y, number_mpt):
        key = str(number_mpt)
        # Handle key if it's stored as int or str in dict, depending on sheet name parsing
        if key not in self.data['3XFMR']:
             # Fallback logic if key mismatch, though CLSData should handle it
             pass 

        xfmr3_data = self.data['3XFMR'].get(key, {})
        if not xfmr3_data:
             print(f"Warning: 3XFMR data not found for key {key}")
             return

        MBASE = xfmr3_data.get('MBASE', 100)
        pri_kv = xfmr3_data.get('Primary_volt', 220)
        sec_kv = xfmr3_data.get('Secondary_volt', 110)
        ter_kv = xfmr3_data.get('Tertiary_volt', 35)
        R01 = xfmr3_data.get('R01', 0)
        X01 = xfmr3_data.get('X01', 0.1)
        R02 = xfmr3_data.get('R02', 0)
        X02 = xfmr3_data.get('X02', 0.1)
        R03 = xfmr3_data.get('R03', 0)
        X03 = xfmr3_data.get('X03', 0.1)
        R12 = xfmr3_data.get('R12', 0)
        X12 = xfmr3_data.get('X12', 0.1)
        R23 = xfmr3_data.get('R23', 0)
        X23 = xfmr3_data.get('X23', 0.1)
        R31 = xfmr3_data.get('R31', 0)
        X31 = xfmr3_data.get('X31', 0.1)
        Vector = xfmr3_data.get('Vector', 'YNyn0d11')
        NLL = xfmr3_data.get('NLL', 0)
        Iext = xfmr3_data.get('Iext', 0)
        Rmax = xfmr3_data.get('Rmax', 1.1)
        Rmin = xfmr3_data.get('Rmin', 0.9)
        Rate = xfmr3_data.get('Rate', 100)
        Code = xfmr3_data.get('Code', 1)
        Tap = int(xfmr3_data.get('Tap', 1))
        
        secbus = 100000 + 10000 * number_mpt
        bus_name = f"MPT{number_mpt}_SEC"
        sld = f"BU {secbus}"
        psspy.bus_data_4(secbus,0,[1,1,1,1],[sec_kv,1.0,0.0,1.1,0.9,1.1,0.9],bus_name)  
        self._grow_diagram(sld,x,y)

        terbus = 100000 + 10000 * number_mpt + 3
        sld2 = f"BU {terbus}"
        bus_name = f"MPT{number_mpt}_TER"
        psspy.bus_data_4(terbus,0,[1,1,1,1],[ter_kv,1.0,0.0,1.1,0.9,1.1,0.9],bus_name)
        self._grow_diagram(sld2,x+1.5,y+1)      
        
        # MPT High Side (PRI) is typically 110002 for first one? 
        # Original code hardcodes 110002 in sld() then connects here.
        # Here we assume PRI is 110002.
        pri_bus_id = 110002 
        
        psspy.three_wnd_imped_data_4(pri_bus_id,secbus,terbus,r"""1""",[_i,_i,_i,_i,_i,2,2,_i,_i,_i,_i,_i,1],[R12,X12,R23,X23,R31,X31,MBASE,MBASE,MBASE,NLL,Iext,_f,_f,_f,_f,_f,_f],"",Vector)
        psspy.three_wnd_winding_data_5(pri_bus_id,secbus,terbus,r"""1""",1,[Tap,_i,secbus,_i,_i,-1],[_f,pri_kv,_f,Rmax,Rmin,1.02,0.98,_f,_f,_f],[Rate,Rate,Rate,_f,_f,_f,_f,_f,_f,_f,_f,_f])
        psspy.three_wnd_winding_data_5(pri_bus_id,secbus,terbus,r"""1""",2,[Tap,_i,_i,_i,_i,_i],[_f,sec_kv,_f,Rmax,Rmin,1.02,0.98,_f,_f,_f],[Rate,Rate,Rate,_f,_f,_f,_f,_f,_f,_f,_f,_f])
        psspy.three_wnd_winding_data_5(pri_bus_id,secbus,terbus,r"""1""",3,[Tap,_i,_i,_i,_i,_i],[_f,ter_kv,_f,Rmax,Rmin,1.02,0.98,_f,_f,_f],[Rate,Rate,Rate,_f,_f,_f,_f,_f,_f,_f,_f,_f])
        psspy.seq_three_winding_data_3(pri_bus_id,secbus,terbus,r"""1""",[2,2,Code],[_f,_f,R01,X01,_f,_f,R02,X02,_f,_f,R03,X03,_f,_f])
        psspy.three_wnd_imped_chng_4(pri_bus_id,secbus,terbus,r"""1""",[_i,_i,_i,_i,_i,_i,1,_i,_i,_i,_i,_i,_i],[_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f,_f],_s,_s)
        
        psspy.growdiagram_2(1,1,[sld],x,y,[0,0,0,0,0,0,0,0,0,0,0,0,0])
        
        return

    def run_build_model(self):
        """Orchestrates the model building similarly to PSSE.py 'sld' method."""
        x = 0
        y = 0 
        k = 2
        
        equi_data = self.data['4UG']['Equivalent']
        
        ## Create MV Side List
        mpt = {}
        mpt_branches = {}
        current = 0
        total = 0      
        count = 0     
        gen_number = 1

        for branch_name, eq_val in equi_data.items():
            gen_type_dict = eq_val.get('Gen_Type', {})
            num_gen_each_branch = len(set(gen_type_dict.values()))

            name_mpt = str(eq_val.get('Name_MPT', '')).strip()

            start = current + 1
            end = current + num_gen_each_branch
            arr = list(range(start, end + 1))
            mpt.setdefault(name_mpt, []).extend(arr)
            # Branch name is likely '1', '2' etc from sheet name "4 UG..._1"
            mpt_branches.setdefault(name_mpt, []).append(branch_name)
            
            total += sum(arr)
            count += len(arr)
            current = end
            
        high_kv = 110 # Default
        for key in self.data['1GEN']:
            high_kv = self.data['1GEN'][key]['HIGH_kV']
            break
            
        if count > 0:
             average = total / count - 1
        else:
             average = 0

        # Create MPT Primary Bus
        psspy.bus_data_4(110002,0,[1,1,1,1],[high_kv,1.0,0.0,1.1,0.9,1.1,0.9],r"""MPT1_PRI""")
        psspy.newseq()
        psspy.growdiagram_2(1,1,[r"""BU 110002"""],x+7,-k*average,[0,0,0,0,0,0,0,0,0,0,0,0,0])
        psspy.bus_data_4(999997,0,[1,1,1,1],[high_kv,1.0,0.0,1.1,0.9,1.1,0.9],r"""DUMMY_POI""")

        ## Create Low Side Buses (Generators & GSUs)
        y1 = y
        for branch_name, eq_val in equi_data.items():
            gen_type_dict = eq_val.get('Gen_Type', {})
            
            # Count generators per type
            gen_type_count = {}
            for g_type in gen_type_dict.values():
                if isinstance(g_type, str):
                    g_type_clean = g_type.replace("Type","")
                    try:
                         g_type_key = int(g_type_clean)
                    except:
                         g_type_key = g_type_clean
                else:
                    g_type_key = g_type
                    # If it's int, keep as is. If it matches key in data (which might be int or str), good.
                    
                gen_type_count[g_type_key] = gen_type_count.get(g_type_key, 0) + 1            
            
            num_gen_each_branch = len(gen_type_count) # Unique types in branch? 
            # Note: PSSE.py uses len(set(values)) which is count of unique types
            
            y1, gen_number = self._create_low_side_bus(x, y1, k, num_gen_each_branch, branch_name, gen_number, gen_type_count)


        # Create High Side Buses (MPTs)
        for mpt1, branchs in mpt.items():
            y2 = sum(branchs)
            n = len(branchs)
            try:
                mpt_idx = int(mpt1)
            except:
                mpt_idx = 1 # fallback
            
            # Position calc from PSSE.py: -y2/n*k+k
            self._create_high_side_bus(x+4, -y2/n*k+k, mpt_idx)

        ## Create Branch GSU - MPT
        for mpt1, branchs in mpt_branches.items():
            for branch in branchs:
                eq_branch = equi_data[branch]
                R0 = eq_branch['R0']
                X0 = eq_branch['X0']
                R1 = eq_branch['R1']
                X1 = eq_branch['X1']
                B1 = eq_branch['B1']
                B0 = eq_branch['B0']
                rate = eq_branch['Rate'] 
                # Note: PSSE.py reads Rate from eq_branch['Rate'] which comes from sum in data parsing

                frombus = 10000 + 1000 * int(branch)
                sld = f"BU {frombus}"
                try:
                     mpt_id = int(mpt1)
                except:
                     mpt_id = 1
                tobus = 100000 + 10000 * mpt_id
                
                psspy.branch_data_3(frombus,tobus,r"""1""",[1,frombus,1,0,0,0],[R1,X1,B1,0.0,0.0,0.0,0.0,0.0,1.0,1.0,1.0,1.0],[rate,rate*1.15,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"")
                psspy.seq_branch_data_3(frombus,tobus,r"""1""",_i,[R0,X0,B0,_f,_f,_f,_f,_f])
                self._grow_diagram(sld,1,1)
        
        ## Create POI and DUMMY SUB
        sld = r"""BU 960000"""
        psspy.bus_data_4(960000,0,[1,1,1,1],[high_kv,1.0,0.0,1.1,0.9,1.1,0.9],r"""DUMMY_SUB""")
        psspy.branch_data_3(110002,960000,r"""1""",[1,110002,1,0,0,0],[0.0,0.0001,0.0,0.0,0.0,0.0,0.0,0.0,1.0,1.0,1.0,1.0],[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"")
        self._grow_diagram(sld,x+9,-k*average)
        
        sld = r"""BU 999997"""
        ohline = self.data['OHLINE']
        R1 = ohline.get('R1', 0)
        X1 = ohline.get('X1', 0.0001)
        B1 = ohline.get('B1', 0)
        R0 = ohline.get('R0', 0)
        X0 = ohline.get('X0', 0.0001)
        B0 = ohline.get('B0', 0)
        length = ohline.get('LINE', 0)
        Rate = ohline.get('RATE', 0)
        
        psspy.branch_data_3(960000,999997,r"""1""",[1,960000,1,0,0,0],[R1,X1,B1,0.0,0.0,0.0,0.0,length,1.0,1.0,1.0,1.0],[Rate,Rate*1.15,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"")
        psspy.seq_branch_data_3(960000,999997,r"""1""",_i,[R0,X0,B0,_f,_f,_f,_f,_f])
        self._grow_diagram(sld,x+11,-k*average)
        
        sld = r"""BU 970000"""
        psspy.bus_data_4(970000,0,[3,1,1,1],[high_kv,1.0,0.0,1.1,0.9,1.1,0.9],r"""POI""")
        psspy.branch_data_3(999997,970000,r"""1""",[1,999997,1,0,0,0],[0.0,0.0001,0.0,0.0,0.0,0.0,0.0,0.0,1.0,1.0,1.0,1.0],[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"")
        psspy.plant_data_4(970000,0,[0,0],[1.0,100.0])
        psspy.machine_data_4(970000,r"""1""",[1,1,0,0,0,0,0],[0.0,0.0,9999.0,-9999.0,9999.0,-9999.0,10000.0,0.0,0.1,0.0,0.0,1.0,1.0,1.0,1.0,1.0,1.0],"")
        self._grow_diagram(sld,x+13,-k*average)
        
        psspy.seq_branch_data_3(110002,960000,r"""1""",_i,[_f,0.0001,_f,_f,_f,_f,_f,_f])
        psspy.seq_branch_data_3(970000,999997,r"""1""",_i,[_f,0.0001,_f,_f,_f,_f,_f,_f])
        psspy.seq_machine_data_4(970000,r"""1""",_i,[_f,0.01,_f,0.01,_f,0.01,0.01,0.01,_f,_f,_f])
        
        # Add Model Setup (Sheet 6)
        if '6Add_Model_Setup' in self.data:
            for key, name_device in self.data['6Add_Model_Setup'].items():
                for name_bus, _data in name_device.items():
                    if 'MPT' in name_bus:
                        # e.g., MPT 1 -> 110000
                        try:
                           bus_number = 100000 + 10000 * int(name_bus.split()[-1])
                        except: 
                           bus_number = 110000
                    elif 'GSU' in name_bus:
                        # e.g., GSU 1 -> 11000
                         try:
                           bus_number = 10000 + 1000 * int(name_bus.split()[-1])
                         except:
                           bus_number = 11000
                    else:
                        bus_number = 0
                    
                    id_cnt = 1
                    for value in _data:
                        if key == "Load Devices":
                            P = value[0]
                            Q = value[1]
                            psspy.load_data_6(bus_number,rf"""{id_cnt}""",[1,1,1,1,1,0,0],[P,Q,0.0,0.0,0.0,0.0,0.0,0.0],"")
                        elif key == "Reactive Devices":
                            Q = value
                            psspy.switched_shunt_data_5(bus_number,rf"""{id_cnt}""",[1,0,0,0,0,0,0,0,0,0,0,1,0,1,1,1,1,1,1,1,0],[Q,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.05,0.95,Q,100.0],"")
                        id_cnt += 1
                        
                    sld = f"BU {bus_number}"
                    self._grow_diagram(sld,0,0)

        # Save files
        output_folder = self.output_path if self.output_path else os.path.dirname(self.file_path)
        model_path = os.path.join(output_folder, "project.sld")
        psspy.savediagfile(model_path)
        psspy.save(model_path.replace(".sld",".sav"))
        
        return "Model built successfully"
