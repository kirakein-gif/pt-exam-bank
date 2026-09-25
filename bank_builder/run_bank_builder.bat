@echo off
setlocal
cd /d "%~dp0"
set "TESSDATA_PREFIX=%~dp0tessdata"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 bank_builder.py
) else (
  python bank_builder.py
)

if errorlevel 1 (
  echo.
  echo Program ended with an error.
  pause
)