import os 
import sys
import openpyxl

class Get_CLS:
    def __init__(self, path):
        self.path = path
        self.bus_number = 101
        self.JB = 2001
        self.data = {'1GEN': {},'2XFMR':{},'3XFMR':{},'OHLINE':{},'4UG':{},'5GEN_IMP':{},'Subtation':{},'User':{}}
    
    def get_gen(self,sheet):
        sheets = self.wb[sheet]
        name_sheet = sheet[-1] 
        Mbase = float(sheets['B7'].value)
        kV = float(sheets['B10'].value)
        Pgen = float(sheets['C7'].value)
        Pmax = float(sheets['C8'].value)    
        Pmin = float(sheets['C9'].value)
        Qmax = float(sheets['C10'].value)
        Qmin = float(sheets['C11'].value)
        collect_kV = float(sheets['B11'].value)
        interconnec_kV = float(sheets['B12'].value)
        form = {'MBASE':Mbase, 'kV':kV, 'collect_kV':collect_kV, 'interconnec_kV':interconnec_kV, 'Pmin':Pmin, 'Pmax':Pmax, 'Qmax':Qmax, 'Qmin':Qmin, 'Pgen':Pgen}
        self.data['1GEN'][name_sheet] = form

    def get_2xfmr(self,sheet):
        sheets = self.wb[sheet]
        name_sheet = sheet[-1] 
        R1 = round(float(sheets['B12'].value), 6)
        X1 = round(float(sheets['B13'].value), 6)
        R0 = round(float(sheets['B34'].value), 6)
        X0 = round(float(sheets['B35'].value), 6)    
        Vector = str(sheets['B3'].value)
        MBASE = float(sheets['B14'].value)
        Primary_volt = float(sheets['B5'].value)
        Secondary_volt = float(sheets['C5'].value)
        form = {'R1':R1 ,'X1':X1,'R0':R0, 'X0':X0, 'Vector':Vector, 'MBASE':MBASE, 'Primary_volt':Primary_volt, 'Secondary_volt':Secondary_volt}
        self.data['2XFMR'][name_sheet] = form

    def get_3xfmr(self,sheet):
        sheets = self.wb[sheet]
        name_sheet = sheet[-1]
        R12 = round(float(sheets['D12'].value), 6)
        X12 = round(float(sheets['D13'].value), 6)
        R23 = round(float(sheets['H12'].value), 6)
        X23 = round(float(sheets['H13'].value), 6)
        R31 = round(float(sheets['F12'].value), 6)
        X31 = round(float(sheets['F13'].value), 6)
        MBASE = float(sheets['D14'].value)
        R01 = round(float(sheets['D34'].value), 6)
        X01 = round(float(sheets['D35'].value), 6)
        R02 = round(float(sheets['H34'].value), 6)
        X02 = round(float(sheets['H35'].value), 6)
        R03 = round(float(sheets['F34'].value), 6)
        X03 = round(float(sheets['F35'].value), 6)
        Vector = str(sheets['D3'].value)
        Primary_volt = float(sheets['D5'].value)
        Secondary_volt = float(sheets['H5'].value)
        Tertiary_volt = float(sheets['I5'].value)
        form = {'R12':R12, 'X12':X12, 'R23':R23, 'X23':X23, 'R31':R31, 'X31':X31, 'MBASE':MBASE, 'Vector':Vector, 'R01':R01, 'X01':X01, 'R02':R02, 'X02':X02, 'R03':R03, 'X03':X03, 'Primary_volt':Primary_volt, 'Secondary_volt':Secondary_volt, 'Tertiary_volt':Tertiary_volt}
        self.data['3XFMR'][name_sheet] = form

    def get_ohline(self,sheet):
        sheets = self.wb[sheet]
        LINE = round(float(sheets['G2'].value), 6)   
        kV = float(sheets['E2'].value)   
        RATE = round(float(sheets['I2'].value), 6)
        R1 = round(float(sheets['AD2'].value), 6)
        X1 = round(float(sheets['AE2'].value), 6)
        R0 = round(float(sheets['AF2'].value), 6)
        X0 = round(float(sheets['AG2'].value), 6)
        B1 = round(float(sheets['AJ2'].value), 6)
        B0 = round(float(sheets['AK2'].value), 6)
        form = {'LINE':LINE ,'kV':kV,'RATE':RATE,'R1':R1,'X1':X1,'R0':R0,'X0':X0,'B1':B1,'B0':B0}
        self.data['OHLINE'] = form

    def get_UGline(self,sheet):
        ## gen number 
        ### self.data['4UG] = { 'GEN':{bus:bus},' Branch':{[gen1,gen2]:{'rate':,'r1'}}}
        sheets = self.wb[sheet]
        name_sheet = sheet[-1]
        check_bus_list = {}
        row = 2 
        form = {'GEN':{},'JB':[],'Branch':{} , 'Rate':{}, 'R1':{}, 'X1':{}, 'R0':{}, 'X0':{}, 'B1':{}, 'B0':{}}
        while True:
            gen1 = sheets[f'B{row}'].value
            gen2 = sheets[f'C{row}'].value

            if gen1 == None or gen2 == None:
                break
            line = round(float(sheets[f'G{row}'].value),6)
            rate = round(float(sheets[f'I{row}'].value),6)
            r1 = round(float(sheets[f'X{row}'].value),6)
            x1 = round(float(sheets[f'Y{row}'].value),6)
            r0 = round(float(sheets[f'Z{row}'].value),6)
            x0 = round(float(sheets[f'AA{row}'].value),6)
            b1 = round(float(sheets[f'AB{row}'].value),6)
            b0 = b1
            ### get new bus number for bus''' form['GEN'][primary bus] = secondary bus
            if gen1 not in check_bus_list and gen1 % 1000 != 0:
                check_bus_list[gen1] = 1000+self.bus_number
                form['GEN'][self.bus_number] = 1000+self.bus_number
                self.bus_number += 1
                
            if gen2 not in check_bus_list and gen2 % 1000 != 0:
                check_bus_list[gen2] = 1000+self.bus_number
                form['GEN'][self.bus_number] = 1000+self.bus_number
                self.bus_number += 1

            ###
            ##JB
            if gen1 % 1000 == 0 and gen1 % 10000 != 0 and gen1 not in check_bus_list:
                check_bus_list[gen1] = self.JB
                form['JB'].append(self.JB)
                self.JB += 1
            if gen2 % 1000 == 0 and gen2 % 10000 != 0 and gen2 not in check_bus_list:
                check_bus_list[gen2] = self.JB
                form['JB'].append(self.JB)
                self.JB += 1
            ## SUBTATION
            if gen1 % 10000 == 0 and gen1 not in self.data['Subtation']:
                self.data['Subtation'][gen1] = name_sheet
                check_bus_list[gen1] = gen1
            elif gen1 % 10000 == 0 and gen1 in self.data['Subtation'] :
                check_bus_list[gen1] = gen1
            if gen2 % 10000 == 0 and gen2 not in self.data['Subtation']:
                self.data['Subtation'][gen2] = name_sheet
                check_bus_list[gen2] = gen2
            elif gen2 % 10000 == 0 and gen2 in self.data['Subtation'] :
                check_bus_list[gen2] = gen2
            ## line 
            form['Branch'][(check_bus_list[gen1],check_bus_list[gen2])] = line
            form['Rate'][(check_bus_list[gen1],check_bus_list[gen2])] = rate
            form['R1'][(check_bus_list[gen1],check_bus_list[gen2])] = r1
            form ['X1'][(check_bus_list[gen1],check_bus_list[gen2])] = x1
            form['R0'][(check_bus_list[gen1],check_bus_list[gen2])] = r0
            form['X0'][(check_bus_list[gen1],check_bus_list[gen2])] = x0
            form['B1'][(check_bus_list[gen1],check_bus_list[gen2])] = b1
            form['B0'][(check_bus_list[gen1],check_bus_list[gen2])] = b0
            row += 1
        self.data['4UG'][name_sheet] = form

    def get_GEN_impedance(self,sheet):
        sheets = self.wb[sheet]
        name_sheet = sheet[-1]
        R1 = float(sheets['B13'].value)
        X1 = float(sheets['B14'].value)
        Xsub = float(sheets['B16'].value)
        Xtrans = float(sheets['B17'].value)
        Xsyn = float(sheets['B18'].value)
        R2 = float(sheets['B20'].value)
        X2= float(sheets['B21'].value)
        R0 = float(sheets['B23'].value)
        X0 = float(sheets['B24'].value)
        Rg = float(sheets['B26'].value)
        Xg = float(sheets['B27'].value)
        form = {'R1':R1 ,'X1':X1,'Xsub':Xsub,'Xtrans':Xtrans,'Xsyn':Xsyn,'R0':R0,'X0':X0,'R2':R2,'X2':X2,'Rg':Rg,'Xg':Xg}
        self.data['5GEN_IMP'][name_sheet] = form

    def User(self,sheet):
        sheets = self.wb[sheet]
        row = 4
        while True:
            name_sheet = str(sheets[f'A{row}'].value)
            Rsource = sheets[f'B{row}'].value
            Xsource = sheets[f'C{row}'].value
            Rate_GSU = sheets[f'E{row}'].value
            NLL_GSU = sheets[f'F{row}'].value
            Iext_GSU = sheets[f'G{row}'].value
            Rate_MPT = sheets[f'I{row}'].value
            NLL_MPT = sheets[f'J{row}'].value
            Iext_MPT = sheets[f'K{row}'].value
            P_LOAD = sheets[f'M{row}'].value
            CODE_GSU = sheets[f'H{row}'].value
            CODE_MPT = sheets[f'L{row}'].value
            if P_LOAD == None:
                P_LOAD = 0
            Q_LOAD = sheets[f'N{row}'].value
            if Q_LOAD == None:
                Q_LOAD = 0
            CAP_BANK = sheets[f'P{row}'].value
            if CAP_BANK == None:
                CAP_BANK = 0
            AUXI_P_LOAD = sheets[f'R{row}'].value
            if  AUXI_P_LOAD == None:
                AUXI_P_LOAD = 0
            AUXI_Q_LOAD = sheets[f'S{row}'].value
            if AUXI_Q_LOAD == None:
                AUXI_Q_LOAD = 0
            AUXI_CAP_BANK = sheets[f'U{row}'].value   
            if AUXI_CAP_BANK == None:
                AUXI_CAP_BANK = 0
    
            form = {'Rsource':Rsource ,'Xsource':Xsource,'Rate_GSU':Rate_GSU,'NLL_GSU':NLL_GSU,'Iext_GSU':Iext_GSU,'Rate_MPT':Rate_MPT,'NLL_MPT':NLL_MPT,'Iext_MPT':Iext_MPT,'P_LOAD':P_LOAD,'Q_LOAD':Q_LOAD,'CAP_BANK':CAP_BANK,'AUXI_P_LOAD':AUXI_P_LOAD,'AUXI_Q_LOAD':AUXI_Q_LOAD,'AUXI_CAP_BANK':AUXI_CAP_BANK,'CODE_GSU':CODE_GSU,'CODE_MPT':CODE_MPT}
            if name_sheet == None or Rsource == None:
                break
            else:
                self.data['User'][name_sheet] = form
            row += 1
        
    def main(self):
        self.wb = openpyxl.load_workbook(self.path, data_only=True)
        sheets = self.wb.sheetnames
        for sheet in sheets:
            if sheet.startswith("1 General"):
                self.get_gen(sheet)
            if sheet.startswith("2 XFMR Impedance"):
                self.get_2xfmr(sheet)
                self.get_3xfmr(sheet)
            if sheet.startswith("3 OH line impedance"):
                self.get_ohline(sheet)
            if sheet.startswith("4 UG collection sys impedance"):
                self.get_UGline(sheet)
            if sheet.startswith("5 Generator Impedance"):
                self.get_GEN_impedance(sheet)
            if sheet.startswith("0user"):
                self.User(sheet)
        # print(self.data)
        return self.data

class RAW_FILE: 
    def __init__(self,path,data,Vsch): 
        self.path = path 
        self.data = data 
        self.Vsch = Vsch
        print(self.data['Subtation']) 

    def title(self,file):
        file.write("@!IC,SBASE,REV,XFRRAT,NXFRAT,BASFRQ\n")
        file.write("0,  100.00, 35,     0,     1, 60.00     / PSS(R)E-35.6    TUE, JAN 07 2025   1:26\n")
        file.write("GENERAL, THRSHZ=0.0001, PQBRAK=0.7, BLOWUP=5.0, MaxIsolLvls=4, CAMaxReptSln=20, ChkDupCntLbl=0\n")
        file.write("GAUSS, ITMX=100, ACCP=1.6, ACCQ=1.6, ACCM=1.0, TOL=0.0001\n")
        file.write("NEWTON, ITMXN=20, ACCN=1.0, TOLN=0.1, VCTOLQ=0.1, VCTOLV=0.00001, DVLIM=0.99, NDVFCT=0.99\n")
        file.write("ADJUST, ADJTHR=0.005, ACCTAP=1.0, TAPLIM=0.05, SWVBND=100.0, MXTPSS=99, MXSWIM=10\n")
        file.write("TYSL, ITMXTY=20, ACCTY=1.0, TOLTY=0.00001\n")
        file.write("SOLVER, FNSL, ACTAPS=1, AREAIN=1, PHSHFT=0, DCTAPS=0, SWSHNT=1, FLATST=1, VARLIM=0, NONDIV=0\n")
        file.write('RATING, 1, "RATE1 ", "RATING SET 1                    "\n')
        file.write('RATING, 2, "RATE2 ", "RATING SET 2                    "\n')
        file.write('RATING, 3, "RATE3 ", "RATING SET 3                    "\n')
        file.write('RATING, 4, "RATE4 ", "RATING SET 4                    "\n')
        file.write('RATING, 5, "RATE5 ", "RATING SET 5                    "\n')
        file.write('RATING, 6, "RATE6 ", "RATING SET 6                    "\n')
        file.write('RATING, 7, "RATE7 ", "RATING SET 7                    "\n')
        file.write('RATING, 8, "RATE8 ", "RATING SET 8                    "\n')
        file.write('RATING, 9, "RATE9 ", "RATING SET 9                    "\n')
        file.write('RATING,10, "RATE10", "RATING SET 10                   "\n')
        file.write('RATING,11, "RATE11", "RATING SET 11                   "\n')
        file.write('RATING,12, "RATE12", "RATING SET 12                   "\n')
    
    def bus(self,file): 
        file.write("0 / END OF SYSTEM-WIDE DATA, BEGIN BUS DATA\n") 
        file.write("@!   I,'NAME        ', BASKV, IDE,AREA,ZONE,OWNER, VM,        VA,    NVHI,   NVLO,   EVHI,   EVLO\n") 
        
        ## create bus for gen and pri bus
        for key in self.data['4UG']:    ## key _1,_2
            for key1 in self.data['4UG'][key]['GEN']:   ## key1 gen_number : value primary_number
                gen_number = key1
                primary_number = self.data['4UG'][key]['GEN'][key1]
                baskv = self.data['1GEN'][key]['kV']
                collect_kV = self.data['1GEN'][key]['collect_kV']
                interconnec_kV = self.data['1GEN'][key]['interconnec_kV']
                form = f'{gen_number},GEN_{gen_number},{baskv},2,1,1,1,1,0,1.1,0.9,1.1,0.9\n'
                form1 = f'{primary_number},BUS_{primary_number},{collect_kV},1,1,1,1,1,0,1.1,0.9,1.1,0.9\n'
                file.write(form) 
                file.write(form1) 
            ## create bus for JB
            for bus in self.data['4UG'][key]['JB']:
                form = f'{bus},BUS_{bus},{collect_kV},1,1,1,1,1,0,1.1,0.9,1.1,0.9\n'
                file.write(form)
        
        dem = 1 
        ## create substation 
        for key in self.data['Subtation']: ### 110000,120000
            for key1 in self.data['Subtation'][key]: ##key1 _1,_2
                Tertiary_volt = self.data['3XFMR'][key1]['Tertiary_volt']
                form = f'{key},MPT{dem}_SEC,{collect_kV},1,1,1,1,1,0,1.1,0.9,1.1,0.9\n'
                form1 = f'{key+3},MPT{dem}_TER,{Tertiary_volt},1,1,1,1,1,0,1.1,0.9,1.1,0.9\n'
                form2 = f'{key+2},DUMMY{dem},{interconnec_kV},1,1,1,1,1,0,1.1,0.9,1.1,0.9\n'
                file.write(form)    
                file.write(form1)
                file.write(form2)
                dem+=1
        ## creat dummy sub and poi
        file.write(f"960000,DUMMY_SUB,{interconnec_kV},1,1,1,1,1,0,1.1,0.9,1.1,0.9\n")
        file.write(f"999997,DUMMY_POI,{interconnec_kV},1,1,1,1,1,0,1.1,0.9,1.1,0.9\n")
        file.write(f"970000,POI,{interconnec_kV},3,1,1,1,1,0,1.1,0.9,1.1,0.9\n")
    
    def load(self,file):
        file.write("0 / END OF BUS DATA, BEGIN LOAD DATA\n")
        file.write("@!   I,'ID',STAT,AREA,ZONE,      PL,        QL,        IP,        IQ,        YP,        YQ, OWNER,SCALE,INTRPT,  DGENP,     DGENQ,DGENF,'  LOAD TYPE '\n")

        ## LOAD AT HIGH SIDE MPT
        for key in self.data['Subtation']: ## key 110000,120000
            for key1 in self.data['Subtation'][key]: ##key1 _1,_2
                P_LOAD = self.data['User'][key1]['P_LOAD']
                Q_LOAD = self.data['User'][key1]['Q_LOAD']
                
                if P_LOAD == 0 and Q_LOAD == 0:
                    print(f"NO LOAD AT {key}")
                else:   
                    form = f"{key},'1',1,1,1,{P_LOAD},{Q_LOAD},0,0,0,0,1,1,0,0,0,0,''\n"
                    file.write(form)
        ## LOAD AT hight side GSU
        for key in self.data['4UG']: ## key _1,_2
            for key1 in self.data['4UG'][key]['GEN']: ## key1 gen_number : value primary_number
                Auxi_P_LOAD = self.data['User'][key]['AUXI_P_LOAD']
                Auxi_Q_LOAD = self.data['User'][key]['AUXI_Q_LOAD']
                if Auxi_P_LOAD == 0 and Auxi_Q_LOAD == 0:
                    print(f"NO AUXI LOAD ")
                else:
                    gen_number = self.data['4UG'][key]['GEN'][key1] 
                    form = f"{gen_number},'1',1,1,1,{Auxi_P_LOAD},{Auxi_Q_LOAD},0,0,0,0,1,1,0,0,0,0,''\n"
                    file.write(form)

    def fix_shunt(self,file):
        file.write("0 / END OF LOAD DATA, BEGIN FIXED SHUNT DATA\n")
        file.write("@!   I,'ID',STATUS,  GL,        BL\n")

    def gen(self,file):
        file.write("0 / END OF FIXED SHUNT DATA, BEGIN GENERATOR DATA\n")
        file.write("@!   I,'ID',      PG,        QG,        QT,        QB,     VS,    IREG,NREG,     MBASE,     ZR,         ZX,         RT,         XT,     GTAP,STAT, RMPCT,      PT,        PB,BASLOD,O1,    F1,  O2,    F2,  O3,    F3,  O4,    F4,WMOD, WPF\n")
        for key in self.data['4UG']:    ## key _1,_2
            for key1 in self.data['4UG'][key]['GEN']:   ## key1 gen_number : value primary_number
                gen_number = key1
            
                Pgen = self.data['1GEN'][key]['Pgen']
                Pmax = self.data['1GEN'][key]['Pmax']
                Pmin = self.data['1GEN'][key]['Pmin']
                Qmax = self.data['1GEN'][key]['Qmax']
                Qmin = self.data['1GEN'][key]['Qmin']
                MBASE = self.data['1GEN'][key]['MBASE']
                Rsource = self.data['User'][key]['Rsource']
                Xsource = self.data['User'][key]['Xsource']
                form = f"{gen_number},'1',{Pgen},0,{Qmax},{Qmin},{self.Vsch},999997,0,{MBASE},{Rsource},{Xsource},0,0,1,1,100,{Pmax},{Pmin},0,1,1,0,1,0,1,0,1,1,1\n"
                file.write(form)
        file.write("970000,'1 ',  0,    0,  9999.000, -9999.000,1.00000,970000,   0, 10000.000, 0.00000E+0, 1.00000E-1, 0.00000E+0, 1.00000E-2,1.00000,1,  100.0,  9999.000, -9999.000, 0,   1,1.0000\n")
    
    def branch(self,file):
        file.write("0 / END OF GENERATOR DATA, BEGIN BRANCH DATA\n")
        file.write("@!   I,     J,'CKT',      R,           X,       B,                   'N A M E'                 ,  RATE1,  RATE2,  RATE3,  RATE4,  RATE5,  RATE6,  RATE7,  RATE8,  RATE9, RATE10, RATE11, RATE12,   GI,      BI,      GJ,      BJ,STAT,MET, LEN,  O1,  F1,    O2,  F2,    O3,  F3,    O4,  F4\n")
        for key in self.data['4UG']:  ## key _1,_2
            for key1 in self.data['4UG'][key]['Branch']: ## key1 gen1,gen2 
                bus1 = key1[0]
                bus2 = key1[1]
                # line = self.data['4UG'][key]['Branch'][key1]
                rate = round(self.data['4UG'][key]['Rate'][key1],2)
                r1 = self.data['4UG'][key]['R1'][key1]
                x1 = self.data['4UG'][key]['X1'][key1]
                b1 = self.data['4UG'][key]['B1'][key1]
                if bus1 % 10000 == 0 or bus2 % 10000 == 0:  ### substation de la 2 
                    form = f"{bus1},{bus2},'1',{r1},{x1},{b1},'',{rate},{rate},{rate},0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,1,1,1\n"
                    file.write(form)
                else:
                    form = f"{bus1},{bus2},'1',{r1},{x1},{b1},'',{rate},{rate},{rate},0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1\n"
                    file.write(form)

        ## dummy line
        for key in self.data['Subtation']:
            
            bus1 = key+2
            r1 = 0
            x1 = 0.0001
            b1 = 0
            rate = 9999
            form = f"{bus1},{960000},'1',{r1},{x1},{b1},'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,1\n"
            file.write(form)
        
        ### oh liner
        r = self.data['OHLINE']['R1']
        x = self.data['OHLINE']['X1']
        b = self.data['OHLINE']['B1']
        rate = round(self.data['OHLINE']['RATE'],2)
        line = self.data['OHLINE']['LINE']
        file.write(f"960000,999997,'1',{r},{x},{b},'',{rate},{rate},{rate},0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,{line},1,1\n")
        file.write(f"999997,970000,'1',0,0.0001,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,0,1,1\n")
        
    def switch_device(self,file):
        file.write("0 / END OF BRANCH DATA, BEGIN SYSTEM SWITCHING DEVICE DATA\n")
        file.write("@!   I,     J,'CKT',          X,  RATE1,  RATE2,  RATE3,  RATE4,  RATE5,  RATE6,  RATE7,  RATE8,  RATE9, RATE10, RATE11, RATE12, STAT,NSTAT,  MET,STYPE,'NAME'\n")
    
    def XFMR(self,file):
        file.write("0 / END OF SYSTEM SWITCHING DEVICE DATA, BEGIN TRANSFORMER DATA\n")
        file.write("@!   I,     J,     K,'CKT',CW,CZ,CM,     MAG1,        MAG2,NMETR,               'N A M E',               STAT,O1,  F1,    O2,  F2,    O3,  F3,    O4,  F4,     'VECGRP', ZCOD\n")
        file.write("@!   R1-2,       X1-2, SBASE1-2,     R2-3,       X2-3, SBASE2-3,     R3-1,       X3-1, SBASE3-1, VMSTAR,   ANSTAR\n")
        file.write("@!WINDV1, NOMV1,   ANG1, RATE1-1, RATE1-2, RATE1-3, RATE1-4, RATE1-5, RATE1-6, RATE1-7, RATE1-8, RATE1-9,RATE1-10,RATE1-11,RATE1-12,COD1,CONT1,NOD1,  RMA1,   RMI1,   VMA1,   VMI1, NTP1,TAB1, CR1,    CX1,  CNXA1\n")
        file.write("@!WINDV2, NOMV2,   ANG2, RATE2-1, RATE2-2, RATE2-3, RATE2-4, RATE2-5, RATE2-6, RATE2-7, RATE2-8, RATE2-9,RATE2-10,RATE2-11,RATE2-12,COD2,CONT2,NOD2,  RMA2,   RMI2,   VMA2,   VMI2, NTP2,TAB2, CR2,    CX2,  CNXA2\n")
        file.write("@!WINDV3, NOMV3,   ANG3, RATE3-1, RATE3-2, RATE3-3, RATE3-4, RATE3-5, RATE3-6, RATE3-7, RATE3-8, RATE3-9,RATE3-10,RATE3-11,RATE3-12,COD3,CONT3,NOD3,  RMA3,   RMI3,   VMA3,   VMI3, NTP3,TAB3, CR3,    CX3,  CNXA3\n")

        ### 2xfmr
        for key in self.data['4UG']: ## key _1,_2
            ## get 0user
            NLL_GSU = self.data['User'][key]['NLL_GSU'] 
            Iext_GSU = self.data['User'][key]['Iext_GSU']

            for key1 in self.data['4UG'][key]['GEN']: ## key1 gen_number : value primary_number   1 : 1001 
                gen_number = key1
                primary_number = self.data['4UG'][key]['GEN'][key1]

                Primary_volt = self.data['1GEN'][key]['kV']
                Secondary_volt = self.data['1GEN'][key]['collect_kV']
                
                R1 = self.data['2XFMR'][key]['R1']
                X1 = self.data['2XFMR'][key]['X1']
                Vector = self.data['2XFMR'][key]['Vector']
                MBASE = self.data['2XFMR'][key]['MBASE']
                # Primary_volt = self.data['2XFMR'][key]['Primary_volt']
                # Secondary_volt = self.data['2XFMR'][key]['Secondary_volt']

                form = f'{primary_number},{gen_number},0,"1",1,2,1,{NLL_GSU},{Iext_GSU},2,"GSU_{gen_number}",1,1,1,0,1,0,1,0,1,"{Vector}"\n'
                form1 = f'{R1},{X1},{MBASE}\n'
                form2= f'1,{Secondary_volt},0,{MBASE},{MBASE},{MBASE},0,0,0,0,0,0,0,0,0,0,0,0,1.05,0.95,1.1,0.9,5,0,0,0,0\n'
                form3 = f'1,{Primary_volt}\n'
                file.write(form) 
                file.write(form1)
                file.write(form2)
                file.write(form3)
            ## 3xfmr
        for key in self.data['Subtation']: ## key 110000,120000
            for key1 in self.data['Subtation'][key]: ##key1 _1,_2
                NLL_MPT = self.data['User'][key1]['NLL_MPT']
                Iext_MPT = self.data['User'][key1]['Iext_MPT']
                Rate_MPT = self.data['User'][key1]['Rate_MPT']
                R12 = self.data['3XFMR'][key1]['R12']
                X12 = self.data['3XFMR'][key1]['X12']
                R23 = self.data['3XFMR'][key1]['R23']
                X23 = self.data['3XFMR'][key1]['X23']
                R31 = self.data['3XFMR'][key1]['R31']
                X31 = self.data['3XFMR'][key1]['X31']
                MBASE = self.data['3XFMR'][key1]['MBASE']
                R01 = self.data['3XFMR'][key1]['R01']
                X01 = self.data['3XFMR'][key1]['X01']
                R02 = self.data['3XFMR'][key1]['R02']
                X02 = self.data['3XFMR'][key1]['X02']
                R03 = self.data['3XFMR'][key1]['R03']
                X03 = self.data['3XFMR'][key1]['X03']
                Primary_volt = self.data['3XFMR'][key1]['Primary_volt']
                Secondary_volt = self.data['3XFMR'][key1]['Secondary_volt']
                Tertiary_volt = self.data['3XFMR'][key1]['Tertiary_volt']
                Vector = self.data['3XFMR'][key1]['Vector']
                
                form = f'{key+2},{key},{key+3},"1",1,2,1,{NLL_MPT},{Iext_MPT},2,"MPT_{key1}",1,1,1,0,1,0,1,0,1,"{Vector}" \n'
                form1 = f'{R12},{X12},{MBASE},{R23},{X23},{MBASE},{R31},{X31},{MBASE},1,0\n'
                form2= f'1,{Primary_volt},0,{Rate_MPT},{Rate_MPT},{Rate_MPT},0,0,0,0,0,0,0,0,0,1,{key},0,1.1,0.9,1.02,0.98,33,0,0,0,0\n'
                form3 = f'1,{Secondary_volt},0,{Rate_MPT},{Rate_MPT},{Rate_MPT},0,0,0,0,0,0,0,0,0,0,0,0,1.1,0.9,1.02,0.98,33,0,0,0,0\n'
                form4 = f'1,{Tertiary_volt},0,{Rate_MPT},{Rate_MPT},{Rate_MPT},0,0,0,0,0,0,0,0,0,0,0,0,1.1,0.9,1.02,0.98,33,0,0,0,0\n'
                file.write(form)
                file.write(form1)
                file.write(form2)
                file.write(form3)
                file.write(form4)
    
    def other(self,file):
        file.write("0 / END OF TRANSFORMER DATA, BEGIN AREA DATA\n")
        file.write("@! I,   ISW,    PDES,     PTOL,    'ARNAME'\n")
        file.write("0 / END OF AREA DATA, BEGIN TWO-TERMINAL DC DATA\n")
        file.write("@!  'NAME',   MDC,    RDC,     SETVL,    VSCHD,    VCMOD,    RCOMP,   DELTI,METER   DCVMIN,CCCITMX,CCCACC\n")
        file.write("@! IPR,NBR,  ANMXR,  ANMNR,   RCR,    XCR,   EBASR,  TRR,    TAPR,   TMXR,   TMNR,   STPR,    ICR,NDR,   IFR,   ITR,'IDR', XCAPR\n")
        file.write("@! IPI,NBI,  ANMXI,  ANMNI,   RCI,    XCI,   EBASI,  TRI,    TAPI,   TMXI,   TMNI,   STPI,    ICI,NDI,   IFI,   ITI,'IDI', XCAPI\n")
        file.write("0 / END OF TWO-TERMINAL DC DATA, BEGIN VSC DC LINE DATA\n")
        file.write("@!  'NAME',   MDC,  RDC,   O1,  F1,    O2,  F2,    O3,  F3,    O4,  F4\n")
        file.write("@!IBUS,TYPE,MODE,  DCSET,  ACSET,  ALOSS,  BLOSS,MINLOSS,  SMAX,   IMAX,   PWF,     MAXQ,   MINQ, VSREG,NREG, RMPCT\n")
        file.write("0 / END OF VSC DC LINE DATA, BEGIN IMPEDANCE CORRECTION DATA\n")
        file.write("@!I,  T1,   Re(F1), Im(F1),   T2,   Re(F2), Im(F2),   T3,   Re(F3), Im(F3),   T4,   Re(F4), Im(F4),   T5,   Re(F5), Im(F5),   T6,   Re(F6), Im(F6)\n")
        file.write("@!    T7,   Re(F7), Im(F7),   T8,   Re(F8), Im(F8),   T9,   Re(F9), Im(F9),   T10, Re(F10),Im(F10),   T11, Re(F11),Im(F11),   T12, Re(F12),Im(F12)\n")
        file.write("0 / END OF IMPEDANCE CORRECTION DATA, BEGIN MULTI-TERMINAL DC DATA\n")
        file.write("@!  'NAME',    NCONV,NDCBS,NDCLN,  MDC, VCONV,   VCMOD, VCONVN\n")
        file.write("@!  IB, N,  ANGMX,  ANGMN,   RC,     XC,     EBAS,   TR,    TAP,    TPMX,   TPMN,   TSTP,   SETVL,   DCPF,  MARG,CNVCOD\n")
        file.write("@!IDC, IB,AREA,ZONE,   'DCNAME',  IDC2, RGRND,OWNER\n")
        file.write("@!IDC,JDC,'DCCKT',MET,  RDC,      LDC\n")
        file.write("0 / END OF MULTI-TERMINAL DC DATA, BEGIN MULTI-SECTION LINE DATA\n")
        file.write("@!   I,     J,'ID',MET,DUM1,  DUM2,  DUM3,  DUM4,  DUM5,  DUM6,  DUM7,  DUM8,  DUM9\n")
        file.write("0 / END OF MULTI-SECTION LINE DATA, BEGIN ZONE DATA\n")
        file.write("@! I,   'ZONAME'\n")
        file.write("0 / END OF ZONE DATA, BEGIN INTER-AREA TRANSFER DATA\n")
        file.write("@!ARFROM,ARTO,'TRID',PTRAN\n")
        file.write("0 / END OF INTER-AREA TRANSFER DATA, BEGIN OWNER DATA\n")
        file.write("@! I,   'OWNAME'\n")
        file.write("0 / END OF OWNER DATA, BEGIN FACTS DEVICE DATA\n")
        file.write("@!  'NAME',         I,     J,MODE,PDES,   QDES,  VSET,   SHMX,   TRMX,   VTMN,   VTMX,   VSMX,    IMX,   LINX,   RMPCT,OWNER,  SET1,    SET2,VSREF, FCREG,NREG,   'MNAME'\n")
    
    def switch_shunt(self,file):
        file.write("0 / END OF FACTS DEVICE DATA, BEGIN SWITCHED SHUNT DATA\n")
        file.write("@!   I,'ID',MODSW,ADJM,ST, VSWHI,  VSWLO, SWREG,NREG, RMPCT,   'RMIDNT',     BINIT,S1,N1,    B1, S2,N2,    B2, S3,N3,    B3, S4,N4,    B4, S5,N5,    B5, S6,N6,    B6, S7,N7,    B7, S8,N8,    B8\n")
        ## CAPBANK at MPT 
        for key in self.data['Subtation']: ## key 110000,120000
            for key1 in self.data['Subtation'][key]: ##key1 _1,_2
                CAPBANK = self.data['User'][key1]['CAP_BANK']
                
                if CAPBANK == 0:
                    print(f"NO CAPBANK AT {key}")
                else:     #1004,'1 ',   0,  0,  1,1.05000,0.95000,  1004,   0, 100.0,'            ',  15.00, 1, 1,  15.00
                    form = f"{key},'1 ',   0,  0,  1,1.05000,0.95000,  {key},   0, 100.0,'            ',  {CAPBANK}, 1, 1,  {CAPBANK}\n"
                    file.write(form)
        ## LOAD AT hight side GSU
        for key in self.data['4UG']: ## key _1,_2
            for key1 in self.data['4UG'][key]['GEN']: ## key1 gen_number : value primary_number
                Auxi_CAP_BANK = self.data['User'][key]['AUXI_CAP_BANK']

                if Auxi_CAP_BANK == 0 :
                    continue
                else:
                    gen_number = self.data['4UG'][key]['GEN'][key1] 
                    form = f"{gen_number},'1 ',   0,  0,  1,1.05000,0.95000,  {gen_number},   0, 100.0,'            ',  {Auxi_CAP_BANK}, 1, 1,  {Auxi_CAP_BANK}\n"
                    file.write(form)        
    
    def other2(self,file):
        file.write("0 / END OF SWITCHED SHUNT DATA, BEGIN GNE DATA\n")
        file.write("@!  'NAME',        'MODEL',     NTERM,BUS1...BUSNTERM,NREAL,NINTG,NCHAR\n")
        file.write("@!ST,OWNER,NMETR\n")
        file.write("@! REAL1...REAL(MIN(10,NREAL))\n")
        file.write("@! INTG1...INTG(MIN(10,NINTG))\n")
        file.write("@! CHAR1...CHAR(MIN(10,NCHAR))\n")
        file.write("0 / END OF GNE DATA, BEGIN INDUCTION MACHINE DATA\n")
        file.write("@!   I,'ID',ST,SC,DC,AREA,ZONE,OWNER,TC,BC, MBASE,RATEKV,PC,  PSET,     H,      A,      B,      D,      E,     RA,        XA,        XM,        R1,        X1,        R2,        X2,        X3,       E1,    SE1,   E2,    SE2,   IA1,   IA2, XAMULT\n")
        file.write("0 / END OF INDUCTION MACHINE DATA, BEGIN SUBSTATION DATA\n")
        file.write("0 / END OF SUBSTATION DATA\n")
        file.write("Q\n")        
    
    def main(self):
        path = self.path.replace(".xlsm",".raw")
        with open(path, "w") as file:
            self.title(file)
            self.bus(file)
            self.load(file)
            self.fix_shunt(file)
            self.gen(file)
            self.branch(file)
            self.switch_device(file)
            self.XFMR(file)
            self.other(file)
            self.switch_shunt(file)
            self.other2(file)
            
class SEQ_FILE:
    def __init__(self,path,data):
        self.path = path
        self.data = data
    
    def title(self,file):
        file.write("@!IC, REV\n")
        file.write("0,     35           / PSS(R)E Xplore-35.4    TUE, JAN 21 2025  16:24\n")
        file.write("RPTFORMAT, AMPOUT=0, POLROU=0, AMPOUTZ=0, POLROUZ=0\n")
        file.write("MOV, ITERATIONS=20, TOLERANCE=0.01, MOVALPHA=0.3\n")
        file.write("SCMODEL, SCNRML=1\n")
        pass
    
    def gen(self,file):
        file.write("0 / END OF SYSTEM-WIDE DATA, BEGIN GENERATOR DATA\n")
        file.write("@!   I,'ID',       ZRPOS,      ZXPPDV,       ZXPDV,       ZXSDV,       ZRNEG,     ZXNEGDV,         ZR0,       ZX0DV,CZG,       ZRG,         ZXG, REFDEG\n")
        for key in self.data['4UG']:    ## key _1,_2
            for key1 in self.data['4UG'][key]['GEN']:   ## key1 gen_number : value primary_number
                gen_number = key1
                R1 = self.data['5GEN_IMP'][key]['R1']
                X1 = self.data['5GEN_IMP'][key]['X1']
                Xsub = self.data['5GEN_IMP'][key]['Xsub']
                Xtrans = self.data['5GEN_IMP'][key]['Xtrans']
                Xsync = self.data['5GEN_IMP'][key]['Xsyn']
                R0 = self.data['5GEN_IMP'][key]['R0']
                X0 = self.data['5GEN_IMP'][key]['X0']
                R2 = self.data['5GEN_IMP'][key]['R2']
                X2 = self.data['5GEN_IMP'][key]['X2']
                Rg = self.data['5GEN_IMP'][key]['Rg']
                Xg = self.data['5GEN_IMP'][key]['Xg']
                form = f"{gen_number},'1',{R1},{Xsub},{Xtrans},{Xsync},{R2},{X2},{R0},{X0},1,{Rg},{Xg},0\n"
                file.write(form)
    
    def load(self,file):
        file.write("0 / END OF GENERATOR DATA, BEGIN LOAD DATA\n")
        file.write("@!   I,'ID',        PNEG,        QNEG,GRDFLG,  PZERO,       QZERO\n")
    
    def branch(self,file):
        file.write("0  / END OF LOAD DATA, BEGIN ZERO SEQ. NON-TRANSFORMER BRANCH DATA\n")
        file.write("@!   I,     J,'ICKT',    RLINZ,      XLINZ,       BCHZ,         GI,         BI,         GJ,         BJ,        IPR,SCTYP\n")
        for key in self.data['4UG']:    ## key _1,_2
            for key1 in self.data['4UG'][key]['Branch']:    ## key1 gen1,gen2
                bus1 = key1[0]
                bus2 = key1[1]
                R0 = self.data['4UG'][key]['R0'][key1]
                X0 = self.data['4UG'][key]['X0'][key1]
                B0 = self.data['4UG'][key]['B0'][key1]
                form = f"{bus1},{bus2},'1',{R0},{X0},{B0},0,0,0,0,0,0\n"
                file.write(form)

        for key in self.data['Subtation']:
            bus1 = key+2       
            bus2 = 960000
            R0 = 0
            X0 = 0.0001
            B0 = 0
            form = f"{bus1},{bus2},'1',{R0},{X0},{B0},0,0,0,0,0,0\n"
            file.write(form)

        R0 = self.data['OHLINE']['R0']
        X0 = self.data['OHLINE']['X0']
        B0 = self.data['OHLINE']['B0']
        bus1 = 960000
        bus2 = 999997
        form = f"{bus1},{bus2},'1',{R0},{X0},{B0},0,0,0,0,0,0\n"
        file.write(form)

        bus1 = 999997
        bus2 = 970000
        form = f"{bus1},{bus2},'1',0,0.0001,0,0,0,0,0,0,0,0\n"
        file.write(form)
    
    def other(self,file):
        file.write("0  / END OF ZERO SEQ. NON-TRANSFORMER BRANCH DATA, BEGIN ZERO SEQ. MUTUAL DATA\n")
        file.write("@!   I,     J,'ICKT1',  K,     L,'ICKT2',      RM,         XM,    BIJ1,    BIJ2,    BKL1,    BKL2\n")
     
    
    def XFMR(self,file):
        file.write("0  / END OF ZERO SEQ. MUTUAL DATA, BEGIN ZERO SEQ. TRANSFORMER DATA\n")
        file.write("@!   I,     J,     K,'ICKT',CZ0,CZG,CC,   RG1,        XG1,        R01,        X01,        RG2,        XG2,        R02,        X02,     RNUTRL,     XNUTRL\n")
        file.write("@!   I,     J,     K,'ICKT',CZ0,CZG,CC,   RG1,        XG1,        R01,        X01,        RG2,        XG2,        R02,        X02,        RG3,        XG3,        R03,        X03,     RNUTRL,     XNUTRL\n")
        for key in self.data['4UG']:    ## key _1,_2
            for key1 in self.data['4UG'][key]['GEN']:   ## key1 gen_number : value primary_number
                gen_number = key1
                primary_number = self.data['4UG'][key]['GEN'][key1]
                R0 = self.data['2XFMR'][key]['R0']
                X0 = self.data['2XFMR'][key]['X0']
                CODE_GSU = self.data['User'][key]['CODE_GSU']
                form = f"{gen_number},{primary_number},0,'1',2,2,{CODE_GSU},0,0,{R0},{X0},0,0,0,0,0,0\n"
                file.write(form)
        for key in self.data['Subtation']:    ## 110000 : value _1
            for key1 in self.data['Subtation'][key]:
                pri = key
                ter = key+3
                sec = key+2
                R01 = self.data['3XFMR'][key1]['R01']
                X01 = self.data['3XFMR'][key1]['X01']
                R02 = self.data['3XFMR'][key1]['R02']
                X02 = self.data['3XFMR'][key1]['X02']  
                R03 = self.data['3XFMR'][key1]['R03']
                X03 = self.data['3XFMR'][key1]['X03']        
                CODE_MPT = self.data['User'][key1]['CODE_MPT']                      
                form = f"{sec},{pri},{ter},'1',2,2,{CODE_MPT},0,0,{R01},{X01},0,0,{R02},{X02},0,0,{R03},{X03},0,0\n"
                file.write(form)
    
    def other2(self,file):
        file.write("0  / END OF ZERO SEQ. TRANSFORMER DATA, BEGIN ZERO SEQ. SWITCHED SHUNT DATA\n")
        file.write("@!   I,'ID',       BZ1,       BZ2,       BZ3,       BZ4,       BZ5,       BZ6,       BZ7,       BZ8\n")
        file.write("0  / END OF ZERO SEQ. SWITCHED SHUNT DATA, BEGIN ZERO SEQ. FIXED SHUNT DATA\n")
        file.write("@!   I,'ID',      GSZERO,      BSZERO\n")
        file.write("0  / END OF ZERO SEQ. FIXED SHUNT DATA, BEGIN INDUCTION MACHINE DATA\n")
        file.write("@!   I,'ID',CZG,GRDFLG,ILR2IR,       RTOX,         ZR0,         ZX0,         ZRG,         ZXG,  ILR2IR_TRN,    RTOX_TRN,  ILR2IR_NEG,    RTOX_NEG\n")
        file.write("0  / END OF INDUCTION MACHINE DATA, BEGIN NON-CONVENTIONAL SOURCE TABLE DATA\n")
        file.write("@!'TABLE NAME ', TYP ,      T1,     C1P,     C1Q,      T2,     C2P,     C2Q,      T3,     C3P,     C3Q,      T4,     C4P,     C4Q,      T5,     C5P,     C5Q,      T6,     C6P,     C6Q\n")
        file.write("@!                          T7,     C7P,     C7Q,      T8,     C8P,     C8Q,      T9,     C9P,     C9Q,     T10,    C10P,    C10Q,     T11,    C11P,    C11Q,     T12,    C12P,    C12Q\n")
        file.write("@!                         ...\n")
        file.write("0  / END OF NON-CONVENTIONAL SOURCE TABLE DATA, BEGIN NON-CONVENTIONAL SOURCE MACHINE DATA\n")
        file.write("@!   I,'ID', TYP ,'   POSTBL   ','   NEGTBL   ',  IFMAX ,  DBVMIN,  DBVMAX\n")
        file.write("0  / END OF NON-CONVENTIONAL SOURCE MACHINE DATA\n")
        file.write("Q\n")

    def main(self):
        path = self.path.replace(".xlsm",".seq")
        with open(path, "w") as file:
            self.title(file)
            self.gen(file)
            self.load(file)
            self.branch(file)
            self.other(file)
            self.XFMR(file)
            self.other2(file)

if __name__ == '__main__':
    path = r"D:\1_GITHUB\Code-For-Team-MQT\Detail model\Aldrin\2025-11-18_Aldrin_138_Strorage_CLS.xlsm"
    Vsch = 1.034
    data = Get_CLS(path).main()
    # cls = Get_CLS(path)
    # cls.main()
    raw= RAW_FILE(path,data,Vsch)
    raw.main()
    print('Raw done')
    seq = SEQ_FILE(path,data)
    seq.main()
    print('SEQ done ')
