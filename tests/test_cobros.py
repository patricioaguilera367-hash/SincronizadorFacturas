import json
import os
import tempfile
import unittest
from pathlib import Path

from flask import Flask

from cobros import (
    METADATA_COBROS,
    _item_desde_payload,
    _leer,
    _presentar,
    registrar_rutas_cobros,
)


def ruta_segura(raiz, *partes):
    try:
        raiz_real = os.path.realpath(raiz)
        candidata = os.path.realpath(os.path.join(raiz_real, *partes))
        relativa = os.path.relpath(candidata, raiz_real)
        if relativa == '..' or relativa.startswith('..' + os.sep):
            return None
        return candidata
    except (OSError, ValueError, TypeError):
        return None


class CobrosTests(unittest.TestCase):
    def test_presentar_suma_solo_pendientes(self):
        a = _item_desde_payload({
            'nombre': 'Persona A', 'detalle': 'Transferencia', 'ot': '',
            'tipo': 'transferencia', 'monto': 100000,
        })
        b = _item_desde_payload({
            'nombre': 'Persona B', 'detalle': 'Abono', 'ot': '206_NT_591',
            'tipo': 'abono', 'monto': 50000, 'estado': 'realizado',
        })
        resumen = _presentar({'items': [a, b]})
        self.assertEqual(resumen['pendiente_total'], 100000)
        self.assertEqual(resumen['realizado_total'], 50000)
        self.assertEqual(resumen['pendientes'], 1)
        self.assertEqual(resumen['realizados'], 1)

    def test_crud_http_guarda_en_carpeta_semanal(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            semana = raiz / '59 Facturas semana 02OCT26'
            semana.mkdir()

            app = Flask(__name__)
            app.config.update(TESTING=True)
            registrar_rutas_cobros(app, str(raiz), ruta_segura)
            client = app.test_client()

            creado = client.post('/api/cobros/guardar', json={
                'semana': semana.name,
                'nombre': 'Juan Perez',
                'detalle': 'Pago persona natural',
                'ot': '206_NT_591',
                'tipo': 'transferencia',
                'monto': 125000,
            })
            self.assertEqual(creado.status_code, 200)
            data = creado.get_json()
            self.assertEqual(data['pendiente_total'], 125000)
            self.assertEqual(len(data['items']), 1)
            identificador = data['items'][0]['id']

            metadata = semana / METADATA_COBROS
            self.assertTrue(metadata.exists())
            guardado = json.loads(metadata.read_text(encoding='utf-8'))
            self.assertEqual(guardado['items'][0]['nombre'], 'Juan Perez')

            realizado = client.post('/api/cobros/estado', json={
                'semana': semana.name,
                'id': identificador,
                'estado': 'realizado',
            })
            self.assertEqual(realizado.status_code, 200)
            self.assertEqual(realizado.get_json()['pendiente_total'], 0)
            self.assertEqual(realizado.get_json()['realizado_total'], 125000)

            eliminado = client.post('/api/cobros/eliminar', json={
                'semana': semana.name,
                'id': identificador,
            })
            self.assertEqual(eliminado.status_code, 200)
            self.assertEqual(eliminado.get_json()['items'], [])

    def test_validacion_rechaza_montos_y_semanas_invalidas(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            semana = raiz / 'Semana 1'
            semana.mkdir()
            app = Flask(__name__)
            app.config.update(TESTING=True)
            registrar_rutas_cobros(app, str(raiz), ruta_segura)
            client = app.test_client()

            invalido = client.post('/api/cobros/guardar', json={
                'semana': semana.name,
                'nombre': 'Persona',
                'tipo': 'transferencia',
                'monto': -1,
            })
            self.assertEqual(invalido.status_code, 400)
            self.assertEqual(_leer(str(semana))['items'], [])

            escape = client.get('/api/cobros', query_string={'semana': '..'})
            self.assertEqual(escape.status_code, 400)

    def test_ui_contiene_navegacion_y_cobros_compactos(self):
        template = (Path(__file__).parents[1] / 'templates' / 'index.html').read_text(encoding='utf-8')
        for token in (
            "abrirCarpeta('facturas')",
            "abrirCarpeta('semana')",
            "Ctrl + click para abrir la carpeta",
            'cobrosForm',
            'Transferencias / abonos sin factura',
            'TOTAL A COBRAR',
            'V1.2 compact-ops',
        ):
            self.assertIn(token, template)


if __name__ == '__main__':
    unittest.main()
