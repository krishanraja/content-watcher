<#
.SYNOPSIS
  Brings this home computer's Content Watcher up to main, safely, in one paste.

.DESCRIPTION
  1. Finds this machine's clone from the scheduled task (or the usual folders).
  2. Pauses the task, letting a run in progress finish (up to 10 minutes; it never kills one).
  3. Pulls main fast-forward only. Local edits or a diverged branch stop it with nothing changed.
  4. Runs the repository's own installer, which reinstalls the package and re-registers the task.
  5. Proves the new code is loaded and runs the language-fix tests.
  6. Reads Hannah Fry's Short locally with yt-dlp only (free, nothing sent anywhere) and prints
     the language check and the first 300 characters of the words.
  The task is always switched back on at the end, even when a step fails.
#>
& {
  $ErrorActionPreference = "Stop"
  $TaskName = "Mindmake Content Watcher"
  $Py = "py"; $PyVer = "-3.12"
  $task = $null; $wasEnabled = $false; $ok = $false; $pulled = $false

  function Say($text, $colour = "Gray") { Write-Host $text -ForegroundColor $colour }
  function Native([scriptblock]$block) {
    # Native tools write progress to stderr; Windows PowerShell must not treat that as a failure.
    $old = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { $out = & $block 2>&1 | ForEach-Object { "$_" } } finally { $ErrorActionPreference = $old }
    return @{ code = $LASTEXITCODE; out = ($out -join "`n") }
  }

  try {
    Say "== Content Watcher update ($env:COMPUTERNAME) ==" Cyan

    # 1. Find the clone.
    $repo = $null
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
      $wasEnabled = $task.State -ne "Disabled"
      $wd = $task.Actions[0].WorkingDirectory
      if ($wd -and (Test-Path (Join-Path $wd "scripts\install-content-watch.ps1"))) { $repo = $wd }
    }
    if (-not $repo) {
      $roots = @("$HOME", "$HOME\Documents", "$HOME\Documents\GitHub", "$HOME\source\repos", "$HOME\code", "$HOME\dev", "$HOME\projects", "C:\dev", "C:\code", "C:\src")
      foreach ($root in $roots) {
        foreach ($name in @("content-watcher", "video-compression")) {
          $candidate = Join-Path $root $name
          if (Test-Path (Join-Path $candidate "scripts\install-content-watch.ps1")) { $repo = $candidate; break }
        }
        if ($repo) { break }
      }
    }
    if (-not $repo) { throw "No Content Watcher clone found. Run: git clone https://github.com/krishanraja/content-watcher.git `"$HOME\content-watcher`" and paste this again." }
    Say "ok  clone        $repo" Green

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git is not on PATH (winget install Git.Git, then open a new PowerShell)." }
    $r = Native { git -C $repo remote get-url origin }
    if ($r.code -ne 0 -or $r.out -notmatch "krishanraja/(content-watcher|video-compression)") { throw "$repo is not a clone of krishanraja/content-watcher (origin: $($r.out))." }

    # 2. Check the clone can move before touching anything.
    $r = Native { git -C $repo status --porcelain --untracked-files=no }
    if ($r.out.Trim()) { throw "The clone has local edits; nothing was changed. Edited files:`n$($r.out)" }
    $r = Native { git -C $repo fetch origin main }
    if ($r.code -ne 0) { throw "git fetch failed (network or sign-in); nothing was changed.`n$($r.out)" }
    $branch = (Native { git -C $repo rev-parse --abbrev-ref HEAD }).out.Trim()
    if ($branch -ne "main") {
      $r = Native { git -C $repo checkout main }
      if ($r.code -ne 0) { throw "Could not switch the clone from '$branch' to main; nothing was changed.`n$($r.out)" }
      Say "ok  branch       switched from $branch to main" Green
    }
    $r = Native { git -C $repo merge-base --is-ancestor HEAD origin/main }
    if ($r.code -ne 0) { throw "The clone's main has commits that are not on GitHub; nothing was changed. Show Claude: git -C `"$repo`" log origin/main..HEAD" }
    $before = (Native { git -C $repo rev-parse --short HEAD }).out.Trim()

    # 3. Pause the task, letting a run in progress finish.
    if ($task) {
      Disable-ScheduledTask -TaskName $TaskName | Out-Null
      # A disabled task reports "Disabled" even mid-run, so look for the run itself.
      function WatchRunning { [bool](Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -match "content_watcher\s+watch" }) }
      $waited = 0
      while ((WatchRunning) -and $waited -lt 600) {
        if ($waited -eq 0) { Say "..  waiting for the current watch run to finish (up to 10 minutes)" Yellow }
        Start-Sleep -Seconds 10; $waited += 10
      }
      Say "ok  task         paused" Green
    }

    # 4. Pull.
    $r = Native { git -C $repo merge --ff-only origin/main }
    if ($r.code -ne 0) { throw "git could not fast-forward to main.`n$($r.out)" }
    $after = (Native { git -C $repo rev-parse --short HEAD }).out.Trim()
    $pulled = $true
    Say "ok  code         $before -> $after" Green
    if (-not (Select-String -Path (Join-Path $repo "content_watcher\fetch\ytdlp.py") -Pattern "def pick_captions" -Quiet)) {
      throw "main does not have the language fix yet (no pick_captions). Ask Claude whether PR #26 is merged."
    }

    # 5. The repository's own installer: checks, pip install, config kept, task re-registered, doctor.
    Say "..  running the installer (a few minutes)" Yellow
    $old = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo "scripts\install-content-watch.ps1")
    $code = $LASTEXITCODE; $ErrorActionPreference = $old
    if ($code -ne 0) { throw "The installer stopped (exit $code); its MISSING lines above say what is needed." }
    $wasEnabled = $true  # the installer registers the task switched on

    # 6. Prove the new code is the one installed.
    Push-Location $repo
    try {
      $r = Native { & $Py $PyVer -c "import content_watcher, pathlib; from content_watcher.fetch import ytdlp; from content_watcher.read import language; print(pathlib.Path(content_watcher.__file__).resolve().parent.parent)" }
      if ($r.code -ne 0) { throw "Python cannot load the new code:`n$($r.out)" }
      if ((Resolve-Path $r.out.Trim().Split("`n")[-1]).Path -ne (Resolve-Path $repo).Path) { throw "Python loads Content Watcher from $($r.out), not from $repo." }
      $r = Native { & $Py $PyVer -m unittest tests.test_cw_language tests.test_cw_fetch.ParserTests }
      if ($r.code -ne 0) { throw "The language-fix tests failed on this machine:`n$($r.out)" }
      Say "ok  tests        language and fetch tests pass" Green
    } finally { Pop-Location }
    $ok = $true
  }
  catch {
    Say ""
    Say "STOPPED: $($_.Exception.Message)" Red
  }
  finally {
    if ($task -and $wasEnabled) {
      try { Enable-ScheduledTask -TaskName $TaskName | Out-Null; Say "ok  task         on" Green } catch { Say "Could not switch the task back on: open Task Scheduler and enable '$TaskName'." Red }
    }
  }

  if (-not $ok) {
    if ($pulled) { Say "The code moved to main but the install did not finish. Fix what STOPPED says, then paste this again." Yellow }
    else { Say "Nothing was changed; the watcher runs the code it had before this paste." Yellow }
    return
  }

  # 7. Live check: yt-dlp only, never a paid step, nothing reported or filed.
  Say ""
  Say "..  live check: reading Hannah Fry's Short on this machine (yt-dlp only, free, about 3 minutes)" Yellow
  $tmp = Join-Path $env:TEMP ("cw-check-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
  New-Item -ItemType Directory -Path $tmp | Out-Null
  $probe = @'
import json, sys, pathlib
from content_watcher.fetch import ytdlp
from content_watcher.read.reader import read_video
folder = pathlib.Path(sys.argv[1])
post = ytdlp.fetch("https://www.youtube.com/shorts/wh3D5Zx6Prg", "youtube", folder, captions="youtube")
reading = read_video(post.media[0], post=post, captions=post.captions_file, workdir=folder / "work")
data = reading.read
print("captions file :", post.captions_file.name if post.captions_file else None)
print("language check:", json.dumps({k: v for k, v in data["words"].get("language_check", {}).items() if k != "withheld"}))
print("heard         :", data["heard"], data.get("heard_class"))
print("first 300     :", data["words_text"][:300])
'@
  Push-Location $repo
  try {
    $old = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $env:PYTHONIOENCODING = "utf-8"  # the words may be in any script; the console must not crash printing them
    $probe | & $Py $PyVer - $tmp
    if ($LASTEXITCODE -ne 0) { Say "The live check could not read the Short here (the update itself is done)." Yellow }
    $ErrorActionPreference = $old
  } finally { Pop-Location; Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue }
  Say "Done. Updated to $after." Green
}
