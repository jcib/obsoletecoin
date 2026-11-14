[Setup]
AppId=ObsoleteCoinTestnet
AppName=Obsolete Coin Testnet
AppVersion=0.3.0
DefaultDirName={localappdata}\Programs\ObsoleteCoinTestnet
DefaultGroupName=Obsolete Coin Testnet
PrivilegesRequired=lowest
OutputBaseFilename=ObsoleteCoin-Testnet-Setup
OutputDir=..\.local\release
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\ObsoleteCoin.exe
[Files]
Source: "..\.local\native-package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Obsolete Coin Testnet"; Filename: "{app}\ObsoleteCoin.exe"
Name: "{autodesktop}\Obsolete Coin Testnet"; Filename: "{app}\ObsoleteCoin.exe"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked
; Data under the user profile is never installed, overwritten or deleted.
