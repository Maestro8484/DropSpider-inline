# Regenerate every STL and every image. Run from anywhere in PowerShell.
# Requires: pip install -r tools\requirements.txt
$ErrorActionPreference = "Stop"
Push-Location "$PSScriptRoot\..\cad"
try { python generate.py; python render.py } finally { Pop-Location }
Push-Location "$PSScriptRoot\..\docs"
try { python diagrams.py } finally { Pop-Location }
