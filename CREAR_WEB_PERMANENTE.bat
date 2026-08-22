@echo off
setlocal EnableExtensions
cd /d "%~dp0"

for /f "usebackq delims=" %%I in (`powershell.exe -NoProfile -Command "[Environment]::GetFolderPath('Startup')"`) do set "STARTUP=%%I"
if not defined STARTUP (
  echo No se pudo localizar la carpeta de Inicio de Windows.
  pause
  exit /b 1
)
set "STARTUP_LAUNCHER=%STARTUP%\YouTube a MP3 Web.vbs"
set "STARTUP_ROUTE=%STARTUP%\YouTube a MP3 Web.ruta.txt"
set "LOCAL_LAUNCHER=%~dp0INICIAR_SERVIDOR_OCULTO.vbs"
set "STARTUP_TEMPLATE=%~dp0INICIAR_WEB_AL_ARRANCAR.vbs"

if not exist "%~dp0servidor.ps1" (
  echo No se encuentra servidor.ps1.
  pause
  exit /b 1
)

if not exist "%LOCAL_LAUNCHER%" (
  echo No se encuentra INICIAR_SERVIDOR_OCULTO.vbs.
  pause
  exit /b 1
)

if not exist "%STARTUP_TEMPLATE%" (
  echo No se encuentra INICIAR_WEB_AL_ARRANCAR.vbs.
  pause
  exit /b 1
)

copy /Y "%STARTUP_TEMPLATE%" "%STARTUP_LAUNCHER%" >nul
if errorlevel 1 (
  echo No se pudo dejar configurado el inicio automatico.
  echo Windows no permite escribir en tu carpeta de Inicio.
  pause
  exit /b 1
)

> "%STARTUP_ROUTE%" echo "%~dp0"
if errorlevel 1 (
  echo No se pudo guardar la ruta de la web para el inicio automatico.
  pause
  exit /b 1
)

start "" wscript.exe "%LOCAL_LAUNCHER%"
timeout /t 2 /nobreak >nul
start "" "http://localhost:8787"

echo.
echo La web ya esta preparada para iniciarse automaticamente al abrir sesion.
echo No requiere permisos de administrador.
echo Se abrira en: http://localhost:8787
echo.
pause
