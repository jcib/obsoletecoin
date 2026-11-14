param([string]$Python = ".local/build-venv314/Scripts/python.exe", [string]$Output = ".local/native-dist")
$ErrorActionPreference = 'Stop'
$env:PYTHONHASHSEED = '0'
$env:SOURCE_DATE_EPOCH = '1794614400'
& $Python -c "import sys; assert sys.version_info[:3] == (3,14,10), 'Use CPython 3.14.10 for this candidate'"
if ($LASTEXITCODE -ne 0) { throw 'Unexpected build runtime' }
$Tk = (& $Python release/prepare-tk.py | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0) { throw 'Tcl/Tk smoke failed' }
if ($Tk.TCL_LIBRARY) { $env:TCL_LIBRARY = $Tk.TCL_LIBRARY; $env:TK_LIBRARY = $Tk.TK_LIBRARY }
$Assets = (Resolve-Path "tools/assets").Path
& $Python -m PyInstaller --noconfirm --clean --windowed --onedir --noupx --name ObsoleteCoin --paths tools --add-data "$Assets;assets" --distpath $Output --workpath .local/pyinstaller-work --specpath .local tools/native_wallet.py
if ($LASTEXITCODE -ne 0) { throw 'Wallet packaging failed' }
