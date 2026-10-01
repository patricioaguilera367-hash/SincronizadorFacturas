@echo off
setlocal EnableExtensions
title Ineltem - Sincronizador de Facturas [DEV]
cd /d "%~dp0"

set "PYTHON_EXE="
set "USE_PY_LAUNCHER=0"

if exist "%~dp0.build-venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.build-venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%LocalAppData%\Python\pythoncore-3.14-64\python.exe" set "PYTHON_EXE=%LocalAppData%\Python\pythoncore-3.14-64\python.exe"

if not defined PYTHON_EXE (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3.14 -c "import sys" >nul 2>&1
        if not errorlevel 1 set "USE_PY_LAUNCHER=1"
    )
)

if not defined PYTHON_EXE if "%USE_PY_LAUNCHER%"=="0" (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=python"
)

:MENU
call "%~dp0MOSTRAR_LOGO.bat"
echo                         ENTORNO DE DESARROLLO
echo.
echo                [1] Iniciar servidor local
echo                [2] Ejecutar pruebas
echo                [3] Generar portable
echo                [4] Salir
echo.
choice /C 1234 /N /M "                Seleccione una opcion: "
if errorlevel 4 goto FIN
if errorlevel 3 goto BUILD
if errorlevel 2 goto TESTS
if errorlevel 1 goto SERVIDOR
goto MENU

:SERVIDOR
call "%~dp0MOSTRAR_LOGO.bat"
echo                         ENTORNO DE DESARROLLO
echo.
echo                Servidor: http://127.0.0.1:5001
echo                Cierra esta ventana o usa Ctrl+C para detener.
echo.

if not defined PYTHON_EXE if "%USE_PY_LAUNCHER%"=="0" (
    echo ERROR: No se encontro Python.
    echo.
    pause
    goto MENU
)

start "" powershell.exe -NoLogo -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5001'"

if "%USE_PY_LAUNCHER%"=="1" (
    py -3.14 "%~dp0servidor.py"
) else (
    "%PYTHON_EXE%" "%~dp0servidor.py"
)

echo.
echo Servidor detenido.
pause
goto MENU

:TESTS
call "%~dp0MOSTRAR_LOGO.bat"
echo                         PRUEBAS DEL PROYECTO
echo.

if not defined PYTHON_EXE if "%USE_PY_LAUNCHER%"=="0" (
    echo ERROR: No se encontro Python.
    echo.
    pause
    goto MENU
)

if "%USE_PY_LAUNCHER%"=="1" (
    py -3.14 -m unittest discover -s tests -p "test_*.py"
) else (
    "%PYTHON_EXE%" -m unittest discover -s tests -p "test_*.py"
)

echo.
pause
goto MENU

:BUILD
call "%~dp0MOSTRAR_LOGO.bat"
echo                         GENERAR PORTABLE
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0BUILD_PORTABLE.ps1"
echo.
pause
goto MENU

:FIN
endlocal
exit /b 0
