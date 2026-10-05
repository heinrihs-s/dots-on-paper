param([switch]$Init, [switch]$Doctor, [switch]$Offline, [switch]$Mcp, [switch]$Update, [switch]$NoBrowser, [string]$Python, [string]$DataDir)
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
if ($Update) {
    & $taskPython (Join-Path $PSScriptRoot 'tools\setup.py')
    if ($LASTEXITCODE -ne 0) { throw 'Update failed. Existing state and keys are retained.' }
    return
}
if (-not $DataDir) { $DataDir = Join-Path $PSScriptRoot 'data' }
$taskPreviousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = $null
    if ($Doctor) {
        $taskArguments = @((Join-Path $PSScriptRoot 'tools\doctor.py'))
        if ($Offline) { $taskArguments += '--offline' }
        if ($Mcp) { $taskArguments += '--mcp' }
        if ($DataDir) { $taskArguments += @('--config', (Join-Path $DataDir 'credentials.json')) }
        & $taskPython @taskArguments
    }
    else {
        $taskArguments = @('-m', 'dots_on_paper')
        if ($Init) { $taskArguments += '--init' }
        elseif (-not $NoBrowser) { $taskArguments += '--open' }
        if ($DataDir) { $taskArguments += @('--data-dir', $DataDir) }
        & $taskPython @taskArguments
    }
    if ($LASTEXITCODE -ne 0) { throw "Dots on Paper exited with code $LASTEXITCODE" }
}
finally { $env:PYTHONPATH = $taskPreviousPythonPath }
