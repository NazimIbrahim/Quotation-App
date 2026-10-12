; Script generated for Inno Setup 6
; AMA Ceramics Quotation Management System Installer

#define MyAppName "AMA Ceramics Quotation Management System"
#define MyAppVersion "1.0"
#define MyAppPublisher "AMA Ceramics Pvt Ltd"
#define MyAppURL "https://www.amaceramics.com"
#define MyAppExeName "AMA_Ceramics_Quotation.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{5C70A21B-4089-4FA3-89AC-0E7C3E1492D8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\AMA Ceramics Quotation
DefaultGroupName=AMA Ceramics
DisableProgramGroupPage=yes
; Support installing per-user without admin rights or for all users with admin
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist_installer
OutputBaseFilename=AMA_Ceramics_Quotation_Setup_v1.0
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion=1.0.0.0
VersionInfoCompany=AMA Ceramics Pvt Ltd
VersionInfoDescription=AMA Ceramics Quotation Management System Installer
VersionInfoProductVersion=1.0.0.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\AMA_Ceramics_Quotation\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app_icon.ico"
Name: "{autodesktop}\AMA Ceramics Quotation"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
