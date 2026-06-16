[Setup]
AppName=Smart Exam - O'qituvchi Paneli
AppVersion=1.0
AppPublisher=Smart Exam System
DefaultDirName={autopf}\SmartExam\OqituvchiPanel
DefaultGroupName=Smart Exam
OutputDir=installer
OutputBaseFilename=OqituvchiPanel-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\OqituvchiPanel.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\OqituvchiPanel\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\O'qituvchi Paneli"; Filename: "{app}\OqituvchiPanel.exe"
Name: "{commondesktop}\O'qituvchi Paneli"; Filename: "{app}\OqituvchiPanel.exe"

[Run]
Filename: "{app}\OqituvchiPanel.exe"; Description: "Dasturni ishga tushirish"; Flags: nowait postinstall skipifsilent
