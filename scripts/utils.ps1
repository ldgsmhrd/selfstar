$ErrorActionPreference = 'Stop'

function Get-PidsOnPort {
    param([Parameter(Mandatory=$true)][int]$Port)
    $pids = @()
    try {
        # Prefer native cmdlet if available
        $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
        if ($conns) {
            $pids += ($conns | Select-Object -ExpandProperty OwningProcess)
        }
    } catch {}
    if (-not $pids -or $pids.Count -eq 0) {
        # Fallback to netstat parsing
        $pattern = ":$Port\s+.+LISTENING\s+(\d+)"
        try {
            $netstatMatches = netstat -ano | Select-String -Pattern $pattern
            foreach ($nm in $netstatMatches) {
                $pids += [int]$nm.Matches[0].Groups[1].Value
            }
        } catch {}
    }
    $pids | Sort-Object -Unique
}

function Stop-ProcessOnPort {
    param([Parameter(Mandatory=$true)][int]$Port)
    $pids = Get-PidsOnPort -Port $Port
    if (-not $pids -or $pids.Count -eq 0) {
        Write-Host "[utils] no process listening on port $Port"
        return
    }
    foreach ($pidItem in $pids) {
        try {
            Stop-Process -Id $pidItem -Force -ErrorAction Stop
            Write-Host "[utils] stopped PID $pidItem on port $Port"
        } catch {
            Write-Warning ("[utils] failed to stop PID {0} on port {1}: {2}" -f $pidItem, $Port, $_)
        }
    }
}

# Import key=value lines from a .env file into current PowerShell process environment
function Import-DotEnv {
    param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    if (-not (Test-Path $Path)) { Write-Warning "[utils] .env not found at $Path"; return }
    try {
        Get-Content -Path $Path | ForEach-Object {
            $line = $_.Trim()
            if ([string]::IsNullOrWhiteSpace($line)) { return }
            if ($line.StartsWith('#')) { return }
            # skip comments with inline text; simple split on first '='
            $idx = $line.IndexOf('=')
            if ($idx -lt 1) { return }
            $key = $line.Substring(0, $idx).Trim()
            $val = $line.Substring($idx + 1).Trim()
            # remove optional surrounding quotes
            if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Substring(1, $val.Length-2) }
            if ($val.StartsWith("'") -and $val.EndsWith("'")) { $val = $val.Substring(1, $val.Length-2) }
            if ($key) { Set-Item -Path ("Env:" + $key) -Value $val }
        }
        Write-Host "[utils] imported .env from $Path"
    } catch {
        Write-Warning "[utils] failed importing .env: $_"
    }
}
