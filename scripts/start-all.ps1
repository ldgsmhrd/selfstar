param(
  [int]$BackendPort = 8000,
  [int]$AiPort = 8600,
  [int]$FrontendPort = 5174
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

Start-Process -FilePath 'powershell' -ArgumentList "-NoExit -Command `"& `"$PSScriptRoot/start-backend.ps1`" -Port $BackendPort`""
Start-Process -FilePath 'powershell' -ArgumentList "-NoExit -Command `"& `"$PSScriptRoot/start-ai.ps1`" -Port $AiPort`""
Start-Process -FilePath 'powershell' -ArgumentList "-NoExit -Command `"& `"$PSScriptRoot/start-frontend.ps1`" -Port $FrontendPort`""

Write-Host "Launched backend:$BackendPort, ai:$AiPort, frontend:$FrontendPort"
