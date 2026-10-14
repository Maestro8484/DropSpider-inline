@echo off
rem DropSpider repo health check. Double-click to run.
rem Says PASS or FAIL for each thing a stranger needs to clone and build this repo:
rem passwords kept out, a license, every doc on the README map, handoffs on the roadmap,
rem no dead links, every named STL present, the firmware version stamp, and (option 2) a full build.
setlocal
cd /d "%~dp0.."
title DropSpider repo check

set "PY=%USERPROFILE%\.platformio\penv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

set "WAY=%~1"
if "%WAY%"=="" (
  echo.
  echo   DropSpider repo check
  echo.
  echo   1  Docs and files only. A few seconds.
  echo   2  Docs and files, then a full firmware build. About a minute.
  echo.
  set /p "PICK=Type 1 or 2 and press Enter: "
)
if "%WAY%"=="" if "%PICK%"=="2" set "WAY=--build"
if /i "%WAY%"=="build" set "WAY=--build"
if not "%WAY%"=="--build" set "WAY="

"%PY%" tools\check_repo.py %WAY%
set "RC=%errorlevel%"
echo.
if "%~1"=="" pause
exit /b %RC%
