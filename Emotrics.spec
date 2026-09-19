# -*- mode: python ; coding: utf-8 -*-
import site
from PyInstaller.utils.hooks import collect_dynamic_libs

opencv_binaries = collect_dynamic_libs('cv2')

a = Analysis(
    ['Emotrics.py'],
    pathex=[],
    binaries=opencv_binaries,
    datas=[('include', 'include')],
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
	icon='include/icon_color/meei_3WR_icon.ico',
    name='Emotrics',
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
)
