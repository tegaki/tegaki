[Setup]
AppName=tegaki-recognize
AppVerName=tegaki-recognize 0.3
AppPublisher=Mathieu Blondel
AppPublisherURL=http://www.tegaki.org
DefaultDirName={pf}\tegaki-recognize
DefaultGroupName=tegaki-recognize
DisableProgramGroupPage=true
OutputBaseFilename=setup
Compression=lzma
SolidCompression=true
AllowUNCPath=false
VersionInfoVersion=0.3
VersionInfoCompany=Tegaki
VersionInfoDescription=tegaki-recognize
;PrivilegeRequired=admin

[Dirs]
Name: {app}; Flags: uninsalwaysuninstall;

[Files]
Source: ..\dist\*; DestDir: {app}; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: {group}\tegaki-recognize; Filename: {app}\tegaki-recognize.exe; WorkingDir: {app}

[Run]
Filename: {app}\tegaki-recognize.exe; Description: {cm:LaunchProgram,tegaki-recognize}; Flags: nowait postinstall skipifsilent
