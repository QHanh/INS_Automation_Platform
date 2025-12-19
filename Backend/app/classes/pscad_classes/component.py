from lxml import etree
import xml.etree.ElementTree as ET
from xml.dom import minidom
import mhi.pscad
import openpyxl
import re
import sys
import math
import os

class PSCAD:
    def __init__(self):
        # self.file_path = file_path
        # self.tree = etree.parse(file_path)
        # self.root = self.tree.getroot()

        pass
    def param_list(self, params,paramlist,val: str = ""):
        try:
            for key, val in params.items():
                etree.SubElement(paramlist, "param", name=key, value=val)   
        except:
            for key in params:
                etree.SubElement(paramlist, "param", name=key, value=val)
    
    def create_bus_wire(self,
        bus_id: int,
        x: int, y: int,
        BaseKV: float = 0.0,
        w: int = 45, h: int = 82,
        name: str = "",
        bus_name: str = "Bus_1",
        orient: str = "0",
        disable: str = "false"
    ) -> etree._Element:
        wire = etree.Element(
            "Wire",
            classid="Bus",
            id=str(bus_id),
            name=name,
            x=str(x),
            y=str(y),
            w=str(w),
            h=str(h),
            orient=orient,
            disable=disable
        )

        # Vertex
        v1 = etree.SubElement(wire, "vertex", x="0", y="0")
        v2 = etree.SubElement(wire, "vertex", x="0", y=str(h - 10))
        # Param list
        paramlist = etree.SubElement(wire, "paramlist", link="-1", name="")

        # Các tham số mặc định
        params = {
            "Name": bus_name,
            "BaseKV": f"{BaseKV} [kV]",
            "Vrms": "0",
            "VA": "0.0",
            "VM": "1.0",
            "type": "0",
            "VRMS": "0"
        }
        self.param_list(params, paramlist)
        # for key, val in params.items():
        #     etree.SubElement(paramlist, "param", name=key, value=val)

        return wire
    
    def create_orthogonal_wire(self,
        x: int, y: int,
        w: int = 28, h: int = 28,
        flag = False,
        orient: str = "0",
        disable: str = "false",
        x1 = [], y1 =  [],
        number_wire: int = 1,
        id=""
    ) -> etree._Element:
        wire = etree.Element(
            "Wire",
            classid="WireOrthogonal",
            id=id,
            name="",
            x=str(x),
            y=str(y),
            w=str(w),
            h=str(h),
            orient=orient,
            disable=disable
        )
        etree.SubElement(wire, "vertex", x="0", y="0")
        ## if flag = True thì vẽ theo chiều dọc, ngược lại vẽ theo chiều ngang
        if flag == True and number_wire == 1:
            etree.SubElement(wire, "vertex", x="0", y=str(h - 10))
        elif flag == False and number_wire == 1:
            etree.SubElement(wire, "vertex", x=str(w - 10), y="0")
        if number_wire != 1:
            for i in range(number_wire):
                etree.SubElement(wire, "vertex", x=str(x1[i]), y=str(y1[i]))
        return wire
    
    def create_transformer_3w(self,
        comp_id: int,
        x: int, y: int,
        w: int = 116, h: int = 116,
        V_W3 = 13.8,
        Sbase: float = 100.0,
        orient: str = "4",
        NLL: float = 0.0,
        Vector = ["0", "0", "1"],
        R12: float = 0.0,
        X12: float = 0.0,
        X23: float = 0.0,
        X13: float = 0.0,
        z: str = "0",
        link: str = "-1",
        disable: str = "false",
        defn: str = "master:xfmr-3p3w2",
        
    ) -> etree._Element:

        user = etree.Element(
            "User",
            classid="UserCmp",
            defn=defn,
            id=str(comp_id),
            x=str(x),
            y=str(y),
            w=str(w),
            h=str(h),
            z=z,
            orient=orient,
            link=link,
            q="4",
            disable=disable
        )
     
        paramlist = etree.SubElement(user, "paramlist", link="-1", name="", crc="")

        default_params = {
            "Name": "",
            "Tmva": f"{Sbase}",
            "f": "Freq_ref",
            "YD1": Vector[0],
            "YD2": Vector[1],
            "YD3": Vector[2],
            "Lead": "1",
            "Xl12": f"{X12} [pu]",
            "Xl13": f"{X13} [pu]",
            "Xl23": f"{X23} [pu]",
            "Ideal": "0",
            "NLL": f"{NLL/Sbase/10e6} [pu]",
            "CuL": "0.0 [pu]",
            "Tap": "1",
            "View": "1",
            "Dtls": "0",
            "V1": "VHV",
            "V2": "VMV",
            "V3": f"{V_W3} [kV]",
            "Enab": "0",
            "Sat": "0",
            "Xair": "0.2 [pu]",
            "Tdc": "0.0 [s]",
            "Xknee": "1.17 [pu]",
            "Txk": "0.0 [s]",
            "Im1": "2.0 [%]",
            "CuL12": f"{R12} [pu]",
            "CuL13": f"{R12} [pu]",
            "CuL23": f"{R12} [pu]",
            "Hys": "0",
            "Fremn1": "0.0",
            "Fremn2": "0.0",
            "Fremn3": "0.0",
            "LW2": "10",
            "Bnom": "1.7",
            "material": "1",
            "C": "0.1",
            "K": "5.0e-5",
            "BETA": "0.96",
            "alpha": "1.325e-5",
            "Msat": "1.72e6",
            "F1": "2730",
            "F2": "3209",
            "F3": "20294",
            "Fb": "2",
        }

        # Các thông số trống dạng "" như các dòng ILx, IMx... có thể thêm nếu cần
        blank_params = [
            "ILA1", "ILB1", "ILC1", "IAB1", "IBC1", "ICA1",
            "ILA2", "ILB2", "ILC2", "IAB2", "IBC2", "ICA2",
            "ILA3", "ILB3", "ILC3", "IAB3", "IBC3", "ICA3",
            "IMA", "IMB", "IMC", "FLXA", "FLXB", "FLXC",
            "IMAB", "IMBC", "IMCA", "FLXAB", "FLXBC", "FLXCA",
            "HA1", "HB1", "HC1", "BA1", "BB1", "BC1",
            "HAB1", "HBC1", "HCA1", "BAB1", "BBC1", "BCA1"
        ]
        self.param_list(default_params, paramlist)
        self.param_list(blank_params, paramlist,val="")
        # for name, value in default_params.items():
        #     etree.SubElement(paramlist, "param", name=name, value=value)

        # for name in blank_params:
        #     etree.SubElement(paramlist, "param", name=name, value="")

        return user

    def create_pi_section_line(self,
        comp_id: int,
        x: int, y: int,
        name: str = "",
        length: float = 1,  # [m]
        Sbase: float = 100.0,
        Vbase: float = 230.0,
        freq = "Freq_ref",
        R : float = 0,  # [pu/m]
        X : float = 0,  # [pu/m]
        B : float = 0,  # [pu/m]
        R0: float = 0,  # [pu/m]
        X0: float = 0,  # [pu/m]
        B0: float = 0,  # [pu/m]
        
    ) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            defn="master:newpi",
            id=str(comp_id),
            x=str(x),
            y=str(y),
            w="116",
            h="21",
            z="0",
            orient="0",
            link="-1",
            q="4",
            disable="false"
        )
        paramlist = etree.SubElement(user, "paramlist", link="-1", name="", crc="")
        default_params = {
            "Name": name,
            "PU": "3",
            "Config": "1",
            "F": f"{freq}",
            "len": f"{length} [m]",
            "Estim": "0",
            "View": "2",
            "REst": "1.5",
            "ZEst": "1.5",
            "TEst": "1.5",
            "VR": f"{Vbase} [kV]",
            "MVA": f"{Sbase} [MVA]",
            "RPUP": " [pu/m]",
            "XLPUP": " [pu/m]",
            "XCPUP": " [pu*m]",
            "RPUZ": " [pu/m]",
            "XLPUZ": " [pu/m]",
            "XCPUZ": " [pu*m]",
            "Rp": " [ohm/m]",
            "Xp": " [ohm/m]",
            "Bp": " [Mohm*m]",
            "Rz": " [ohm/m]",
            "Xz": " [ohm/m]",
            "Bz": " [Mohm*m]",
            "RTP": " [ohm/m]",
            "TTP": " [ms]",
            "ZTP": " [ohm]",
            "RTZ": " [ohm/m]",
            "TTZ": " [ms]",
            "ZTZ": " [ohm]",
            "VR2": f"{Vbase} [kV]",
            "MVA2": f"{Sbase} [MVA]",
            "RPUP2": f"{R} [pu/m]",
            "XLPUP2": f"{X} [pu/m]",
            "BPUP2": f"{B} [pu/m]",
            "RPUZ2": f"{R0} [pu/m]",
            "XLPUZ2": f"{X0} [pu/m]",
            "BPUZ2": f"{B0} [pu/m]",
            "Rp2": "",
            "Lp": "",
            "Cp": "-",
            "Rz2": "",
            "Lz": "",
            "Cz": ""
        }

        # Thông số estimation mode (có thể sẽ cập nhật theo tính toán riêng)
        self.param_list(default_params, paramlist)
        return user

    def create_multimeter(self,
        x: int, y: int,
        s_base: float = 1.0,
        v_base: float = 1.0,
        a_base: float = 1.0,
        ts: float = 0.02,
        P: str = "",
        Q: str = "",
        V: str = "",
        I: str = "",
        Eabc: str = ""
    ) -> etree._Element:

        user = etree.Element(
            "User",
            classid="UserCmp",
            id="",
            name="master:multimeter",
            defn="master:multimeter",
            x=str(x),
            y=str(y),
            w="44",
            h="54",
            z="-1",
            orient="0",
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")
        # Các thông số đo mặc định: chưa bật đo dòng/áp/công suất
        default_params = {
            "MeasV": "1",
            "MeasI": "1",
            "MeasP": "1",
            "MeasQ": "1",
            "RMS": "2",
            "IRMS": "1",
            "MeasPh": "0",
            "S": f"{s_base}",
            "BaseV": f"{v_base}",
            "BaseA": f"{a_base}",
            "TS": f"{ts} [s]",
            "Freq": f"Freq_ref",
            "Name": "",
            "Dis": "1",
            "VolI": f"{Eabc}",
            "VolILL": "",
            "CurI": "",
            "P": f"{P}",
            "Q": f"{Q}",
            "Vrms": f"{V}",
            "Crms": f"{I}",
            "Ph": "",
            "hide1": "0",
            "hide2": "0",
            "Pd": "0.0",
            "Qd": "0.0",
            "Vd": "0.0"
        }
        self.param_list(default_params, paramlist)

        return user

    def create_ground(self,
        x: int, y: int,
        orient: str = "1"
    ) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            id="",
            name="master:ground",
            defn="master:ground",
            x=str(x),
            y=str(y),
            w="26",
            h="34",
            z="-1",
            orient=orient,
            link="-1",
            q="4",
            disable="false"
        )
        etree.SubElement(user, "paramlist", name="", link="-1", crc="")
        return user

    def create_resistor(self,
        x: int, y: int,
        R: str = "1e7",
        orient: str = "1",
        id : str ="",
        w = '33',
        h = '62'
    ) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            id=id,
            name="master:resistor",
            defn="master:resistor",
            x=str(x),
            y=str(y),
            w=w,
            h=h,
            z="-1",
            orient=orient,
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")
        etree.SubElement(paramlist, "param", name="Name", value="")
        etree.SubElement(paramlist, "param", name="R", value=f"{R}")

        return user

    def create_xfmr_2w_scaled(self,
        comp_id: int,
        x: int, y: int,
        name: str = "",
        Tmva: float = 0 ,
        f: float = 60.0,
        Vector = ["0", "1"],
        Lead: int = 1,
        X: float = 0.1,
        R: float = 0.01,
        V1: float = 0,
        V2: float = 0,
        Xair: float = 0.2,
        Xknee: float = 1.25,
        Tdc: float = 1.0,
        Txk: float = 0.1,
        Im1: float = 0.4,
        orient: str = "4",
        NLL: float = 0.0
    ) -> etree._Element:

        user = etree.Element(
            "User",
            classid="UserCmp",
            name="ETRAN:xfmr_2w_scaled",
            defn="ETRAN:xfmr_2w_scaled",
            id=str(comp_id),
            x=str(x),
            y=str(y),
            w="116",
            h="81",
            z="-1",
            orient=orient,
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", link="-1", name="", crc="")

        fixed_params = {
            "Name": name,
            "Tmva": f"{Tmva} [MVA]",
            "f": f"{f} [Hz]",
            "YD1": Vector[0],
            "YD2": Vector[1],
            "Lead": str(Lead),
            "Xl": f"{X} [pu]",
            "Ideal": "0",
            "NLL": f"{NLL} [pu]",
            "CuL": f"{R} [pu]",
            "Tap": "1",
            "View": "1",
            "Dtls": "0",
            "V1": f"{V1} [kV]",
            "V2": f"{V2} [kV]",
            "Enab": "0",
            "Sat": "1",
            "Xair": f"{Xair} [pu]",
            "Tdc": f"{Tdc} [s]",
            "Xknee": f"{Xknee} [pu]",
            "Txk": f"{Txk} [s]",
            "Im1": f"{Im1} [%]"
        }

        # Add all fixed params
        def add_param(parent, name: str, value: str):
            etree.SubElement(parent, "param", name=name, value=value)
        for k, v in fixed_params.items():
            add_param(paramlist, k, v)

        # Add empty parameters
        empty_names = [
            "ILA1", "ILB1", "ILC1", "IAB1", "IBC1", "ICA1",
            "ILA2", "ILB2", "ILC2", "IAB2", "IBC2", "ICA2",
            "IMA", "IMB", "IMC",
            "FLXA", "FLXB", "FLXC",
            "IMAB", "IMBC", "IMCA",
            "FLXAB", "FLXBC", "FLXCA"
        ]
        for name in empty_names:
            add_param(paramlist, name, "")

        return user
    
    def create_pgb_component(
        self,
        comp_id: int,
        x: int, y: int,
        name: str = "Value_1",
        orient: str = "0",
        unit:str = ''
    ) -> etree._Element:

        user = etree.Element(
            "User",
            classid="UserCmp",
            id=str(comp_id),
            name="master:pgb",
            defn="master:pgb",
            x=str(x),
            y=str(y),
            w="61",
            h="40",
            z="-1",
            orient=orient,
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")

        param_dict = {
            "Name": name,
            "Group": "",
            "UseSignalName": "1",
            "enab": "1",
            "Display": "1",
            "Scale": "1.0",
            "Units": unit,
            "mrun": "0",
            "Pol": "0",
            "Max": "2.0",
            "Min": "-2.0",
        }
        self.param_list(param_dict, paramlist)
        return user
    
    def create_datalabel(
        self,
        x: int, y: int,
        name: str = "Sig_1",
        orient: str = "6"
    ) -> etree._Element:

        user = etree.Element(
            "User",
            classid="UserCmp",
            id="",
            name="master:datalabel",
            defn="master:datalabel",
            x=str(x),
            y=str(y),
            w="36",
            h="23",
            z="-1",
            orient=orient,
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")
        etree.SubElement(paramlist, "param", name="Name", value=name)

        return user

    def create_const(
        self,
        x: int, y: int,
        value: float = 1.0,
        dim: int = 1,
        orient: str = "0"
    ) -> etree._Element:

        user = etree.Element(
            "User",
            classid="UserCmp",
            id="",
            name="master:const",
            defn="master:const",
            x=str(x),
            y=str(y),
            w="76",
            h="22",
            z="-1",
            orient=orient,
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")
        etree.SubElement(paramlist, "param", name="Name", value="")
        etree.SubElement(paramlist, "param", name="Value", value=str(value))
        etree.SubElement(paramlist, "param", name="Dim", value=str(dim))

        return user
    
    def create_graph_frame(
        self,
        frame_id: int,
        graph_id: [],
        link_id: [],
        x: int = 144, y: int = 468,
        w: int = 450, h: int = 288
    ) -> etree._Element:
        frame = etree.Element(
            "Frame",
            classid="GraphFrame",
            id=str(frame_id),
            name="frame",
            link="-1",
            x=str(x),
            y=str(y),
            w=str(w),
            h=str(h),
        )

        # First paramlist
        paramlist1 = etree.SubElement(frame, "paramlist", name="", link="-1")
        plist1 = {
            "Icon": "-1,0",
            "state": "1",
            "title": "$(GROUP) : Graphs",
            "XLabel": "sec",
            "Pan": "false",
            "pan_enable": "false",
            "pan_amount": "75",
            "markers": "false",
            "glyphs": "false",
            "ticks": "false",
            "grid": "false",
            "yinter": "false",
            "xinter": "false",
            "semilog": "false",
            "snapaperture": "false",
            "dynaperture": "true",
            "minorgrids": "false",
            "lockmarkers": "false",
            "deltareadout": "false",
            "xmarker": "0",
            "omarker": "0",
            "xfont": "Tahoma, 12world",
            "xangle": "0",
            "xtitle": "sec",
            "xgridauto": "true",
            "xgrid": "0.1"
        }

        self.param_list(plist1, paramlist1)

        # Second paramlist (xmin, xmax)
        paramlist2 = etree.SubElement(frame, "paramlist", name="", link=str(frame_id))
        etree.SubElement(paramlist2, "param", name="xmin", value="0.000000")
        etree.SubElement(paramlist2, "param", name="xmax", value="1.000000")
        ## end of format graph frame
        ##-------------------------------------------

        # Add a link to the graph if more than one graph need to be use for
        # Graph inside frame

        for i in range(len(graph_id)):
            graph = etree.SubElement(frame, "Graph", classid="OverlayGraph", id=str(graph_id[i]), link="-1")
            graph_paramlist1 = etree.SubElement(graph, "paramlist", name="", link="-1")
            graph_params = {
                "title": "",
                "units": "",
                "gridvalue": "0.1",
                "yintervalue": "0",
                "grid": "true",
                "ticks": "false",
                "glyphs": "false",
                "yinter": "true",
                "xinter": "true",
                "marker": "false",
                "trigger": "false",
                "invertcolor": "false",
                "crosshair": "false",
                "manualscale": "false",
                "autoframe": "10",
                "grid_color": "#FF95908C",
                "curve_colours": "Navy;Green;Maroon;Teal;Purple;Brown",
                "curve_colours2": "Blue;Lime;Red;Aqua;Fuchsia;Yellow"
            }

            self.param_list(graph_params, graph_paramlist1)

            # Graph second paramlist
            graph_paramlist2 = etree.SubElement(graph, "paramlist", name="", link=str(graph_id[i]))
            etree.SubElement(graph_paramlist2, "param", name="ymin", value="-2.0")
            etree.SubElement(graph_paramlist2, "param", name="ymax", value="2.0")

            # Curve inside graph

            etree.SubElement(graph, "Curve",
                classid="Curve",
                id="",
                name="Value_1",
                link=str(link_id[i]),
                color="0",
                bold="0",
                show="-1",
                mode="0",
                gradient="false",
                transparency="255",
                thresh="0.5",
                above="High",
                below="Low",
                style="0"
            ).append(etree.Element("path"))

        return frame

    def create_fixed_load(self,  x: int = 558, y: int = 504, P: float= 0,Q: float= 0,V: float= 0) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            defn="master:fixed_load",
            id="",
            x=str(x),
            y=str(y),
            w="38",
            h="54",
            z="0",
            orient="0",
            link="-1",
            q="4",
            disable="false"
        )
 
        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")

        params = {
            "PO": f"{P} [MW]",
            "QO": f"{Q} [MVAR]",
            "VBO": f"{V} [kV]",
            "NP": "2",
            "NQ": "2",
            "KPF": "0",
            "KQF": "0",
            "FR": "Freq_ref",
            "Dtls": "0",
            "R1": "",
            "L1": "",
            "C1": "",
            "Name": "",
            "VPU": "1.0",
            "PQdef": "0",
            "Parts": "1",
            "NPB": "2",
            "NPC": "2",
            "NQB": "2",
            "NQC": "2",
            "KPA": "1",
            "KPB": "0",
            "KQA": "1",
            "KQB": "0",
            "Scale": "1.0",
            "NCYC": "10"
        }
        for k, v in params.items():
            etree.SubElement(paramlist, "param", name=k, value=v)

        return user

    def create_capacitive_load(self,V, x: int = 360, y: int = 360,Q: float= 0,) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            defn="master:capacitive_load",
            id="",
            x=str(x),
            y=str(y),
            w="70",
            h="67",
            z="0",
            orient="0",
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")

        params = {
            "S": f"{Q} [MVAR]",
            "V": f"{V}",
            "F": "Freq_ref",
            "SD": "0",
            "Name": ""
        }

        self.param_list(params,paramlist)
        return user

    def create_breaker3(self,  x: int = 342, y: int = 324,name: str = "BRK") -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            defn="master:breaker3",
            id="",
            x=str(x),
            y=str(y),
            w="80",
            h="41",
            z="0",
            orient="0",
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")

        params = {
            "Ctrl": "0",
            "OPCUR": "0",
            "ENAB": "0",
            "CLVL": "0.0 [kA]",
            "View": "1",
            "ViewB": "1",
            "DisPQ": "0",
            "NAME": name,
            "NAMEA": "BRKA",
            "NAMEB": "BRKB",
            "NAMEC": "BRKC",
            "ROFF": "1.0e6 [ohm]",
            "RON": "0.005 [ohm]",
            "PRER": "0.5 [ohm]",
            "TDA": "0.0 [s]",
            "TDB": "0.0 [s]",
            "TDC": "0.0 [s]",
            "TDRA": "0.05 [s]",
            "TDRB": "0.05 [s]",
            "TDRC": "0.05 [s]",
            "PostIns": "0",
            "TDBOA": "0.005 [s]",
            "IBRA": "",
            "IBRB": "",
            "IBRC": "",
            "IBR0": "",
            "SBRA": "",
            "SBRB": "",
            "SBRC": "",
            "BP": "",
            "BQ": "",
            "Vbr": "",
            "BOpen1": "0",
            "BOpen2": "0",
            "BOpen3": "0",
            "P": "0 [MW]",
            "Q": "0 [MVAR]",
            "InitStatus": "0"
        }
        self.param_list(params,paramlist)
        return user

    def create_tbreakn(self, x: int = 342, y: int = 198, nums: int = 1,t1: float = 100,t2: float = 1.05,init: float = 0) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            defn="master:tbreakn",
            id="",
            x=str(x),
            y=str(y),
            w="78",
            h="59",
            z="0",
            orient="0",
            link="-1",
            q="4",
            disable="false"
        )
        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")

        params = {
            "NUMS": f"{nums}",
            "INIT": f"{init}",
            "TO1": f"{t1} [s]",
            "TO2": f"{t2} [s]",
            "Name": ""
        }
        self.param_list(params,paramlist)
        return user

    def create_xfmr_2w_scaled(
        self,
        user_id: int,
        x: int = 576,
        y: int = 792,
        sbase: float = 0,
        Vector = ["0", "1"],
        V1: float = 34.5,
        V2: float = 0.69,
        R: float = 0.01,
        X: float = 0.1,
        NLL: float = 0.0
    ) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            name="ETRAN:xfmr_2w_scaled",
            defn="ETRAN:xfmr_2w_scaled",
            id=str(user_id),
            x=str(x),
            y=str(y),
            w="116",
            h="81",
            z="-1",
            orient="4",
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")

        params = {
            "Name": "",
            "Tmva": f"{sbase} [MVA]",
            "f": "60.0 [Hz]",
            "YD1": Vector[0],
            "YD2": Vector[1],
            "Lead": "1",
            "Xl": f"{X} [pu]",
            "Ideal": "0",
            "NLL": f"{NLL} [pu]",
            "CuL": f"{R} [pu]",
            "Tap": "1",
            "View": "1",
            "Dtls": "0",
            "V1": f"{V1} [kV]",
            "V2": f"{V2} [kV]",
            "Enab": "0",
            "Sat": "1",
            "Xair": "0.2 [pu]",
            "Tdc": "1.0 [s]",
            "Xknee": "1.25 [pu]",
            "Txk": "0.1 [s]",
            "Im1": "0.4 [%]",
            "ILA1": "",
            "ILB1": "",
            "ILC1": "",
            "IAB1": "",
            "IBC1": "",
            "ICA1": "",
            "ILA2": "",
            "ILB2": "",
            "ILC2": "",
            "IAB2": "",
            "IBC2": "",
            "ICA2": "",
            "IMA": "",
            "IMB": "",
            "IMC": "",
            "FLXA": "",
            "FLXB": "",
            "FLXC": "",
            "IMAB": "",
            "IMBC": "",
            "IMCA": "",
            "FLXAB": "",
            "FLXBC": "",
            "FLXCA": ""
        }
        self.param_list(params, paramlist)
        return user

    def create_oltc(
        self,
        x: int = 486,
        y: int = 1044,
        name: str = "InitTap"
    ) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            name="ERCOTLibs:OLTC",
            id="",
            x=str(x),
            y=str(y),
            w="116",
            h="32",
            z="-1",
            orient="0",
            defn="ERCOTLibs:OLTC",
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")

        params = {
            "pos_step": "16",
            "neg_step": "16",
            "pos_reg": "10 [%]",
            "neg_reg": "-10 [%]",
            "v_set": "1.0 [pu]",
            "v_band": "1 [%]",
            "td": "30 [s]",
            "init_step": name,
            "enab_t": "1 [s]",
            "lock": "0"
        }
        self.param_list(params,paramlist)
        return user
    
    def create_gain(
        self,
        x: int = 1188,
        y: int = 324,
        gain_value: str = "SMVA"
    ) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            defn="master:gain",
            id="",
            x=str(x),
            y=str(y),
            w="80",
            h="36",
            z="570",
            orient="0",
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", link="-1", name="", crc="34173863")

        params = {
            "G": gain_value,
            "COM": "Gain",
            "Dim": "1",
            "Name": "",
            "DPath": "1"
        }

        self.param_list(params,paramlist)

        return user
    
    def create_sticky(
        self,
        x: int = 2538,
        y: int = 90,
        w: int = 360,
        h: int = 36,
        text: str = "Measurement"
    ) -> etree._Element:
        sticky = etree.Element(
            "Sticky",
            classid="Sticky",
            x=str(x),
            y=str(y),
            w=str(w),
            h=str(h),
            colors="10526880, 15792890",
            id=""
        )

        paramlist = etree.SubElement(sticky, "paramlist")

        params = {
            "font": "1",
            "align": "1",
            "style": "1",
            "fg_color": "0",
            "bg_color": "15793151",
            "arrows": "0",
            "full_font": "Tahoma, 9pt",
            "opacity": "25",
            "fg_color_adv": "#FF000000",
            "bg_color_adv": "#FFFFFBF0",
            "hl_color_adv": "#FFFFFF00",
            "bdr_color_adv": "#FF95918C"
        }

        self.param_list(params,paramlist)
        # Add the CDATA section
        sticky.text = etree.CDATA(text)

        return sticky
        
    def create_datatap(
        self,
        x: int,
        y: int,
        index: int = 1,
        dim: int = 1,
        type_: int = 2,
        style: int = 0,
        disp: int = 1,
        orient: int = 7,
        z: int = 520,
        w: int = 26,
        h: int = 28
    ) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            defn="master:datatap",
            id="",
            x=str(x),
            y=str(y),
            w=str(w),
            h=str(h),
            z=str(z),
            orient=str(orient),
            link="-1",
            q="4",
            disable="false",
            layer=""
        )

        paramlist = etree.SubElement(user, "paramlist", link="-1", name="", crc="")

        params = {
            "Index": str(index),
            "Dim": str(dim),
            "Type": str(type_),
            "Style": str(style),
            "Disp": str(disp),
            "Name": ""
        }

        self.param_list(params,paramlist)

        return user

    def create_pllblk(
        self,
        x: int,
        y: int,
        frated: float = 60.0,
        vrated: float = 138.0,
        kp_v: float = 250.0,
        ki_v: float = 0.001,
        kp_f: float = 10.0,
        ki_f: float = 0.001,
        tv: float = 0.0005,
        tf: float = 0.159,
        z: int = 630,
        w: int = 152,
        h: int = 119,
        orient: int = 0
    ) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            name="PLLv46:PLLBlk",
            defn="PLLv46:PLLBlk",
            id="",
            x=str(x),
            y=str(y),
            w=str(w),
            h=str(h),
            z=str(z),
            orient=str(orient),
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", link="-1", name="", crc="")

        params = {
            "PE_PLL": "",
            "Frated": str(frated),
            "Vrated": str(vrated),
            "Kp_v": str(kp_v),
            "Ki_v": str(ki_v),
            "Kp_f": str(kp_f),
            "Ki_f": str(ki_f),
            "Tv": str(tv),
            "Tf": str(tf)
        }

        self.param_list(params,paramlist)

        return user
    
    def create_inductor(
        self,
        
        x: int,
        y: int,
        user_id: str="",
        l_value: str = "0.1",
        name_val: str = "",
        z: int = -1,
        w: int = 46,
        h: int = 31,
        orient: int = 0
    ) -> etree._Element:
        user = etree.Element(
            "User",
            classid="UserCmp",
            name="master:inductor",
            defn="master:inductor",
            id=str(user_id),
            x=str(x),
            y=str(y),
            w=str(w),
            h=str(h),
            z=str(z),
            orient=str(orient),
            link="-1",
            q="4",
            disable="false"
        )

        paramlist = etree.SubElement(user, "paramlist", name="", link="-1", crc="")
        params = {
            "Name": name_val,
            "L": l_value
        }
        self.param_list(params, paramlist)

        return user
