param(
  [int]$Port = 5174
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$frontDir = Join-Path $repoRoot 'frontend'
$nodeModules = Join-Path $frontDir 'node_modules'
.$PSScriptRoot/utils.ps1

function Assert-Port-Free {
  param([int]$Port)
  $pids = Get-PidsOnPort -Port $Port
  if ($pids -and $pids.Count -gt 0) {
    throw "[frontend] port $Port is already in use by PIDs: $($pids -join ', ')"
  }
}

Write-Host "[frontend] working dir: $frontDir"
Push-Location $frontDir
try {
  if (!(Test-Path $nodeModules)) {
    Write-Host '[frontend] installing dependencies'
    npm install
  } else {
    Write-Host '[frontend] using existing node_modules'
  }
  Assert-Port-Free -Port $Port
  Write-Host "[frontend] starting vite on port $Port (strict)"
  npm run dev -- --port $Port
}
finally {
  Pop-Location
}
