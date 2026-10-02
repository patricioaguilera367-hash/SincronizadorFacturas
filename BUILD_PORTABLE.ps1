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

# indice_obras.csv es un seed local opcional. Esta ignorado por Git porque
# contiene estructura interna de la empresa. Si existe al construir, viaja
# junto al portable y se importa una sola vez al indice persistente local.
$IndiceSeed = Join-Path $Root "indice_obras.csv"
if (Test-Path $IndiceSeed) {
    Copy-Item $IndiceSeed (Join-Path $Dist "indice_obras.csv") -Force
    Write-Host "Seed OT incluido: indice_obras.csv"
}
else {
    Write-Host "Seed OT no encontrado; el indice se construira dinamicamente." -ForegroundColor Yellow
}

$leerme = @'
SINCRONIZADORFACTURAS PORTABLE

1. Copie esta carpeta completa al PC de destino.
2. No instale Python, Flask, PyMuPDF ni Git.
3. Ejecute INICIAR.bat.
4. Si el servidor esta disponible, la app actualiza el indice OT en segundo plano.
5. Si el servidor no esta disponible, la app puede mostrar el ultimo snapshot en modo SOLO LECTURA.
6. Si cambia el servidor, edite config.json.

Si existe indice_obras.csv junto al ejecutable, se usa solo como seed inicial.
Luego el indice local se mantiene en data\indice_ot.json.
El snapshot de contexto se guarda en data\snapshot_app.json.

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
