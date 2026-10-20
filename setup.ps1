param([switch]$InstallMissing, [string]$UserName, [string]$UserEmail)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
}
function Install-Tool($Id) {
    if (-not $InstallMissing) { throw "Missing dependency: $Id. Run ./setup.ps1 -InstallMissing" }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Install Windows App Installer (winget), then rerun setup.' }
    & winget install --id $Id --exact --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "Installation failed: $Id" }
    Refresh-Path
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Install-Tool 'Git.Git' }
& git --version
if ($LASTEXITCODE -ne 0) { throw 'Git is unavailable. Restart Codex after installation.' }
& git lfs version
if ($LASTEXITCODE -ne 0) { Install-Tool 'GitHub.GitLFS' }
& git lfs install --local
if ($LASTEXITCODE -ne 0) { throw 'Git LFS initialization failed.' }
& git config --local core.autocrlf false
& git config --local pull.ff only
& git config --local push.default simple
if ($UserName) { & git config --local user.name $UserName }
if ($UserEmail) { & git config --local user.email $UserEmail }
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $bundledPython) { $python = $bundledPython } else {
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($python) { & $python -c 'import sys; assert sys.version_info >= (3, 10)'; if ($LASTEXITCODE -ne 0) { $python = $null } }
    if (-not $python) { Install-Tool 'Python.Python.3.12'; $python = (Get-Command python -ErrorAction SilentlyContinue).Source }
}
if (-not $python) { throw 'Python unavailable. Restart Codex after installation.' }
& $python -c 'import sys; assert sys.version_info >= (3, 10); print(sys.version)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ required.' }
$blender = $env:BLENDER_PATH
if (-not $blender) { $blender = (Get-Command blender -ErrorAction SilentlyContinue).Source }
if (-not $blender) {
    $roots = @("$env:ProgramFiles\Blender Foundation", "${env:ProgramFiles(x86)}\Steam\steamapps\common\Blender")
    $blender = Get-ChildItem -LiteralPath $roots -Filter blender.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $blender) {
    Install-Tool 'BlenderFoundation.Blender'
    $blender = Get-ChildItem -LiteralPath "$env:ProgramFiles\Blender Foundation" -Filter blender.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $blender) { throw 'Set BLENDER_PATH to blender.exe and rerun setup.' }
& $blender --version
if ($LASTEXITCODE -ne 0) { throw 'Blender could not start.' }
& git rev-parse --verify HEAD 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    & git lfs pull
    if ($LASTEXITCODE -ne 0) { throw 'LFS download failed. Check remote access and quota.' }
}
$name = & git config user.name
$email = & git config user.email
if (-not $name -or -not $email) { Write-Warning 'Set your own commit identity: ./setup.ps1 -UserName "Your name" -UserEmail "Your email"' }
Write-Host "Ready. Blender: $blender"
Write-Host 'Start viewer: ./serve.ps1; open http://127.0.0.1:8769/viewer.html'
