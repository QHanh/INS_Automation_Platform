#[psse3504.py]     10/17/2022     Set PSSE Environment
"""
Use "import psse3504" to set PSSE 35.4.x Environment to enable PSSE run outside of PSSE GUI,
from any Python interpreter.

Also get PSSE 35.4.x Example folder Path as:
    exam_path = psse3504.EXAM_PATH

Following shows its typical usage. 

import psse3504 as psse35 
exam_path = psse35.EXAM_PATH 

import psspy
psspy.psseinit()

# Below this add any PSSE function calls.

"""
import os, psseloc

_FPTH, _FNAM_EXT = os.path.split(os.path.abspath( __file__ ))
_FNAM, _FEXT     = os.path.splitext(_FNAM_EXT)

_s_vrsn = _FNAM.lower().replace('psse','')

EXAM_PATH = psseloc._set_psse_loc(_s_vrsn)


