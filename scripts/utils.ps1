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
