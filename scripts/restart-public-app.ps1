# Restart the public Link Check Flask app (default port 5055).
# Use after template, CSS, or package changes so the browser is not served stale UI.
param(
    [int]$Port = 5055,
    [switch]$SkipInstall,
    [switch]$Background
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

function Get-ListenersOnPort {
    param([int]$ListenPort)
    $pids = @()
    $lines = netstat -ano | Select-String ":$ListenPort\s+.*LISTENING"
    foreach ($line in $lines) {
        $parts = ($line.ToString().Trim() -split '\s+')
        $procId = $parts[-1]
        if ($procId -match '^\d+$' -and $procId -ne '0') {
            $pids += [int]$procId
        }
    }
    return $pids | Select-Object -Unique
}

$listenerPids = Get-ListenersOnPort -ListenPort $Port
if ($listenerPids.Count -gt 0) {
    Write-Host "Stopping $($listenerPids.Count) process(es) on port $Port ..."
    foreach ($procId in $listenerPids) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

if (-not $SkipInstall) {
    Write-Host "Reinstalling editable package (public + dev extras) ..."
    python -m pip install -e ".[public,dev]"
}

$env:LINK_CHECK_PORT = "$Port"
$env:PORT = "$Port"

if ($Background) {
  $log = Join-Path $repoRoot ".local-server.log"
  $errLog = Join-Path $repoRoot ".local-server.err.log"
  Start-Process -FilePath "python" -ArgumentList "public_app/app.py" -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $log -RedirectStandardError $errLog -WindowStyle Hidden
  Write-Host "Started in background. Logs: $log"
  Write-Host "Open http://127.0.0.1:$Port (hard refresh: Ctrl+Shift+R)"
  exit 0
}

Write-Host "Starting http://127.0.0.1:$Port (Ctrl+C to stop) ..."
python public_app/app.py