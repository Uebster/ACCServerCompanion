# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['acc-server-tool\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('acc-server-tool/templates', 'templates'), ('acc-server-tool/static', 'static')],
    hiddenimports=[],
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
    name='ACC Server Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['acc-server-tool\\static\\ico\\ACC_Server_Companion.ico'],
)
