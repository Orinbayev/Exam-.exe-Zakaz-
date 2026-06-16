[Setup]
AppName=Smart Exam - O'quvchi Paneli
AppVersion=1.0
AppPublisher=Smart Exam System
DefaultDirName={autopf}\SmartExam\OquvchiPanel
DefaultGroupName=Smart Exam
OutputDir=installer
OutputBaseFilename=OquvchiPanel-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\OquvchiPanel.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\OquvchiPanel\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\O'quvchi Paneli"; Filename: "{app}\OquvchiPanel.exe"
Name: "{commondesktop}\O'quvchi Paneli"; Filename: "{app}\OquvchiPanel.exe"

[Run]
Filename: "{app}\OquvchiPanel.exe"; Description: "Dasturni ishga tushirish"; Flags: nowait postinstall skipifsilent
