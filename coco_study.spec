# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path.cwd()
icon_path = str(project_root / "assets" / "cocoai_app_icon.icns")

datas = [
    (str(project_root / "assets"), "assets"),
    (str(project_root / "app.py"), "."),
    (str(project_root / "app"), "app"),
]

a = Analysis(
    ["desktop_app.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "streamlit.web.cli",
        "streamlit.runtime.scriptrunner",
        "webview.platforms.cocoa",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CocoAIStudy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_path,
)
app = BUNDLE(
    exe,
    name="CocoAIStudy.app",
    icon=icon_path,
    bundle_identifier="com.cocoai.study",
)
