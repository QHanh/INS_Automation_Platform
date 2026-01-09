# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server.py'],
    pathex=['.', 'TOOLs'],
    binaries=[],
    datas=[('templates', 'templates'), ('app/services/build_model_libs', 'app/services/build_model_libs'), ('TOOLs', 'TOOLs')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off', 'PSSE_Model', 'PSSE_Model_Detail', 'PSCAD_Model', 'Data', 'component', 'TOOLs.mhi', 'TOOLs.mhi.pscad'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
