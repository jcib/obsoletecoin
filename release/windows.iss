#ifndef PackageDir
  #define PackageDir "..\.local\native-package"
#endif
#ifndef ReleaseDir
  #define ReleaseDir "..\.local\release"
#endif
#ifndef ReleaseVersion
  #define ReleaseVersion "0.5.1"
#endif
[Setup]
AppId=ObsoleteCoinMainnet
AppName=Obsolete Coin Mainnet
AppVersion={#ReleaseVersion}
DefaultDirName={localappdata}\Programs\ObsoleteCoinMainnet
DefaultGroupName=Obsolete Coin Mainnet
PrivilegesRequired=lowest
OutputBaseFilename=ObsoleteCoin-Mainnet-Setup
OutputDir={#ReleaseDir}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\ObsoleteCoin.exe
[Files]
Source: "{#PackageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Obsolete Coin Mainnet"; Filename: "{app}\ObsoleteCoin.exe"
Name: "{autodesktop}\Obsolete Coin Mainnet"; Filename: "{app}\ObsoleteCoin.exe"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked
; Data under the user profile is never installed, overwritten or deleted.
