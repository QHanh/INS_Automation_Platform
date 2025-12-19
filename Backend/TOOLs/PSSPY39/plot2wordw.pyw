#[plot2wordw.pyw]  04/04/2022    Create/Update Word Document by inserting Plot/Picture Files
# ====================================================================================================
'''This Python module is used to Create/Update Word Document by inserting Plot/Picture Files.
'''

import sys, os

pyvrsn = sys.version_info[0]*10 + sys.version_info[1]

if pyvrsn>=38:
    dir_psspyXX = os.path.dirname(__file__)
    dir2, junk = os.path.split(dir_psspyXX)
    dir_pssbin = os.path.join(dir2, 'PSSBIN')
    for pth in [dir_psspyXX, dir_pssbin]:
        os.add_dll_directory(pth)

try:
    import plot2word
    plot2word.main()
except:
    import comonpy
    excmsg = comonpy._GetExceptionMessage(ttl='Plot2Word')
    print(excmsg)

