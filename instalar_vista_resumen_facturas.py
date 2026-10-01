from pathlib import Path
import shutil
import sys

ARCHIVO = Path('templates') / 'index.html'
MARCADOR = 'function extraerDatosVisualesFactura(item)'

if not ARCHIVO.exists():
    print(f'ERROR: no encuentro {ARCHIVO}. Ejecuta este instalador desde la carpeta SincronizadorWeb.')
    sys.exit(1)

texto = ARCHIVO.read_text(encoding='utf-8')
if MARCADOR in texto:
    print('La vista compacta de montos ya está instalada. No se hicieron cambios.')
    sys.exit(0)

reemplazos = []

reemplazos.append((
"""        .montos-table { min-width: 800px; font-variant-numeric: tabular-nums; }\n        .montos-table th { position: sticky; top: 0; }\n        .montos-table td { padding: 10px 12px; }\n        .montos-table td:nth-child(n+3):nth-child(-n+5) { text-align: right; }\n        .montos-table th:nth-child(n+3):nth-child(-n+5) { text-align: right; }\n""",
"""        .montos-table { min-width: 980px; font-variant-numeric: tabular-nums; }\n        .montos-table th { position: sticky; top: 0; }\n        .montos-table td { padding: 10px 12px; }\n        .montos-table .col-numero { width: 72px; white-space: nowrap; }\n        .montos-table .col-nombre { min-width: 210px; }\n        .montos-table .col-ubicacion { min-width: 220px; }\n        .montos-table .col-ot { min-width: 170px; }\n        .montos-table .monto-num { text-align: right; white-space: nowrap; }\n        .montos-table.ocultar-ot .col-ot { display: none; }\n        #montosToggleOT[aria-pressed=\"false\"] { opacity: .78; }\n"""
))

reemplazos.append((
"""                        <thead><tr><th>Carpeta / factura</th><th>OT</th><th>Neto</th><th>IVA</th><th>Total</th><th>Estado / acciones</th></tr></thead>\n""",
"""                        <thead><tr><th class=\"col-numero\">N°</th><th class=\"col-nombre\">Nombre</th><th class=\"col-ubicacion\">Ubicación</th><th class=\"col-ot\">OT</th><th>Neto</th><th>IVA</th><th>Total</th><th>Estado / acciones</th></tr></thead>\n"""
))

reemplazos.append((
"""                <button type=\"button\" class=\"btn-outline\" id=\"montosRefrescar\" onclick=\"refrescarTodosMontos()\">↻ Actualizar</button>\n""",
"""                <button type=\"button\" class=\"btn-outline\" id=\"montosToggleOT\" onclick=\"toggleColumnaOT()\" aria-pressed=\"false\">Mostrar OT</button>\n                <button type=\"button\" class=\"btn-outline\" id=\"montosRefrescar\" onclick=\"refrescarTodosMontos()\">↻ Actualizar</button>\n"""
))

reemplazos.append((
"""        const dineroCLP = n => '$ ' + Number(n).toLocaleString('es-CL', {maximumFractionDigits:0});\n        let montosEnCarga = false;\n        function cerrarModalMontos() { document.getElementById('modalMontos').style.display='none'; }\n""",
"""        const dineroCLP = n => '$ ' + Number(n).toLocaleString('es-CL', {maximumFractionDigits:0});\n        let montosEnCarga = false;\n        const MONTOS_OT_KEY = 'sincronizador_montos_mostrar_ot';\n\n        function extraerDatosVisualesFactura(item) {\n            const fuente = String(item.archivo || item.carpeta || '').replace(/\\.[^.]+$/, '').trim();\n            const m = fuente.match(/^F\\s*N\\s*[°º]\\s*([0-9]+(?:\\s*[-–]\\s*[0-9]+)?)\\s*(.*)$/i);\n            const numero = m ? m[1].replace(/\\s+/g, '') : (item.numero || '—');\n            let resto = m ? m[2].trim() : '';\n\n            // Si el archivo sólo trae el número, usar el nombre de la carpeta como respaldo.\n            if (!resto && item.carpeta) {\n                const carpeta = String(item.carpeta).trim();\n                const mc = carpeta.match(/^F\\s*N\\s*[°º]\\s*[0-9]+(?:\\s*[-–]\\s*[0-9]+)?\\s*(.*)$/i);\n                resto = mc ? mc[1].trim() : carpeta;\n            }\n\n            const partes = resto.split(',').map(v => v.trim()).filter(Boolean);\n            const nombre = partes.length ? partes.shift() : '—';\n            const ubicacion = partes.length ? partes.join(', ') : '—';\n            return { numero, nombre, ubicacion };\n        }\n\n        function aplicarVisibilidadOT() {\n            const tabla = document.querySelector('#modalMontos .montos-table');\n            const boton = document.getElementById('montosToggleOT');\n            if (!tabla || !boton) return;\n            const mostrar = localStorage.getItem(MONTOS_OT_KEY) === '1';\n            tabla.classList.toggle('ocultar-ot', !mostrar);\n            boton.textContent = mostrar ? 'Ocultar OT' : 'Mostrar OT';\n            boton.setAttribute('aria-pressed', mostrar ? 'true' : 'false');\n        }\n\n        function toggleColumnaOT() {\n            const mostrarAhora = localStorage.getItem(MONTOS_OT_KEY) === '1';\n            localStorage.setItem(MONTOS_OT_KEY, mostrarAhora ? '0' : '1');\n            aplicarVisibilidadOT();\n        }\n\n        function cerrarModalMontos() { document.getElementById('modalMontos').style.display='none'; }\n"""
))

reemplazos.append((
"""            document.getElementById('modalMontos').style.display='flex';\n            await cargarMontos();\n""",
"""            document.getElementById('modalMontos').style.display='flex';\n            aplicarVisibilidadOT();\n            await cargarMontos();\n"""
))

reemplazos.append((
"""                    const n=item.montos;\n                    const nombre=celda(item.carpeta+' / '+item.archivo);\n                    nombre.title=item.archivo;\n                    tr.append(nombre, celda(item.ot || '—'), celda(n && item.estado !== 'duplicado' ? dineroCLP(n.neto) : '—'),\n                        celda(n && item.estado !== 'duplicado' ? dineroCLP(n.iva) : '—'),\n                        celda(n && item.estado !== 'duplicado' ? dineroCLP(n.total) : '—'));\n""",
"""                    const n=item.montos;\n                    const datosVisuales=extraerDatosVisualesFactura(item);\n                    const numero=celda(datosVisuales.numero); numero.className='col-numero'; numero.title=item.archivo || '';\n                    const nombre=celda(datosVisuales.nombre); nombre.className='col-nombre'; nombre.title=item.archivo || '';\n                    const ubicacion=celda(datosVisuales.ubicacion); ubicacion.className='col-ubicacion'; ubicacion.title=item.carpeta || '';\n                    const ot=celda(item.ot || '—'); ot.className='col-ot';\n                    const neto=celda(n && item.estado !== 'duplicado' ? dineroCLP(n.neto) : '—'); neto.className='monto-num';\n                    const iva=celda(n && item.estado !== 'duplicado' ? dineroCLP(n.iva) : '—'); iva.className='monto-num';\n                    const total=celda(n && item.estado !== 'duplicado' ? dineroCLP(n.total) : '—'); total.className='monto-num';\n                    tr.append(numero, nombre, ubicacion, ot, neto, iva, total);\n"""
))

reemplazos.append((
"""                    const fila=document.createElement('tr');const td=document.createElement('td');td.colSpan=6;td.textContent='No hay archivos cuyo nombre comience por F N° y sean PDF o imagen.';fila.appendChild(td);tbody.appendChild(fila);\n""",
"""                    const fila=document.createElement('tr');const td=document.createElement('td');td.colSpan=8;td.textContent='No hay archivos cuyo nombre comience por F N° y sean PDF o imagen.';fila.appendChild(td);tbody.appendChild(fila);\n"""
))

for viejo, nuevo in reemplazos:
    if viejo not in texto:
        print('ERROR: no encontré uno de los bloques esperados. No se modificó el archivo.')
        print('Esto probablemente significa que tu index.html ya cambió respecto de la versión instalada.')
        sys.exit(2)
    texto = texto.replace(viejo, nuevo, 1)

backup = ARCHIVO.with_suffix('.html.bak_antes_vista_compacta')
shutil.copy2(ARCHIVO, backup)
ARCHIVO.write_text(texto, encoding='utf-8')

print('OK: vista compacta instalada.')
print(f'Backup: {backup}')
print('Cambios: N°, Nombre, Ubicación, OT ocultable, Neto, IVA, Total y Estado/acciones.')
print('La columna OT queda oculta por defecto y se puede mostrar con el botón "Mostrar OT".')
