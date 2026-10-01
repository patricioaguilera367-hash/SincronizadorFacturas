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
            throw "No se encontro Python en este PC de desarrollo."
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
    throw "Las pruebas fallaron. Se cancelo el build."
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
    "--console",
    "--name", "SincronizadorFacturas",
    "--add-data", "templates;templates",
    "--collect-all", "pymupdf",
    "servidor.py"
)
& $Python -m PyInstaller @ArgsPyInstaller

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller termino con error."
}

if (-not (Test-Path $Dist)) {
    throw "No se genero la carpeta portable esperada."
}

Copy-Item (Join-Path $Root "config.example.json") (Join-Path $Dist "config.json") -Force
Copy-Item (Join-Path $Root "INICIAR_PORTABLE.bat") (Join-Path $Dist "INICIAR.bat") -Force
Copy-Item (Join-Path $Root "MOSTRAR_LOGO.bat") (Join-Path $Dist "MOSTRAR_LOGO.bat") -Force

$leerme = @'
SINCRONIZADORFACTURAS PORTABLE

1. Copie esta carpeta completa al PC de destino.
2. No instale Python, Flask, PyMuPDF ni Git.
3. Verifique que el PC pueda acceder a \\192.168.99.61\obras.
4. Ejecute INICIAR.bat.
5. Si cambia el servidor, edite config.json.

La ventana de consola queda visible a proposito.
Cerrar esa ventana detiene el servidor.

No copie solamente el .exe:
la carpeta _internal es parte de la aplicacion.
'@

Set-Content -Path (Join-Path $Dist "LEEME_PORTABLE.txt") -Value $leerme -Encoding ASCII

Write-Host ""
Write-Host "BUILD COMPLETADO" -ForegroundColor Green
Write-Host "Portable:"
Write-Host "  $Dist"
Write-Host ""
Write-Host "Copie TODA esa carpeta al otro PC."
