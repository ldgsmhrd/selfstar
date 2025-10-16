param(
  [string]$Url = "http://localhost:8000/api/images"
)

Write-Host "Testing POST $Url" -ForegroundColor Cyan

$payloadObj = @{
  name = "홍길동"
  gender = "여"
  feature = "테스트 프롬프트"
  options = @("v1")
  featureCombined = "테스트 프롬프트 | 얼굴형:계란형, 피부톤:밝은 17~21호"
  faceShape = "계란형"
  skinTone = "밝은 17~21호"
  hair = "스트레이트"
  eyes = "고양이상"
  nose = "오똑함"
  lips = "도톰"
  personalities = @("활발함","지적인")
}

$json = $payloadObj | ConvertTo-Json -Depth 6 -Compress

try {
  $resp = Invoke-RestMethod -Uri $Url -Method Post -ContentType 'application/json' -Body $json -TimeoutSec 120
  $ok = $false
  if ($resp -and $resp.PSObject.Properties.Name -contains 'ok') { $ok = [bool]$resp.ok }
  $hasImg = $false
  $isDataUri = $false
  $len = 0
  if ($resp -and $resp.PSObject.Properties.Name -contains 'image') {
    $hasImg = [bool]$resp.image
    if ($hasImg -and ($resp.image -is [string])) {
      $isDataUri = $resp.image.StartsWith('data:image')
      $len = $resp.image.Length
    }
  }
  $hasUrl = $resp -and ($resp.PSObject.Properties.Name -contains 'url') -and [bool]$resp.url
  $urlOut = ""
  if ($hasUrl) { $urlOut = $resp.url }
  Write-Host ("ok=$ok dataUri=$isDataUri len=$len url=$urlOut") -ForegroundColor Green
} catch {
  Write-Host ("Request failed: " + $_.Exception.Message) -ForegroundColor Red
  if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
}
