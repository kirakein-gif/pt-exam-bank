@echo off
setlocal
cd /d "%~dp0"

echo.
echo [1/4] Python package install...
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)

%PY% --version
if errorlevel 1 (
  echo.
  echo Python not found.
  echo Install Python 3.11 or 3.12 first: https://www.python.org/downloads/
  pause
  exit /b 1
)

%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo Python package installation failed.
  pause
  exit /b 1
)

echo.
echo [2/4] Tesseract OCR check...
set "TESS=C:\Program Files\Tesseract-OCR\tesseract.exe"
if exist "%TESS%" goto tess_ok

where tesseract >nul 2>nul
if %errorlevel%==0 goto tess_ok

where winget >nul 2>nul
if %errorlevel% neq 0 (
  echo Tesseract is not installed and winget is unavailable.
  echo Install Tesseract OCR manually, then run this file again.
  echo Recommended Windows build: UB-Mannheim Tesseract OCR
  pause
  exit /b 1
)

echo Installing Tesseract OCR...
winget install --id UB-Mannheim.TesseractOCR -e --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
  echo Tesseract installation failed.
  pause
  exit /b 1
)

:tess_ok
echo.
echo [3/4] Korean OCR data...
if not exist "tessdata" mkdir "tessdata"

if not exist "tessdata\kor.traineddata" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/kor.traineddata' -OutFile '%CD%\tessdata\kor.traineddata'"
)
if not exist "tessdata\eng.traineddata" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/eng.traineddata' -OutFile '%CD%\tessdata\eng.traineddata'"
)

if not exist "tessdata\kor.traineddata" (
  echo Korean OCR data download failed.
  pause
  exit /b 1
)
if not exist "tessdata\eng.traineddata" (
  echo English OCR data download failed.
  pause
  exit /b 1
)

echo.
echo [4/4] Done.
echo Run 'run_bank_builder.bat'.
pause