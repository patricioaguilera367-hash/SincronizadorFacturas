"""Diagnóstico TEMPORAL y SOLO LECTURA para la OT 206/NT-591.

Instalación en el archivo Python que define Flask, justo ANTES del bloque
`if __name__ == '__main__':`:

    from diagnostico_sync import registrar_diagnostico_ot
    registrar_diagnostico_ot(app, BASE_OBRAS, ruta_aprobada)

Reinicia INICIAR_APP.bat y abre en el MISMO PC:
    http://127.0.0.1:5001/api/diagnostico_ot

Para comprobar además la validación de una factura concreta:
    http://127.0.0.1:5001/api/diagnostico_ot?factura=NOMBRE_REAL_DE_LA_FACTURA

No crea, elimina ni modifica carpetas ni archivos. El endpoint rechaza
peticiones que no provengan del propio equipo. Retira la importación y
este módulo una vez terminado el diagnóstico.
"""

import getpass
import os
import stat
import subprocess
import sys
import time

from flask import jsonify, request

OT_PRUEBA = "206/NT-591"
CARPETA_PRUEBA = "206_NT_591"
SUBCARPETA_DESTINO = "Pensiones y almuerzos"


def registrar_diagnostico_ot(app, base_obras, ruta_aprobada):
    @app.route('/api/diagnostico_ot', methods=['GET'])
    def diagnostico_ot_temporal():
        # La app escucha en 0.0.0.0; NO exponer diagnósticos del servidor a la LAN.
        if request.remote_addr not in ('127.0.0.1', '::1'):
            return jsonify({'error': 'Diagnóstico accesible solamente desde este PC.'}), 403

        factura = request.args.get('factura', '')
        if factura and (factura in ('.', '..') or '/' in factura or '\\' in factura
                        or os.path.isabs(factura) or len(factura) > 200):
            return jsonify({'error': 'Nombre de factura inválido.'}), 400

        pasos = []

        def probar(nombre, funcion):
            print(f'[DIAG_OT] INICIO {nombre}', flush=True)
            inicio = time.perf_counter()
            try:
                valor = funcion()
                paso = {
                    'paso': nombre,
                    'resultado': 'OK' if valor is not None else 'DEVOLVIÓ NONE',
                    'valor': valor,
                    'segundos': round(time.perf_counter() - inicio, 3),
                }
            except Exception as exc:
                paso = {
                    'paso': nombre,
                    'resultado': 'EXCEPCIÓN',
                    'tipo': type(exc).__name__,
                    'mensaje': str(exc),
                    'winerror': getattr(exc, 'winerror', None),
                    'errno': getattr(exc, 'errno', None),
                    'segundos': round(time.perf_counter() - inicio, 3),
                }
            pasos.append(paso)
            print(f'[DIAG_OT] FIN {nombre}: {paso}', flush=True)
            return paso.get('valor') if paso['resultado'] == 'OK' else None

        def identidad_real():
            proc = subprocess.run(['whoami'], capture_output=True, text=True,
                                  timeout=5, check=True)
            return proc.stdout.strip()

        def metadatos(ruta):
            s = os.stat(ruta)
            return {'es_directorio': stat.S_ISDIR(s.st_mode)}

        def listar_uno(ruta):
            # Acceder al directorio sin listar todas sus carpetas ni recorrerlo.
            with os.scandir(ruta) as entradas:
                next(entradas, None)
            return 'LECTURA_OK'

        contexto = {
            'ot': OT_PRUEBA,
            'carpeta_esperada': CARPETA_PRUEBA,
            'python': sys.executable,
            'usuario_entorno_NO_AUTORITATIVO': getpass.getuser(),
            'base_obras': base_obras,
            'factura_opcional': factura or None,
            'escritura_realizada': False,
        }
        probar('identidad_windows_del_proceso_flask', identidad_real)
        probar('base_obras_os_stat', lambda: metadatos(base_obras))
        probar('base_obras_scandir', lambda: listar_uno(base_obras))

        ruta_directa = os.path.join(base_obras, CARPETA_PRUEBA)
        probar('ot_ruta_directa_os_stat', lambda: metadatos(ruta_directa))
        probar('ot_ruta_directa_scandir', lambda: listar_uno(ruta_directa))
        ruta_validada = probar('ot_ruta_aprobada',
                               lambda: ruta_aprobada(base_obras, CARPETA_PRUEBA))
        if ruta_validada:
            probar('ot_ruta_validada_os_stat', lambda: metadatos(ruta_validada))
            probar('ot_ruta_validada_scandir', lambda: listar_uno(ruta_validada))
            parent = probar('destino_padre_ruta_aprobada',
                            lambda: ruta_aprobada(ruta_validada, SUBCARPETA_DESTINO))
            if parent:
                # Si la subcarpeta no existe, FileNotFoundError es esperable.
                probar('destino_padre_ya_existe', lambda: os.path.isdir(parent))
                if os.path.isdir(parent):
                    probar('destino_padre_os_stat', lambda: metadatos(parent))
                    probar('destino_padre_scandir', lambda: listar_uno(parent))
                if factura:
                    probar('destino_final_factura_ruta_aprobada',
                            lambda: ruta_aprobada(ruta_validada,
                                                 SUBCARPETA_DESTINO, factura))
        return jsonify({'contexto': contexto, 'pasos': pasos})
