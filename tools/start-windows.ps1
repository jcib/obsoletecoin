param(
    [string]$Server = '192.0.2.36:19777',
    [ValidateSet('mine','wallet')][string]$Mode = 'mine',
    [ValidateRange(0,2147483647)][int]$Blocks = 0
)
$ErrorActionPreference = 'Stop'
function Stop-WithHelp([string]$Message) {
    Write-Host $Message -ForegroundColor Red
    Write-Host 'See docs/WINDOWS.md for setup instructions.'
    exit 2
}
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    Stop-WithHelp 'WSL is missing. Install WSL with Debian before starting the miner.'
}
$distroOutput = ((& wsl.exe --list --quiet 2>&1) -join "`n") -replace "`0", ''
$distroExit = $LASTEXITCODE
if ($distroExit -ne 0) {
    Write-Host $distroOutput
    Stop-WithHelp 'WSL could not list its distributions. If none are installed, run: wsl --install -d Debian'
}
if ($distroOutput -notmatch '(?m)^Debian\s*$') {
    Stop-WithHelp 'Debian is not installed in WSL. Run: wsl --install -d Debian. Then open Debian and install the runtime libraries.'
}
$packageRoot = Split-Path -Parent $PSScriptRoot
$pathOutput = (& wsl.exe -d Debian --exec wslpath -u $packageRoot) -join "`n"
if ($LASTEXITCODE -ne 0) { Stop-WithHelp 'Debian could not start or access this folder. Open Debian once to finish setup.' }
$linuxRoot = $pathOutput.Trim()
& wsl.exe -d Debian --exec bash "$linuxRoot/tools/start-laptop.sh" $Server $Mode $Blocks
exit $LASTEXITCODE
