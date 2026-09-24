# Build, flash, and open the serial console. Run from the repo root in PowerShell.
# Requires: pip install platformio
param([string]$Port = "")
$ErrorActionPreference = "Stop"
Push-Location "$PSScriptRoot\..\firmware"
try {
    if ($Port) { pio run -t upload --upload-port $Port } else { pio run -t upload }
    if ($Port) { pio device monitor -b 115200 -p $Port } else { pio device monitor -b 115200 }
} finally { Pop-Location }
