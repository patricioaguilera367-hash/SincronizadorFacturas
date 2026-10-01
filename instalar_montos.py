"""Ejecutar UNA vez desde la raíz de SincronizadorWeb, sobre feature/montos-facturas.
Hace backup de servidor.py y realiza modificaciones localizadas y verificadas.
NO reemplaza ruta_aprobada ni ningún algoritmo de sincronización.
"""
from pathlib import Path
from datetime import datetime
import ast
import sys

ruta = Path(__file__).resolve().parent / 'servidor.py'
if not ruta.exists():
    sys.exit('ERROR: falta servidor.py en esta carpeta; copia este instalador junto a él.')
original = ruta.read_text(encoding='utf-8-sig')
if 'registrar_rutas_montos(app' in original:
    sys.exit('Los endpoints de montos ya están instalados; no se hicieron cambios.')

# Guardas: no modificar versiones desconocidas del backend.
requisitos = [
    "app = Flask(__name__)",
    'def subir_archivo():',
    'file.save(destino)',
    "['ot.txt', '.sync_state.json', 'ignorado.txt']",
    "['.sync_state.json', 'ignorado.txt']",
    "if __name__ == '__main__':",
]
for texto in requisitos:
    if texto not in original:
        sys.exit(f'ERROR: el backend no contiene {texto!r}. No se hizo ningún cambio.')

nuevo = original.replace(
    "['ot.txt', '.sync_state.json', 'ignorado.txt']",
    "['ot.txt', '.sync_state.json', 'ignorado.txt', '.factura_montos.json']",
)
nuevo = nuevo.replace(
    "['.sync_state.json', 'ignorado.txt']",
    "['.sync_state.json', 'ignorado.txt', '.factura_montos.json']",
)
# Bloquear que se cargue el nombre reservado, evitando sobrescribir metadata.
assert nuevo.count('file.save(destino)') == 1
nuevo = nuevo.replace('        file.save(destino)',
    "        if nombre.lower() == '.factura_montos.json':\n"
    "            return jsonify({'error': 'Nombre reservado.'}), 400\n"
    "        file.save(destino)\n"
    "        from factura_montos import es_factura, actualizar_archivo_cargado\n"
    "        if es_factura(nombre):\n"
    "            try:\n"
    "                actualizar_archivo_cargado(ruta, destino)\n"
    "            except Exception:\n"
    "                app.logger.exception('La factura se cargó, pero no se pudo extraer el monto')")
nuevo = nuevo.replace("if __name__ == '__main__':",
    "# Módulo opcional e independiente para importes de facturas.\n"
    "from factura_montos import registrar_rutas_montos\n"
    "registrar_rutas_montos(app, BASE_FACTURAS, ruta_factura_aprobada, ruta_aprobada)\n\n"
    "if __name__ == '__main__':")
try:
    ast.parse(nuevo, filename=str(ruta))
except SyntaxError as exc:
    sys.exit(f'ERROR: se canceló la instalación porque la versión modificada no compila: {exc}')
backup = ruta.with_name('servidor.antes_montos.' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.bak')
backup.write_text(original, encoding='utf-8')
ruta.write_text(nuevo, encoding='utf-8')
print('Instalación terminada. Backup:', backup.name)
print('Verifica con: python -m py_compile servidor.py')
