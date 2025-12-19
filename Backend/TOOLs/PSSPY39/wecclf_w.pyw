# [wecclf_w.pyw]   08/25/2020  PSLF to PSSE Power Flow and Sequence Data Conversion
# =======================================================================================================
'''This Python module is used for conveting PSLF Power Flow and Sequence Data to PSSE.
'''

# =======================================================================================================

try:
    import wecclf_gui
    wecclf_gui.main()
except:
    import comonpy
    excmsg = comonpy._GetExceptionMessage(ttl='WECCLF')
    print(excmsg)

