#[psse35.py]    07/18/2019    Set PSSE Environment
"""
Use "import psse35" to set PSSE 35 Environment to enable PSSE run outside of PSSE GUI,
from any Python interpreter.

By default, it sets to latest minor version among installed versions of PSSE35.

To set specific minor version among installed versions of PSSE35, use it as:
    psse35.set_minor(n)    # here n is minor version number, like 0 in 35.0.x

Also get PSSE 35 Example folder Path as:
    exam_path = psse35.EXAM_PATH

Following shows its typical usage.

import psse35
psse35.set_minor(n)    # here n is minor version number, like 0 in 35.0.x
exam_path = psse35.EXAM_PATH

import psspy
psspy.psseinit()

# Below this add any PSSE function calls.

"""
from TOOLs.PSSPY39 import psseloc
import os

_FPTH, _FNAM_EXT = os.path.split(os.path.abspath( __file__ ))
_FNAM, _FEXT     = os.path.splitext(_FNAM_EXT)

_s_vrsn = _FNAM.lower().replace('psse','')

EXAM_PATH = psseloc._set_psse_loc(_s_vrsn)

msg  = "    Sets PSSE environment to latest minor version among installed versions of PSSE 35.\n"
msg += "    Use psse35.set_minor(n) to set PSSE35 minor version (n) to use.\n"
msg += "        Example, for PSSE 35.0.x, use this as: psse35.set_minor(0)"
print(msg)

def set_minor(minor):
    global EXAM_PATH
    EXAM_PATH = psseloc._set_psse_loc(_s_vrsn, _psse_mnor=minor)
