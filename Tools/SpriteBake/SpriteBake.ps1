param(
    [Parameter(Mandatory=$true)][ValidateSet('inspect','validate','bake','preview','metadata','sync-definitions','export','verify-export')][string]$Command,
    [Parameter(Mandatory=$true)][string]$Project,
    [Parameter(Mandatory=$true)][string]$Style,
    [string[]]$Blocks = @(),
    [ValidateSet('128','256','all')][string]$Quality = 'all',
    [string]$BlenderPath,
    [string]$PythonPath,
    [string]$GameRoot,
    [string]$BackupRoot,
    [switch]$WriteRoles,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
if (-not $PythonPath) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    if (Test-Path -LiteralPath $bundledPython) { $PythonPath = $bundledPython }
    else { $PythonPath = (Get-Command python -ErrorAction Stop).Source }
}
$arguments = @((Join-Path $PSScriptRoot 'cli.py'), $Command, '--project', $Project, '--style', $Style, '--quality', $Quality)
if ($Blocks.Count) { $arguments += @('--blocks', ($Blocks -join ',')) }
if ($BlenderPath) { $arguments += @('--blender', $BlenderPath) }
if ($GameRoot) { $arguments += @('--game-root', $GameRoot) }
if ($BackupRoot) { $arguments += @('--backup-root', $BackupRoot) }
if ($WriteRoles) { $arguments += '--write-roles' }
if ($Force) { $arguments += '--force' }
& $PythonPath @arguments
exit $LASTEXITCODE
