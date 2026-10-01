$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Venv = Join-Path $Root ".build-venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$Dist = Join-Path $Root "dist\SincronizadorFacturas"
$Build = Join-Path $Root "build"

Write-Host "=== SincronizadorFacturas - build portable ===" -ForegroundColor Cyan

if (-not (Test-Path $Python)) {
    $py = Get-Command py -ErrorAction SilentlyContinue

    if ($py) {
        Write-Host "Creando entorno de build con Python 3.14..."
        & py -3.14 -m venv $Venv
    }
    else {
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCmd) {
            throw "No se encontró Python en este PC de desarrollo."
        }

        Write-Host "Creando entorno de build con Python..."
        & python -m venv $Venv
    }
}

if (-not (Test-Path $Python)) {
    throw "No se pudo crear .build-venv."
}

Write-Host "Actualizando pip..."
& $Python -m pip install --upgrade pip

Write-Host "Instalando dependencias de build..."
& $Python -m pip install -r (Join-Path $Root "requirements-portable.txt")

Write-Host "Ejecutando pruebas..."
& $Python -m unittest discover -s tests -p "test_*.py"
if ($LASTEXITCODE -ne 0) {
    throw "Las pruebas fallaron. Se canceló el build."
}

Write-Host "Limpiando build anterior..."
if (Test-Path $Build) {
    Remove-Item $Build -Recurse -Force
}
if (Test-Path $Dist) {
    Remove-Item $Dist -Recurse -Force
}

Write-Host "Generando portable ONEDIR..."
$ArgsPyInstaller = @(
    "--noconfirm",
    "--clean",
    "--onedir",
    "--name", "SincronizadorFacturas",
    "--add-data", "templates;templates",
    "--collect-all", "pymupdf",
    "servidor.py"
)
& $Python -m PyInstaller @ArgsPyInstaller

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller terminó con error."
}

if (-not (Test-Path $Dist)) {
    throw "No se generó la carpeta portable esperada."
}

$configOrigen = Join-Path $Root "config.example.json"
$configDestino = Join-Path $Dist "config.json"
Copy-Item $configOrigen $configDestino -Force

$iniciar = @'
@echo off
setlocal
cd /d "%~dp0"
start "" "SincronizadorFacturas.exe"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5001"
exit /b 0
'@
Set-Content -Path (Join-Path $Dist "INICIAR.bat") -Value $iniciar -Encoding ASCII

$leerme = @'
SINCRONIZADORFACTURAS PORTABLE

1. Copie esta carpeta completa al PC de destino.
2. No instale Python, Flask, PyMuPDF ni Git.
3. Verifique que el PC pueda acceder a \\192.168.99.61\obras.
4. Ejecute INICIAR.bat o SincronizadorFacturas.exe.
5. Si cambia el servidor, edite config.json.

No copie solamente el .exe: la carpeta _internal es parte de la aplicación.
'@
Set-Content -Path (Join-Path $Dist "LEEME_PORTABLE.txt") -Value $leerme -Encoding UTF8

Write-Host ""
Write-Host "BUILD COMPLETADO" -ForegroundColor Green
Write-Host "Portable:"
Write-Host "  $Dist"
Write-Host ""
Write-Host "Copie TODA esa carpeta al otro PC."
