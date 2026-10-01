@echo off
setlocal EnableExtensions
title SincronizadorFacturas
cd /d "%~dp0"

if exist "%~dp0dist\SincronizadorFacturas\SincronizadorFacturas.exe" (
    echo Iniciando version portable...
    start "" "%~dp0dist\SincronizadorFacturas\SincronizadorFacturas.exe"
    exit /b 0
)

set "PYTHON="

if exist "%~dp0.build-venv\Scripts\python.exe" set "PYTHON=%~dp0.build-venv\Scripts\python.exe"
if not defined PYTHON if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not defined PYTHON if exist "%LocalAppData%\Python\pythoncore-3.14-64\python.exe" set "PYTHON=%LocalAppData%\Python\pythoncore-3.14-64\python.exe"

if not defined PYTHON (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3.14 -c "import sys" >nul 2>&1
        if not errorlevel 1 (
            echo Iniciando con Python 3.14...
            py -3.14 "%~dp0servidor.py"
            goto FIN
        )
    )
)

if not defined PYTHON (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON=python"
)

if not defined PYTHON (
    echo.
    echo ERROR: No se encontro Python para ejecutar el codigo fuente.
    echo Para otros PC use la carpeta portable generada en dist\SincronizadorFacturas.
    echo.
    pause
    exit /b 1
)

echo Iniciando codigo fuente...
"%PYTHON%" "%~dp0servidor.py"

:FIN
echo.
echo Servidor detenido.
pause
