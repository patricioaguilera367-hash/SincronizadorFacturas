@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Motor del Sincronizador Web
color 0A
cd /d "%~dp0"
set "PYTHON=C:\Users\Supervisor\AppData\Local\Python\bin\python.exe"

:MENU
cls
echo ========================================================
echo MOTOR DEL SINCRONIZADOR WEB
echo ========================================================
echo.
echo [1] Iniciar servidor
echo [2] Diagnosticar entorno
echo [3] Trazar rutas OT y facturas (solo lectura)
echo [4] Salir
choice /C 1234 /N /M "Seleccione una opcion"
if errorlevel 4 goto END
if errorlevel 3 goto TRAZA_MENU
if errorlevel 2 goto DIAGNOSTICO
if errorlevel 1 goto INICIAR

:INICIAR
call :CHECK_PORT
if errorlevel 1 (
    echo.
    echo El servidor no se inicio. Corrija el problema del puerto 5001 y vuelva a intentarlo.
    pause
    goto MENU
)

echo.
echo ========================================================
echo INICIANDO EL SERVIDOR LOCAL... POR FAVOR NO CIERRE ESTA VENTANA
echo ========================================================
echo.
echo Servidor corriendo en http://localhost:5001
echo Para detenerlo, presione Ctrl+C.
echo.
"%PYTHON%" "%~dp0servidor.py"

echo.
echo Servidor detenido.
pause
goto MENU

:DIAGNOSTICO
cls
echo ========================================================
echo DIAGNOSTICO DEL ENTORNO
echo ========================================================
echo.
echo Identidad de Windows:
whoami
echo.
echo Python configurado:
if exist "%PYTHON%" (
    "%PYTHON%" --version
) else (
    echo ERROR: No se encontro "%PYTHON%".
)
echo.
echo Puerto 5001:
call :CHECK_PORT
echo.
echo Acceso a BASE_FACTURAS:
call :CHECK_READ_PATH "\\192.168.99.61\obras\Facturas pensiones\Facturas pensiones" "BASE_FACTURAS documentada"
echo.
pause
goto MENU

:TRAZA_MENU
cls
echo ========================================================
echo TRAZA DE RUTAS OT Y FACTURAS - SOLO LECTURA
echo ========================================================
echo Esta herramienta nunca copia, crea, elimina ni modifica archivos.
echo No instrumenta servidor.py; solo comprueba rutas documentadas.
echo.
echo [1] Comprobar rutas base de facturas y obras
echo [2] Buscar una OT bajo la ruta de obras
echo [3] Comprobar una ruta relativa de factura
echo [4] Volver
choice /C 1234 /N /M "Seleccione una opcion"
if errorlevel 4 goto MENU
if errorlevel 3 goto TRAZA_FACTURA
if errorlevel 2 goto TRAZA_OT
if errorlevel 1 goto TRAZA_BASES

:TRAZA_BASES
cls
echo === Paso 1: identidad que realiza la comprobacion ===
whoami
echo.
echo === Paso 2: ruta base de facturas ===
call :CHECK_READ_PATH "\\192.168.99.61\obras\Facturas pensiones\Facturas pensiones" "Facturas"
echo.
echo === Paso 3: ruta base de obras para localizar OT ===
call :CHECK_READ_PATH "\\192.168.99.61\obras" "Obras"
echo.
pause
goto TRAZA_MENU

:TRAZA_OT
cls
echo === Traza de busqueda de OT ===
echo Identidad de Windows:
whoami
echo.
echo Paso 1: se comprobara la ruta base de obras.
call :CHECK_READ_PATH "\\192.168.99.61\obras" "Obras"
if errorlevel 1 (
    echo DETENIDO: no es seguro buscar la OT hasta resolver el acceso a Obras.
    echo.
    pause
    goto TRAZA_MENU
)
echo.
set "DIAG_OT="
set /p "DIAG_OT=Paso 2: escriba el codigo OT (letras, numeros, guion, guion bajo o barra): "
echo(!DIAG_OT!| findstr /R /X "[A-Za-z0-9][A-Za-z0-9_/-]*" >nul
if errorlevel 1 (
    echo ERROR: codigo OT invalido o vacio. No se probo ninguna ruta.
    echo.
    pause
    goto TRAZA_MENU
)
echo Paso 3: se buscaran carpetas cuyo nombre coincida al normalizar letras y numeros.
echo Limite: profundidad 4 y 1500 carpetas; no se escribira nada.
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $root='\\192.168.99.61\obras'; $ot=[Environment]::GetEnvironmentVariable('DIAG_OT'); $normalizedOt=($ot -replace '[^A-Za-z0-9]','').ToUpperInvariant(); $maxDepth=4; $maxDirs=1500; $queue=New-Object System.Collections.Queue; $queue.Enqueue([PSCustomObject]@{Path=$root;Depth=0}); $seen=0; $matches=@(); $accessErrors=@(); $readErrors=@(); while($queue.Count -gt 0 -and $seen -lt $maxDirs){ $current=$queue.Dequeue(); Write-Host ('REVISANDO: ' + $current.Path); try { $children=Get-ChildItem -LiteralPath $current.Path -Directory -Force -ErrorAction Stop } catch [System.UnauthorizedAccessException] { $accessErrors += $current.Path; continue } catch { $readErrors += $current.Path; Write-Host ('ERROR al leer: ' + $current.Path + ' - ' + $_.Exception.Message); continue }; foreach($child in $children){ if($current.Path -eq $root -and $child.Name -ieq 'Facturas pensiones'){ Write-Host ('OMITIDA: ' + $child.FullName + ' (subarbol de facturas)'); continue }; $seen++; $normalizedCandidate=($child.Name -replace '[^A-Za-z0-9]','').ToUpperInvariant(); if($normalizedCandidate -eq $normalizedOt){ $matches += $child.FullName; Write-Host ('ENCONTRADA: entrada=' + $ot + '; carpeta=' + $child.Name + '; ruta=' + $child.FullName) }; if($current.Depth -lt $maxDepth -and $seen -lt $maxDirs){ $queue.Enqueue([PSCustomObject]@{Path=$child.FullName;Depth=($current.Depth + 1)}) } } }; Write-Host ('Carpetas revisadas: ' + $seen); if($accessErrors.Count -gt 0){ Write-Host ('INACCESIBLE: ' + $accessErrors.Count + ' tramo(s) sin permiso. Primera ruta: ' + $accessErrors[0]) }; if($readErrors.Count -gt 0){ Write-Host ('ERROR: ' + $readErrors.Count + ' tramo(s) no se pudieron leer. Primera ruta: ' + $readErrors[0]) }; if($matches.Count -gt 0){ Write-Host 'RESULTADO: OT localizada; la sincronizacion no fue ejecutada.'; exit 0 }; if($accessErrors.Count -gt 0){ Write-Host 'RESULTADO: OT no localizada dentro del alcance; hay rutas inaccesibles.'; exit 2 }; if($readErrors.Count -gt 0){ Write-Host 'RESULTADO: busqueda incompleta por error de lectura.'; exit 1 }; if($seen -ge $maxDirs){ Write-Host 'RESULTADO: limite de 1500 carpetas alcanzado; resultado incompleto.'; exit 4 }; Write-Host 'RESULTADO: OT no encontrada en las rutas revisadas.'; exit 3"
set "DIAG_OT_RESULT=!errorlevel!"
if "!DIAG_OT_RESULT!"=="0" echo RESULTADO FINAL: OT localizada.
if "!DIAG_OT_RESULT!"=="1" echo RESULTADO FINAL: error de lectura; resultado incompleto.
if "!DIAG_OT_RESULT!"=="2" echo RESULTADO FINAL: se encontro una ruta inaccesible.
if "!DIAG_OT_RESULT!"=="3" echo RESULTADO FINAL: no encontrada.
if "!DIAG_OT_RESULT!"=="4" echo RESULTADO FINAL: limite de recorrido alcanzado; resultado incompleto.
echo.
pause
goto TRAZA_MENU

:TRAZA_FACTURA
cls
echo === Traza de ruta de factura ===
echo Identidad de Windows:
whoami
echo.
echo Paso 1: ruta base documentada.
call :CHECK_READ_PATH "\\192.168.99.61\obras\Facturas pensiones\Facturas pensiones" "Facturas"
if errorlevel 1 (
    echo DETENIDO: no se puede revisar una factura hasta resolver la ruta base.
    echo.
    pause
    goto TRAZA_MENU
)
echo.
set "DIAG_FACTURA="
set /p "DIAG_FACTURA=Paso 2: ruta relativa bajo Facturas (vacia para solo la base): "
powershell -NoProfile -Command "$r=[Environment]::GetEnvironmentVariable('DIAG_FACTURA'); if([string]::IsNullOrWhiteSpace($r)){exit 0}; if($r -match '(^[\\/]|:|(^|[\\/])\.\.([\\/]|$))'){exit 1}; exit 0"
if errorlevel 1 (
    echo ERROR: use una ruta relativa sin unidad, ruta UNC ni '..'. No se probo ninguna ruta adicional.
    echo.
    pause
    goto TRAZA_MENU
)
if not defined DIAG_FACTURA (
    echo RESULTADO: solo se comprobo la ruta base de Facturas.
) else (
    echo Paso 3: ruta de factura construida bajo la base documentada.
    powershell -NoProfile -Command "$base='\\192.168.99.61\obras\Facturas pensiones\Facturas pensiones'; $r=[Environment]::GetEnvironmentVariable('DIAG_FACTURA'); $path=Join-Path -Path $base -ChildPath $r; Write-Host ('Ruta probada: ' + $path); try { $item=Get-Item -LiteralPath $path -Force -ErrorAction Stop; if(-not $item.PSIsContainer){ Write-Host 'RESULTADO: encontrada, pero no es una carpeta.'; exit 1 }; $null=Get-ChildItem -LiteralPath $path -Force -ErrorAction Stop | Select-Object -First 1; Write-Host 'RESULTADO: ACCESIBLE para lectura; no se ejecuto sincronizacion.'; exit 0 } catch [System.UnauthorizedAccessException] { Write-Host ('RESULTADO: INACCESIBLE - ' + $_.Exception.Message); exit 2 } catch [System.Management.Automation.ItemNotFoundException] { Write-Host 'RESULTADO: NO ENCONTRADA.'; exit 3 } catch { if($_.Exception.Message -match '(?i)access|deneg|permiso'){ Write-Host ('RESULTADO: INACCESIBLE - ' + $_.Exception.Message); exit 2 }; Write-Host ('RESULTADO: ERROR - ' + $_.Exception.Message); exit 1 }"
)
echo.
pause
goto TRAZA_MENU

:CHECK_READ_PATH
echo Ruta probada (%~2): %~1
set "DIAG_READ_PATH=%~1"
powershell -NoProfile -Command "$p=$env:DIAG_READ_PATH; try { $item=Get-Item -LiteralPath $p -Force -ErrorAction Stop; if(-not $item.PSIsContainer){ Write-Host 'RESULTADO: encontrada, pero no es una carpeta.'; exit 1 }; $null=Get-ChildItem -LiteralPath $p -Force -ErrorAction Stop | Select-Object -First 1; Write-Host 'RESULTADO: ACCESIBLE para lectura.'; exit 0 } catch [System.UnauthorizedAccessException] { Write-Host ('RESULTADO: INACCESIBLE - ' + $_.Exception.Message); exit 2 } catch [System.Management.Automation.ItemNotFoundException] { Write-Host 'RESULTADO: NO ENCONTRADA.'; exit 3 } catch { if($_.Exception.Message -match '(?i)access|deneg|permiso'){ Write-Host ('RESULTADO: INACCESIBLE - ' + $_.Exception.Message); exit 2 }; Write-Host ('RESULTADO: ERROR - ' + $_.Exception.Message); exit 1 }"
exit /b %errorlevel%

:CHECK_PORT
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $queryErrors=@(); $listener = Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue -ErrorVariable +queryErrors | Select-Object -First 1; if ($null -ne $listener) { Write-Host ('Puerto 5001 ocupado por PID ' + $listener.OwningProcess + '.'); exit 2 }; if ($queryErrors.Count -gt 0) { if ($queryErrors[0].FullyQualifiedErrorId -like '*CmdletizationQuery_NotFound*') { exit 0 }; Write-Host $queryErrors[0].Exception.Message; exit 1 }; exit 0"
if errorlevel 2 (
    echo BLOQUEADO: el puerto 5001 ya esta en uso. No se detuvo ningun proceso.
    exit /b 2
)
if errorlevel 1 (
    echo ERROR: no se pudo comprobar el puerto 5001. El servidor no se iniciara.
    exit /b 1
)
echo Puerto 5001 disponible.
exit /b 0

:END
endlocal
exit /b 0
