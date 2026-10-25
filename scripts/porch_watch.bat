@echo off
title DropSpider porch watch
cd /d "%~dp0.."
python tools\porch_watch.py %*
pause
