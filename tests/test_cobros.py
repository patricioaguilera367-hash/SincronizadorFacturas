import json
import os
import tempfile
import unittest
from pathlib import Path

from flask import Flask

from cobros import METADATA_COBRO, registrar_rutas_cobros


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


class CobrosCarpetaTests(unittest.TestCase):
    def crear_cliente(self, raiz):
        app = Flask(__name__)
        app.config.update(TESTING=True)
        registrar_rutas_cobros(app, str(raiz), ruta_segura)
        return app.test_client()

    def test_carpeta_sin_factura_aparece_aunque_no_tenga_monto(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            semana = raiz / '59 Facturas semana 02OCT26'
            manual = semana / 'Persona natural - anticipo'
            factura = semana / 'Factura normal'
            manual.mkdir(parents=True)
            factura.mkdir()
            (factura / 'F N°123.pdf').write_bytes(b'pdf')

            client = self.crear_cliente(raiz)
            response = client.get('/api/cobros', query_string={'semana': semana.name})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(len(data['items']), 1)
            self.assertEqual(data['items'][0]['carpeta'], manual.name)
            self.assertFalse(data['items'][0]['configurado'])
            self.assertIsNone(data['items'][0]['monto'])
            self.assertEqual(data['sin_monto'], 1)
            self.assertEqual(data['pendiente_total'], 0)

    def test_guardar_monto_en_carpeta_existente_no_crea_otra(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            semana = raiz / 'Semana 1'
            carpeta = semana / 'Juan Perez pago'
            carpeta.mkdir(parents=True)
            (carpeta / 'comprobante.pdf').write_bytes(b'x')

            client = self.crear_cliente(raiz)
            response = client.post('/api/cobros/guardar', json={
                'semana': semana.name,
                'carpeta_actual': carpeta.name,
                'carpeta': carpeta.name,
                'detalle': 'Transferencia persona natural',
                'tipo': 'transferencia',
                'monto': 125000,
            })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(carpeta.exists())
            self.assertEqual(len([x for x in semana.iterdir() if x.is_dir()]), 1)

            metadata = carpeta / METADATA_COBRO
            self.assertTrue(metadata.exists())
            guardado = json.loads(metadata.read_text(encoding='utf-8'))
            self.assertEqual(guardado['monto'], 125000)
            self.assertEqual(response.get_json()['pendiente_total'], 125000)

    def test_guardar_cobro_nuevo_crea_su_carpeta(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            semana = raiz / 'Semana 1'
            semana.mkdir()
            client = self.crear_cliente(raiz)

            response = client.post('/api/cobros/guardar', json={
                'semana': semana.name,
                'carpeta': 'Abono proveedor X',
                'detalle': 'Primer abono',
                'tipo': 'abono',
                'monto': 80000,
            })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.get_json()['creada'])
            carpeta = semana / 'Abono proveedor X'
            self.assertTrue(carpeta.is_dir())
            self.assertTrue((carpeta / METADATA_COBRO).is_file())

    def test_realizado_deja_de_sumar_y_limpiar_conserva_carpeta(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            semana = raiz / 'Semana 1'
            semana.mkdir()
            client = self.crear_cliente(raiz)

            client.post('/api/cobros/guardar', json={
                'semana': semana.name,
                'carpeta': 'Transferencia pendiente',
                'detalle': '',
                'tipo': 'transferencia',
                'monto': 60000,
            })
            carpeta = semana / 'Transferencia pendiente'

            realizado = client.post('/api/cobros/estado', json={
                'semana': semana.name,
                'carpeta': carpeta.name,
                'estado': 'realizado',
            })
            self.assertEqual(realizado.status_code, 200)
            self.assertEqual(realizado.get_json()['pendiente_total'], 0)
            self.assertEqual(realizado.get_json()['realizado_total'], 60000)

            limpio = client.post('/api/cobros/limpiar', json={
                'semana': semana.name,
                'carpeta': carpeta.name,
            })
            self.assertEqual(limpio.status_code, 200)
            self.assertTrue(carpeta.is_dir())
            self.assertFalse((carpeta / METADATA_COBRO).exists())
            item = limpio.get_json()['items'][0]
            self.assertFalse(item['configurado'])
            self.assertIsNone(item['monto'])

    def test_si_aparece_factura_la_carpeta_sale_del_cobro_manual(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            semana = raiz / 'Semana 1'
            semana.mkdir()
            client = self.crear_cliente(raiz)

            client.post('/api/cobros/guardar', json={
                'semana': semana.name,
                'carpeta': 'Pendiente de factura',
                'detalle': '',
                'tipo': 'transferencia',
                'monto': 90000,
            })
            carpeta = semana / 'Pendiente de factura'
            (carpeta / 'F N°77.pdf').write_bytes(b'pdf')

            listado = client.get('/api/cobros', query_string={'semana': semana.name})
            self.assertEqual(listado.status_code, 200)
            self.assertEqual(listado.get_json()['items'], [])
            self.assertEqual(listado.get_json()['pendiente_total'], 0)

    def test_no_permite_usar_factura_como_cobro_manual(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            semana = raiz / 'Semana 1'
            carpeta = semana / 'Factura'
            carpeta.mkdir(parents=True)
            (carpeta / 'F N°6.pdf').write_bytes(b'pdf')
            client = self.crear_cliente(raiz)

            response = client.post('/api/cobros/guardar', json={
                'semana': semana.name,
                'carpeta_actual': carpeta.name,
                'carpeta': carpeta.name,
                'detalle': '',
                'tipo': 'transferencia',
                'monto': 1000,
            })
            self.assertEqual(response.status_code, 409)
            self.assertFalse((carpeta / METADATA_COBRO).exists())

    def test_ui_expresa_relacion_carpeta_monto(self):
        template = (Path(__file__).parents[1] / 'templates' / 'index.html').read_text(encoding='utf-8')
        for token in (
            'Carpetas sin factura · cobros manuales',
            'Nombre de carpeta',
            'carpeta_actual',
            '/api/cobros/limpiar',
            'TOTAL A COBRAR',
            "abrirCarpeta('facturas')",
            'Ctrl + click para abrir la carpeta',
        ):
            self.assertIn(token, template)


if __name__ == '__main__':
    unittest.main()
