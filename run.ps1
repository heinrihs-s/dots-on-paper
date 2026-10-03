param([switch]$Init, [switch]$Doctor, [switch]$Offline, [string]$Python, [string]$DataDir)
$ErrorActionPreference = 'Stop'
$taskRuntime = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$taskVenvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$taskActivePython = if ($env:VIRTUAL_ENV) { Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe' } else { $null }
$taskPathPython = Get-Command python -ErrorAction SilentlyContinue
$taskPython = if ($Python) { $Python }
    elseif (Test-Path -LiteralPath $taskVenvPython) { $taskVenvPython }
    elseif ($taskActivePython -and (Test-Path -LiteralPath $taskActivePython)) { $taskActivePython }
    elseif ($taskPathPython) { $taskPathPython.Source }
    elseif (Test-Path -LiteralPath $taskRuntime) { $taskRuntime }
    else { throw 'Install Python 3.11+ and run python tools/setup.py first.' }
if ($Init -and $Doctor) { throw 'Choose either -Init or -Doctor.' }
if ($Offline -and -not $Doctor) { throw '-Offline is used with -Doctor.' }
$taskPreviousPythonPath = $env:PYTHONPATH
try {
    $taskSource = Join-Path $PSScriptRoot 'src'
    $env:PYTHONPATH = if ($taskPreviousPythonPath) { $taskSource + [IO.Path]::PathSeparator + $taskPreviousPythonPath } else { $taskSource }
    if ($Doctor) {
        $taskArguments = @((Join-Path $PSScriptRoot 'tools\doctor.py'))
        if ($Offline) { $taskArguments += '--offline' }
        if ($DataDir) { $taskArguments += @('--config', (Join-Path $DataDir 'credentials.json')) }
        & $taskPython @taskArguments
    }
    else {
        $taskArguments = @('-m', 'dots_on_paper')
        if ($Init) { $taskArguments += '--init' }
        if ($DataDir) { $taskArguments += @('--data-dir', $DataDir) }
        & $taskPython @taskArguments
    }
    if ($LASTEXITCODE -ne 0) { throw "Dots on Paper exited with code $LASTEXITCODE" }
}
finally { $env:PYTHONPATH = $taskPreviousPythonPath }
