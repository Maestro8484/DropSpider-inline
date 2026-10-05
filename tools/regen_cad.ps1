# The FULL rebuild: every STL (only the ones whose geometry changed are rewritten) and every image. The owner runs this;
# a session changing one part runs  python generate.py --export <part>  instead (cad\README.md).
# Requires: pip install -r tools\requirements.txt
$ErrorActionPreference = "Stop"
Push-Location "$PSScriptRoot\..\cad"
try { python generate.py --export-all; python render.py } finally { Pop-Location }
Push-Location "$PSScriptRoot\..\docs"
try { python diagrams.py } finally { Pop-Location }
