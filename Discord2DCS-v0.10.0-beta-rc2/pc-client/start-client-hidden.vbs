Option Explicit
Dim fso, shell, base, pythonw, client
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
base = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = base & "\.venv\Scripts\pythonw.exe"
client = base & "\client.py"
shell.CurrentDirectory = base
If fso.FileExists(pythonw) And fso.FileExists(client) Then
    shell.Run Chr(34) & pythonw & Chr(34) & " " & Chr(34) & client & Chr(34), 0, False
End If
