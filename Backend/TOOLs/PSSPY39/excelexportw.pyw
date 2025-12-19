#[excelexportw.pyw]  03/03/2021    Export PSS(R)E Data/Results to Excel
import sys, os

pyvrsn = sys.version_info[0]*10 + sys.version_info[1]

if pyvrsn>=38:
    dir_psspyXX = os.path.dirname(__file__)
    dir2, junk = os.path.split(dir_psspyXX)
    dir_pssbin = os.path.join(dir2, 'PSSBIN')
    for pth in [dir_psspyXX, dir_pssbin]:
        os.add_dll_directory(pth)

try:
    import excelexport
    excelexport.run_as_mainloop()
except:
    import comonpy
    excmsg = comonpy._GetExceptionMessage(ttl='ExcelExport')
    print(excmsg)
