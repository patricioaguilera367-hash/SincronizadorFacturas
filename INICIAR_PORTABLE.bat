@echo off
setlocal EnableExtensions
title Ineltem - Sincronizador de Facturas
cd /d "%~dp0"

call "%~dp0MOSTRAR_LOGO.bat"
echo                           APLICACION PORTABLE
echo.
echo                Servidor local: http://127.0.0.1:5001
echo                La interfaz se abrira automaticamente.
echo.
echo                Para detener la aplicacion:
echo                cierra esta ventana o presiona Ctrl+C.
echo.
echo -------------------------------------------------------------------------------
echo.

if not exist "%~dp0SincronizadorFacturas.exe" (
    echo ERROR: No se encontro SincronizadorFacturas.exe
    echo.
    pause
    exit /b 1
)

start "" powershell.exe -NoLogo -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5001'"

rem Se ejecuta en primer plano a proposito.
rem Asi, cerrar esta consola tambien detiene el servidor.
"%~dp0SincronizadorFacturas.exe"
set "APP_EXIT=%ERRORLEVEL%"

echo.
echo -------------------------------------------------------------------------------
if not "%APP_EXIT%"=="0" echo La aplicacion termino con codigo %APP_EXIT%.
echo Servidor detenido.
echo.
echo Presiona ENTER para cerrar...
set /p "_="
exit /b %APP_EXIT%
