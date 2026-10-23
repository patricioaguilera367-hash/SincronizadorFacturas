"""Comparación local reproducible: python tests/benchmark_nas.py.

Cuenta operaciones potencialmente remotas para 2 semanas simuladas de 30
facturas cada una. NO sustituye una medición real de latencia en el NAS SMB.
"""

import collections
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import types
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import servidor  # noqa: E402


def cargar_version_anterior():
    modulo_diagnostico = types.ModuleType('diagnostico_sync')
    modulo_diagnostico.registrar_diagnostico_ot = lambda *args: None
    sys.modules['diagnostico_sync'] = modulo_diagnostico
    modulo = types.ModuleType('servidor_v112')
    fuente = subprocess.check_output(
        ['git', 'show', 'fea0f01:servidor.py'], text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    exec(compile(fuente, 'servidor_v112.py', 'exec'), modulo.__dict__)
    return modulo


def crear_datos(raiz):
    facturas = raiz / 'facturas'
    obras = raiz / 'obras'
    obras.mkdir()
    semanas = []
    for numero in range(2):
        semana = facturas / f'Semana {numero + 1}'
        semanas.append(semana.name)
        for i in range(30):
            carpeta = semana / f'Factura {i:02}'
            carpeta.mkdir(parents=True)
            ot = carpeta / '.OT.txt'
            ot.write_text('OT1', encoding='utf-8')
            archivos = {}
            for j in range(4):
                ruta = carpeta / f'archivo{j}.pdf'
                ruta.write_bytes(b'abc' * 100)
                stat = ruta.stat()
                archivos[ruta.name] = {'size': stat.st_size, 'mtime': int(stat.st_mtime)}
            # Los estados heredados incluían por error el archivo .OT.txt.
            stat = ot.stat()
            archivos['.OT.txt'] = {'size': stat.st_size, 'mtime': int(stat.st_mtime)}
            (carpeta / '.sync_state.json').write_text(
                json.dumps({'ots': ['OT1'], 'archivos': archivos}), encoding='utf-8',
            )
    return facturas, obras, semanas


def medir(modulo, semanas):
    operaciones = collections.Counter()
    nombres = ('realpath', 'getsize', 'getmtime')
    originales = {nombre: getattr(os.path, nombre) for nombre in nombres}
    originales['listdir'] = os.listdir
    originales['scandir'] = os.scandir

    def contar(nombre):
        def llamada(*args, **kwargs):
            operaciones[nombre] += 1
            return originales[nombre](*args, **kwargs)
        return llamada

    inicio = time.perf_counter()
    with patch('os.path.realpath', side_effect=contar('realpath')), \
         patch('os.path.getsize', side_effect=contar('getsize')), \
         patch('os.path.getmtime', side_effect=contar('getmtime')), \
         patch('os.listdir', side_effect=contar('listdir')), \
         patch('os.scandir', side_effect=contar('scandir')):
        cliente = modulo.app.test_client()
        respuestas = [cliente.get('/api/facturas', query_string={'semana': s}) for s in semanas]
    assert all(respuesta.status_code == 200 for respuesta in respuestas)
    assert sum(len(respuesta.get_json()) for respuesta in respuestas) == 60
    datos = [sorted(r.get_json(), key=lambda row: row['nombre']) for r in respuestas]
    return round((time.perf_counter() - inicio) * 1000, 1), operaciones, datos


if __name__ == '__main__':
    original = cargar_version_anterior()
    with TemporaryDirectory() as directorio:
        facturas, obras, semanas = crear_datos(Path(directorio))
        for modulo in (original, servidor):
            modulo.BASE_FACTURAS = str(facturas)
            modulo.BASE_OBRAS = str(obras)
        referencia = None
        for nombre, modulo in [('v1.1.2', original), ('optimizada', servidor)]:
            duracion, operaciones, datos = medir(modulo, semanas)
            if referencia is None:
                referencia = datos
            else:
                assert datos == referencia, 'El API de facturas cambió su respuesta.'
            print(f'{nombre}: {duracion} ms locales; llamadas: {dict(operaciones)}')
        print('Respuestas JSON equivalentes en los 60 registros.')
