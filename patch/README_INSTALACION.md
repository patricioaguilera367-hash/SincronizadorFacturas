# Extensión de montos — SincronizadorWeb

## Contenido

- `factura_montos.py`: módulo nuevo, independiente, con endpoints y metadata JSON.
- `instalar_montos.py`: modificación controlada de tu **servidor.py existente**, sin reemplazar el validador UNC corregido ni las funciones de búsqueda y sincronización. Crea un `.bak`.
- `templates/index.html`: interfaz completa basada en el HTML entregado, con botón `$` y modal de resumen de la semana.
- `tests/test_factura_montos.py`: pruebas de prefijos, números, extracción sintética, JSON, fotos y PDF.

**Importante:** el paquete NO incluye un `servidor.py` de reemplazo: el tuyo ya tiene la corrección de rutas y la V1.0. El instalador introduce sólo las conexiones necesarias en su código real.

## Instalación en PowerShell

1. Mantente en `feature/montos-facturas`. Comprueba `git status` limpio y haz copia de seguridad si modificaste algo desde que nos enviaste los archivos.
2. Descomprime el ZIP en una carpeta temporal (no lo descomprimas directamente sobre la aplicación):

```powershell
cd C:\Users\Supervisor\Desktop\SincronizadorWeb
Expand-Archive -LiteralPath "$HOME\Downloads\SincronizadorWeb_Montos.zip" -DestinationPath "$env:TEMP\sincronizador_montos" -Force
```

Ajusta la ruta del ZIP si lo descargaste en otra carpeta. Ejecuta lo siguiente **con la aplicación cerrada**:

```powershell
Copy-Item .\templates\index.html .\templates\index.html.antes_montos.bak
Copy-Item "$env:TEMP\sincronizador_montos\factura_montos.py" .\
Copy-Item "$env:TEMP\sincronizador_montos\instalar_montos.py" .\
Copy-Item "$env:TEMP\sincronizador_montos\templates\index.html" .\templates\index.html
Copy-Item "$env:TEMP\sincronizador_montos\tests\test_factura_montos.py" .\tests\
```

3. Instala PyMuPDF en **el mismo Python que utiliza `INICIAR_APP.bat`**. En el diagnóstico previo aparecía esta ruta:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -m pip install pymupdf
```

Si no puedes instalar la biblioteca, la aplicación seguirá permitiendo registrar importes manualmente. Comprueba la ruta de Python de tu `.bat` si difiere.

4. Con el proyecto abierto en PowerShell:

```powershell
python .\instalar_montos.py
python -m py_compile .\servidor.py .\factura_montos.py
python -m unittest discover -s tests -p "test_factura_montos.py"
git diff --stat
git diff -- servidor.py
```

Si alguna prueba falla, **no sincronices**: comparte el mensaje. El instalador crea un backup del backend `servidor.antes_montos.AAAAMMDD_HHMMSS.bak` y arriba también respaldaste el HTML. No registres los `.bak` en Git.

5. Prueba en tu propia app: sube un PDF denominado `F N°587.pdf` a una carpeta de factura de pruebas. Ábrelo con `$` en la semana y comprueba los importes. Sube `DETALLE F N°587.pdf`: no debe incorporarse. Las fotos deben solicitar importes manuales. Comprueba la suma antes de usarla para contabilidad real.

## Funcionalidad

- El prefijo del archivo **debe ser exactamente** `F N°` o `F Nº` (se admiten espacios y mayúsculas/minúsculas) seguido inmediatamente del número y, al final, una extensión PDF o imagen.
- `DETALLE F N°...` queda excluido por la coincidencia al principio del nombre.
- Extracción automática del texto de PDF seleccionables. PDF escaneados o imágenes no son analizados por OCR: aparecen como **Pendiente** con botón ✎ para ingresar Neto, IVA y Total.
- Si neto + IVA no coincide con total, el PDF queda pendiente para evitar importes incorrectos (p. ej., cuando tiene impuestos adicionales). La captura manual permite confirmar esa diferencia y la marca para revisión.
- La información se guarda en `.factura_montos.json` dentro de cada carpeta de factura. Este nombre se excluye del copiado y del control de cambios de OT, para evitar que la metadata altere el estado de sincronización.
- La vista semanal no incluye carpetas ignoradas. Si detecta dos documentos con el mismo número de factura dentro de una carpeta, los marca como duplicados y evita sumarlos hasta resolver la duplicidad.
- El botón ↻ Actualizar del modal vuelve a leer todos los PDF de la semana **sin borrar entradas manuales válidas**. Los archivos actualizados o sustituidos se reanalizan al consultar el resumen.
- Se agregó un filtro contra la carga de un archivo con el nombre reservado `.factura_montos.json`.

## Antes del commit

Añade a `.gitignore` estas líneas si todavía no existen:

```gitignore
servidor.antes_montos.*.bak
templates/*.bak
```

Para comprobar qué registrarás:

```powershell
git status
git add servidor.py factura_montos.py instalar_montos.py templates/index.html tests/test_factura_montos.py .gitignore
git diff --cached --stat
```

**No hagas commit hasta verificar visualmente la tabla, una extracción correcta y la sincronización habitual de una OT de prueba.**
