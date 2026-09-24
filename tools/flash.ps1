# Build, flash over USB, and open the serial console. Run from anywhere in PowerShell.
# Requires PlatformIO (VS Code extension, or: pip install platformio) and secrets.ini at the repo root.
#   tools\flash.ps1              USB, port from platformio.ini (COM13)
#   tools\flash.ps1 -Port COM5   USB, other port
#   tools\flash.ps1 -Ota         over the network to dropspider.local
param([string]$Port = "", [switch]$Ota)
$ErrorActionPreference = "Stop"
Push-Location "$PSScriptRoot\.."
try {
    if (-not (Test-Path "secrets.ini")) { throw "secrets.ini is missing. Copy secrets.ini.example to secrets.ini and fill it in." }
    if ($Ota) {
        pio run -e ota -t upload
    } elseif ($Port) {
        pio run -e nodemcu-32s -t upload --upload-port $Port
        pio device monitor -b 115200 -p $Port
    } else {
        pio run -e nodemcu-32s -t upload
        pio device monitor -e nodemcu-32s
    }
} finally { Pop-Location }
