@echo off
rem DropSpider firmware update. Double-click to run.
rem Builds the firmware from this repo, then loads it onto the board by WiFi or by USB.
rem Can also be run with an argument: update_firmware.bat wifi   or   update_firmware.bat usb
setlocal
cd /d "%~dp0.."
title DropSpider firmware update

if not exist secrets.ini (
  echo secrets.ini is missing. Copy secrets.ini.example to secrets.ini and fill it in.
  goto :fail
)

set "PIO=%USERPROFILE%\.platformio\penv\Scripts\pio.exe"
if not exist "%PIO%" set "PIO=pio"
set "PY=%USERPROFILE%\.platformio\penv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
set "PORT=COM13"

set "WAY=%~1"
if "%WAY%"=="" (
  echo.
  echo   DropSpider firmware update
  echo.
  echo   1  WiFi  - board on the network at dropspider.local. No buttons. About 90 seconds.
  echo   2  USB   - board plugged into %PORT%. Buttons only if it asks.
  echo.
  set /p "PICK=Type 1 or 2 and press Enter: "
)
if "%WAY%"=="" if "%PICK%"=="1" set "WAY=wifi"
if "%WAY%"=="" if "%PICK%"=="2" set "WAY=usb"
if /i "%WAY%"=="wifi" goto :wifi
if /i "%WAY%"=="usb" goto :usb
echo Nothing chosen.
goto :fail

:wifi
echo.
echo Building and sending over WiFi. The motor and servo switch off first.
echo When it restarts the finger servo moves to its lock angle: keep hands clear.
echo.
rem A WiFi upload sometimes drops on the first try, so it gets three.
set /a TRY=1
:wifi_try
"%PIO%" run -e ota -t upload
if not errorlevel 1 goto :ok
if %TRY% geq 3 (
  echo.
  echo WiFi update FAILED three times. Check the board is powered and on the network: open http://dropspider.local
  goto :fail
)
set /a TRY+=1
echo.
echo That try did not go through. Trying again in 10 seconds, try %TRY% of 3...
timeout /t 10 /nobreak >nul
goto :wifi_try

:usb
echo.
echo Building and loading over USB. Most boards go into flash mode by themselves.
echo When it restarts the finger servo moves to its lock angle: keep hands clear.
echo.
"%PIO%" run -e nodemcu-32s -t upload
if not errorlevel 1 goto :ok
echo.
echo The board did not go into flash mode by itself. Do it by hand instead,
echo with the USB cable plugged in:
echo   1. press and hold BOOT (marked IO0 on some boards)
echo   2. press and let go of EN
echo   3. let go of BOOT
echo When it restarts the finger servo moves to its lock angle: keep hands clear.
echo.
pause
set "B=.pio\build\nodemcu-32s"
set "A0=%USERPROFILE%\.platformio\packages\framework-arduinoespressif32\tools\partitions\boot_app0.bin"
"%PY%" tools\esptool_noreset.py --chip esp32 --port %PORT% --baud 460800 --before no_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "%B%\bootloader.bin" 0x8000 "%B%\partitions.bin" 0xe000 "%A0%" 0x10000 "%B%\firmware.bin"
if errorlevel 1 (
  echo.
  echo USB update FAILED. Do the BOOT and EN buttons again and rerun this.
  goto :fail
)
goto :ok

:ok
echo.
echo Update done. The board restarts and is back on the network in about 30 seconds.
if "%~1"=="" pause
exit /b 0

:fail
if "%~1"=="" pause
exit /b 1
