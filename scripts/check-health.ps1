$ErrorActionPreference = 'Stop'
param(
  [string]$BackendUrl = 'http://localhost:8000/health'
  ,
  [string]$AiUrl = 'http://localhost:8600/health'
)
Write-Host "[check] backend => $BackendUrl"
try {
  $b = Invoke-RestMethod -Uri $BackendUrl -Method GET -TimeoutSec 5
  Write-Host "[check] backend ok: $($b | ConvertTo-Json -Compress)"
} catch {
  Write-Warning "[check] backend failed: $_"
}
Write-Host "[check] ai => $AiUrl"
try {
  $a = Invoke-RestMethod -Uri $AiUrl -Method GET -TimeoutSec 5
  Write-Host "[check] ai ok: $($a | ConvertTo-Json -Compress)"
} catch {
  Write-Warning "[check] ai failed: $_"
}