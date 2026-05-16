@echo off
title ILPA Processor
color 0A
cd /d "%~dp0"

echo.
echo  +------------------------------------------+
echo  ^|        ILPA Processor                    ^|
echo  ^|        Albourne Partners                 ^|
echo  +------------------------------------------+
echo.

:: ── Paths ────────────────────────────────────────────────────
set RUNTIME=%~dp0runtime
set PYTHON=%RUNTIME%\python\python.exe
set PTH=%RUNTIME%\python\python311._pth

:: ── If already set up, skip straight to launch ───────────────
if exist "%PYTHON%" goto :launch

:: ════════════════════════════════════════════════════════════
::  FIRST-TIME SETUP  (runs once, never again)
:: ════════════════════════════════════════════════════════════
echo  First-time setup -- takes 3-5 minutes.
echo  This will NOT happen again after today.
echo.

mkdir "%RUNTIME%" 2>nul
mkdir "%RUNTIME%\python" 2>nul

:: ── Download portable Python ─────────────────────────────────
echo  [1/4]  Downloading portable Python 3.11...

:: Try PowerShell first (Windows 10+)
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%RUNTIME%\py.zip'" 2>nul
if exist "%RUNTIME%\py.zip" goto :extract

:: Fallback: curl (also built into Windows 10+)
curl -L -o "%RUNTIME%\py.zip" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip" 2>nul
if exist "%RUNTIME%\py.zip" goto :extract

:: Fallback: bitsadmin (older Windows)
bitsadmin /transfer pydownload /download /priority normal "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip" "%RUNTIME%\py.zip" 2>nul
if exist "%RUNTIME%\py.zip" goto :extract

echo.
echo  ERROR: Could not download Python.
echo  Check your internet connection and try again.
echo.
pause
exit /b

:extract
:: ── Extract Python ────────────────────────────────────────────
echo  [2/4]  Extracting Python...
powershell -Command "Expand-Archive -Path '%RUNTIME%\py.zip' -DestinationPath '%RUNTIME%\python' -Force"
del "%RUNTIME%\py.zip"

:: ── Enable pip in embedded Python ────────────────────────────
echo  [3/4]  Enabling package manager...
powershell -Command "(Get-Content '%PTH%') -replace '#import site','import site' | Set-Content '%PTH%'"

:: Download get-pip.py
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%RUNTIME%\get-pip.py'" 2>nul
if not exist "%RUNTIME%\get-pip.py" (
  curl -L -o "%RUNTIME%\get-pip.py" "https://bootstrap.pypa.io/get-pip.py" 2>nul
)

"%PYTHON%" "%RUNTIME%\get-pip.py" --quiet
del "%RUNTIME%\get-pip.py" 2>nul

:: ── Install packages ─────────────────────────────────────────
echo  [4/4]  Installing packages (streamlit, pdfplumber, openpyxl)...
echo         This is the longest step -- please wait...
"%PYTHON%" -m pip install streamlit pdfplumber openpyxl pandas --quiet --disable-pip-version-check

echo.
echo  ✓  Setup complete! Launching now...
echo.

:: ════════════════════════════════════════════════════════════
::  LAUNCH
:: ════════════════════════════════════════════════════════════
:launch
echo  ✓  Python ready  ^(bundled, no system install needed^)
echo.
echo  →  Opening at http://localhost:8501
echo  →  Keep this window open while using the app
echo  →  Press Ctrl+C to stop
echo.

:: Open browser after 5 second delay
start "" cmd /c "timeout /t 5 /nobreak >nul & start http://localhost:8501"

:: Run app using bundled Python
"%PYTHON%" -m streamlit run "%~dp0app.py" ^
  --server.port 8501 ^
  --browser.gatherUsageStats false

echo.
echo  App stopped. Press any key to close.
pause >nul
