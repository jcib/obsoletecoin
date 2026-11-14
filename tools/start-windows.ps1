param([string]$Server = '192.0.2.36:19777', [ValidateSet('mine','wallet')][string]$Mode = 'mine')
$ErrorActionPreference = 'Stop'
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'Install WSL with Debian first. See docs/WINDOWS.md.'
}
$distros = ((& wsl.exe --list --quiet) -join "`n") -replace "`0", ''
if ($LASTEXITCODE -ne 0 -or $distros -notmatch '(?m)^Debian\s*$') {
    throw 'Debian is not initialized in WSL. Run wsl --install -d Debian, open Debian once, and follow docs/WINDOWS.md.'
}
$packageRoot = Split-Path -Parent $PSScriptRoot
$linuxRoot = (& wsl.exe -d Debian -- wslpath -u $packageRoot).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot access the package from Debian.' }
& wsl.exe -d Debian -- bash "$linuxRoot/tools/start-laptop.sh" $Server $Mode
exit $LASTEXITCODE
