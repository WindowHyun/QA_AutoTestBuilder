# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui\\app_minimal.py'],
    pathex=[],
    binaries=[],
    datas=[('core', 'core'), ('gui', 'gui'), ('utils', 'utils'), ('config.py', '.')],
    hiddenimports=['pandas', 'openpyxl', 'cryptography', 'cryptography.fernet', 'selenium', 'selenium.webdriver', 'selenium.webdriver.common.keys', 'selenium.webdriver.common.by', 'selenium.webdriver.chrome.service', 'selenium.webdriver.chrome.options', 'selenium.webdriver.firefox.service', 'selenium.webdriver.firefox.options', 'selenium.webdriver.edge.service', 'selenium.webdriver.edge.options', 'webdriver_manager', 'webdriver_manager.chrome', 'webdriver_manager.firefox', 'webdriver_manager.microsoft', 'packaging', 'requests', 'pytest'],
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
    name='AutoTestBuilder',
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
