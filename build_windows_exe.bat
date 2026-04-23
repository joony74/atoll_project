@echo off
setlocal

cd /d %~dp0

if not exist venv\Scripts\python.exe (
  echo Python virtual environment not found at venv\Scripts\python.exe
  exit /b 1
)

if not exist venv\Scripts\pyinstaller.exe (
  echo Installing PyInstaller and pywebview...
  venv\Scripts\pip.exe install pyinstaller pywebview
)

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

venv\Scripts\pyinstaller.exe --noconfirm --windowed --name CocoAIStudy ^
  --icon assets\cocoai_app_icon.png ^
  --add-data "assets;assets" ^
  --add-data "app;app" ^
  --add-data "app.py;." ^
  --hidden-import streamlit.web.cli ^
  --hidden-import streamlit.runtime.scriptrunner ^
  --hidden-import webview.platforms.edgechromium ^
  desktop_app.py

echo.
echo Build complete:
echo   dist\CocoAIStudy\CocoAIStudy.exe
