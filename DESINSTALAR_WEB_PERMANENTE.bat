@echo off
setlocal EnableExtensions
for /f "usebackq delims=" %%I in (`powershell.exe -NoProfile -Command "[Environment]::GetFolderPath('Startup')"`) do set "STARTUP=%%I"

del /Q "%STARTUP%\YouTube a MP3 Web.vbs" >nul 2>&1
del /Q "%STARTUP%\YouTube a MP3 Web.ruta.txt" >nul 2>&1

echo Se ha eliminado el inicio automatico de la web.
pause
