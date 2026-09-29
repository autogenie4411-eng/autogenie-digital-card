@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py"
if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
  echo Python is not installed.
  echo Install Python from https://www.python.org/
  echo Check "Add Python to PATH" during installation.
  pause
  exit /b 1
)

%PY_CMD% -c "import PIL" >nul 2>nul
if errorlevel 1 (
  echo Installing Pillow...
  %PY_CMD% -m pip install pillow
)

echo.
echo Generating employee pages and OG images...
%PY_CMD% generate.py

echo.
echo Done. Check cards, og, and the employee link text file.
pause
endlocal
