@echo off
setlocal
cd /d "%~dp0"
title Interview Copilot

rem --- find Python -----------------------------------------------------------
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (
  echo.
  echo  Python was not found. Install Python 3.12 from https://www.python.org/downloads/
  echo  and tick "Add python.exe to PATH" during setup. Then run this file again.
  echo.
  pause
  exit /b 1
)

rem --- first run: create a private environment and install packages ---------
if not exist ".venv\Scripts\python.exe" (
  echo Setting up for the first time. This takes a minute or two...
  %PY% -m venv .venv || goto :fail
)
if not exist ".venv\installed.flag" (
  ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q || goto :fail
  echo ok> ".venv\installed.flag"
)

if not exist ".env" copy ".env.example" ".env" >nul

rem --- start the app (your browser opens automatically) ----------------------
".venv\Scripts\python.exe" -m app.server
pause
exit /b 0

:fail
echo.
echo  Setup failed. Scroll up for the error. If it mentions PyAudioWPatch,
echo  install Python 3.12 (64-bit) and delete the .venv folder, then try again.
echo.
pause
exit /b 1
