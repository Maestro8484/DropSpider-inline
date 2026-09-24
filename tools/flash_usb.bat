@echo off
rem Build and load the firmware over the USB cable (port set in platformio.ini), then show the console.
rem Double-click to run. Close the window to stop the console.
cd /d "%~dp0.."
if not exist secrets.ini (
  echo secrets.ini is missing. Copy secrets.ini.example to secrets.ini and fill it in.
  pause
  exit /b 1
)
set PIO=%USERPROFILE%\.platformio\penv\Scripts\pio.exe
if not exist "%PIO%" set PIO=pio
"%PIO%" run -e nodemcu-32s -t upload || (echo. & echo Upload failed. If it stopped at Connecting: hold BOOT, tap EN, let go of BOOT, run this again. & pause & exit /b 1)
"%PIO%" device monitor -e nodemcu-32s
