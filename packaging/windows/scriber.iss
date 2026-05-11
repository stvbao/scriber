#define MyAppName "Scriber"
#define MyAppPublisher "Scriber"
#define MyAppURL "https://github.com/stvbao/Scriber"
#define MyAppExeName "Scriber.exe"
#ifndef MyAppVersion
#define MyAppVersion "0.0.0"
#endif
#ifndef SourceDir
#define SourceDir "..\..\dist\Scriber"
#endif
#ifndef OutputDir
#define OutputDir "..\..\dist"
#endif

[Setup]
AppId={{A214732B-C560-4C7D-9C4C-6687DFD2E8F1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=Scriber-{#MyAppVersion}-windows-installer
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "addtopath"; Description: "Add Scriber to the user PATH"; GroupDescription: "Command line:"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Scriber"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall Scriber"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Scriber"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,Scriber}"; Flags: nowait postinstall skipifsilent

[Code]
const
  EnvRegKey = 'Environment';
  HWND_BROADCAST = $FFFF;
  WM_SETTINGCHANGE = $001A;
  SMTO_ABORTIFHUNG = $0002;

function SendMessageTimeout(hWnd: LongWord; Msg: LongWord; wParam: LongWord; lParam: String; fuFlags: LongWord; uTimeout: LongWord; var lpdwResult: LongWord): LongWord;
external 'SendMessageTimeoutW@user32.dll stdcall';

function GetUserPath(): string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, EnvRegKey, 'Path', Result) then
    Result := '';
end;

function PathContains(ExistingPath: string; Entry: string): Boolean;
var
  NormalizedPath: string;
  NormalizedEntry: string;
begin
  NormalizedPath := ';' + Lowercase(ExistingPath) + ';';
  NormalizedEntry := ';' + Lowercase(Entry) + ';';
  StringChangeEx(NormalizedPath, ';;', ';', True);
  Result := Pos(NormalizedEntry, NormalizedPath) > 0;
end;

procedure AddToUserPath(Entry: string);
var
  ExistingPath: string;
begin
  ExistingPath := GetUserPath();
  if not PathContains(ExistingPath, Entry) then begin
    if ExistingPath = '' then
      RegWriteStringValue(HKEY_CURRENT_USER, EnvRegKey, 'Path', Entry)
    else
      RegWriteStringValue(HKEY_CURRENT_USER, EnvRegKey, 'Path', ExistingPath + ';' + Entry);
  end;
end;

procedure RemoveFromUserPath(Entry: string);
var
  ExistingPath: string;
  Parts: TArrayOfString;
  I: Integer;
  NewPath: string;
begin
  ExistingPath := GetUserPath();
  if ExistingPath = '' then
    Exit;

  StringChangeEx(ExistingPath, Entry + ';', '', True);
  StringChangeEx(ExistingPath, ';' + Entry, '', True);

  Parts := SplitString(ExistingPath, ';');
  NewPath := '';
  for I := 0 to GetArrayLength(Parts) - 1 do begin
    if (Parts[I] <> '') and (CompareText(Parts[I], Entry) <> 0) then begin
      if NewPath = '' then
        NewPath := Parts[I]
      else
        NewPath := NewPath + ';' + Parts[I];
    end;
  end;

  RegWriteStringValue(HKEY_CURRENT_USER, EnvRegKey, 'Path', NewPath);
end;

procedure BroadcastEnvironmentChange();
var
  ResultCode: LongWord;
begin
  SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', SMTO_ABORTIFHUNG, 5000, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    if IsTaskSelected('addtopath') then begin
      AddToUserPath(ExpandConstant('{app}'));
      BroadcastEnvironmentChange();
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then begin
    RemoveFromUserPath(ExpandConstant('{app}'));
    BroadcastEnvironmentChange();
  end;
end;
