# [createusrdllw.pyw]   04/04/2022  PSS(R)E User Model Compile/Link and Environment Manager Python Module
# =======================================================================================================

import sys, os

pyvrsn = sys.version_info[0]*10 + sys.version_info[1]

if pyvrsn>=38:
    dir_psspyXX = os.path.dirname(__file__)
    dir2, junk = os.path.split(dir_psspyXX)
    dir_pssbin = os.path.join(dir2, 'PSSBIN')
    for pth in [dir_psspyXX, dir_pssbin]:
        os.add_dll_directory(pth)

import psse_env_manager_gui
psse_env_manager_gui.run_as_mainloop()
