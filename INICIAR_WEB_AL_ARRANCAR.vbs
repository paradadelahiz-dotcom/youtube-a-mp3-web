Option Explicit

Dim fso, shell, startupFolder, routeFile, reader, projectFolder, command
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

startupFolder = fso.GetParentFolderName(WScript.ScriptFullName)
routeFile = fso.BuildPath(startupFolder, "YouTube a MP3 Web.ruta.txt")

If fso.FileExists(routeFile) Then
    Set reader = fso.OpenTextFile(routeFile, 1, False)
    projectFolder = Trim(reader.ReadLine)
    reader.Close

    If Left(projectFolder, 1) = """" And Right(projectFolder, 1) = """" Then
        projectFolder = Mid(projectFolder, 2, Len(projectFolder) - 2)
    End If

    If fso.FileExists(fso.BuildPath(projectFolder, "servidor.ps1")) Then
        command = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & fso.BuildPath(projectFolder, "servidor.ps1") & """"
        shell.Run command, 0, False
    End If
End If
