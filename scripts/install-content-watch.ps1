<#
.SYNOPSIS
  Installs the Content Watcher scheduled task on this Windows home computer.

.DESCRIPTION
  Checks everything first and installs nothing if a required piece is missing, saying which.
  Then installs the Python package with its watch extras and registers a scheduled task that runs
  `content-watch watch --once` every minute. Both home computers may run it; the engine's claim decides
  who does each request. The task's log stays on this machine and carries counts and classes only.

  Run from the repository folder in PowerShell:
    powershell -ExecutionPolicy Bypass -File scripts\install-content-watch.ps1
  To see what it would do without installing:
    powershell -ExecutionPolicy Bypass -File scripts\install-content-watch.ps1 -CheckOnly
#>
param(
  [switch]$CheckOnly,
  [string]$Python = "py",
  [string]$PythonVersion = "-3.12",
  [string]$TaskName = "Mindmake Content Watcher"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$missing = @()

function Check($name, $ok, $detail) {
  if ($ok) { Write-Host ("ok       {0,-22} {1}" -f $name, $detail) }
  else { Write-Host ("MISSING  {0,-22} {1}" -f $name, $detail); $script:missing += $name }
}

# 1. Python (pinned through the py launcher, as content-engine pins it).
$pyOk = $false
try { $pyVer = & $Python $PythonVersion -c "import sys; print(sys.version.split()[0])" 2>$null; $pyOk = $LASTEXITCODE -eq 0 } catch {}
Check "python" $pyOk ($(if ($pyOk) { $pyVer } else { "install Python 3.12 (winget install Python.Python.3.12)" }))

# 2. FFmpeg.
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
Check "ffmpeg" ([bool]$ffmpeg) ($(if ($ffmpeg) { $ffmpeg.Source } else { "winget install Gyan.FFmpeg, then open a new terminal" }))

# 3. The engine key in Windows Credential Manager (never printed).
$null = cmdkey /list:Mindmake/engine-operator-token 2>$null
$keyOk = ($LASTEXITCODE -eq 0) -and ((cmdkey /list:Mindmake/engine-operator-token) -match "Mindmake/engine-operator-token")
Check "engine key" $keyOk ($(if ($keyOk) { "present" } else { "store it as the generic credential Mindmake/engine-operator-token" }))

# 4. Optional pieces: named, never blocking.
$tess = Get-Command tesseract -ErrorAction SilentlyContinue
if (-not $tess) { Write-Host "no       tesseract              words on screen will not be read (winget install UB-Mannheim.TesseractOCR)" }
$deno = Get-Command deno -ErrorAction SilentlyContinue
if (-not $deno) { Write-Host "no       deno                   YouTube may refuse downloads (winget install DenoLand.Deno)" }

if ($missing.Count -gt 0) {
  Write-Host ""
  Write-Host ("Not installed. Missing: {0}." -f ($missing -join ", "))
  exit 1
}
if ($CheckOnly) { Write-Host ""; Write-Host "Everything required is here. Run again without -CheckOnly to install."; exit 0 }

# 5. Install the package and its watch extras.
& $Python $PythonVersion -m pip install --upgrade --quiet -e "$repo[watch]"
if ($LASTEXITCODE -ne 0) { Write-Host "pip install failed; nothing was registered."; exit 1 }

# 6. Register the scheduled task: every minute, hidden, whether or not anyone is signed in to the desktop session.
$pythonw = & $Python $PythonVersion -c "import sys, pathlib; p = pathlib.Path(sys.executable); print(p.with_name('pythonw.exe') if p.with_name('pythonw.exe').exists() else p)"
$action = New-ScheduledTaskAction -Execute $pythonw -Argument "-m content_watcher watch --once" -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Reads every link Krish pastes and every file he drops into text, on this machine." -Force | Out-Null

# 7. Readback.
$task = Get-ScheduledTask -TaskName $TaskName
Write-Host ""
Write-Host ("Scheduled task '{0}': {1}" -f $TaskName, $task.State)
& $Python $PythonVersion -m content_watcher doctor
Write-Host ""
Write-Host ("Log (counts and classes only): {0}\content-watcher\watch.log" -f $env:LOCALAPPDATA)
