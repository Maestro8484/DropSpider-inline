@echo off
rem Build and load the firmware over the home network to dropspider.local.
rem Double-click to run. The board switches its motor and servo off, updates, and restarts.
cd /d "%~dp0.."
if not exist secrets.ini (
  echo secrets.ini is missing. Copy secrets.ini.example to secrets.ini and fill it in.
  pause
  exit /b 1
)
set PIO=%USERPROFILE%\.platformio\penv\Scripts\pio.exe
if not exist "%PIO%" set PIO=pio
"%PIO%" run -e ota -t upload
pause
