# Regenerate every STL and every image. Run from the repo root in PowerShell.
# Requires: pip install trimesh manifold3d shapely numpy matplotlib
$ErrorActionPreference = "Stop"
Push-Location "$PSScriptRoot\..\cad"
try { python generate.py; python render.py } finally { Pop-Location }
Push-Location "$PSScriptRoot\..\docs"
try { python diagrams.py } finally { Pop-Location }
