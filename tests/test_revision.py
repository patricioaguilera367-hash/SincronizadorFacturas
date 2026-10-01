import json
import os
import tempfile
import unittest
from pathlib import Path

from flask import Flask

from revision import detectar_semana, registrar_rutas_revision


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


class RevisionTests(unittest.TestCase):
    def test_detecta_carpeta_sin_factura_y_sin_monto(self):
        with tempfile.TemporaryDirectory() as d:
            semana = Path(d) / 'Semana 1'
            carpeta = semana / 'Persona natural'
            carpeta.mkdir(parents=True)
            (carpeta / 'comprobante.pdf').write_bytes(b'x')

            data = detectar_semana(str(semana))
            codigos = {x['codigo'] for x in data['items']}
            self.assertIn('sin_factura_sin_monto', codigos)
            self.assertEqual(data['warning'], 1)

    def test_cobro_manual_valido_no_es_anomalia(self):
        with tempfile.TemporaryDirectory() as d:
            semana = Path(d) / 'Semana 1'
            carpeta = semana / 'Abono'
            carpeta.mkdir(parents=True)
            (carpeta / '.cobro_manual.json').write_text(json.dumps({
                'version': 1,
                'detalle': 'Abono',
                'tipo': 'abono',
                'monto': 50000,
                'estado': 'pendiente',
            }), encoding='utf-8')

            data = detectar_semana(str(semana))
            self.assertEqual(data['items'], [])

    def test_factura_con_metadata_manual_residual_se_reporta_sin_borrar(self):
        with tempfile.TemporaryDirectory() as d:
            semana = Path(d) / 'Semana 1'
            carpeta = semana / 'Caso mixto'
            carpeta.mkdir(parents=True)
            (carpeta / 'F N°12.pdf').write_bytes(b'pdf')
            manual = carpeta / '.cobro_manual.json'
            manual.write_text(json.dumps({'monto': 10000, 'tipo': 'transferencia'}), encoding='utf-8')

            data = detectar_semana(str(semana))
            self.assertIn('cobro_manual_con_factura', {x['codigo'] for x in data['items']})
            self.assertTrue(manual.exists())
            self.assertFalse((carpeta / '.factura_montos.json').exists())

    def test_detecta_numero_factura_duplicado_sin_analizar_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            semana = Path(d) / 'Semana 1'
            carpeta = semana / 'Duplicada'
            carpeta.mkdir(parents=True)
            (carpeta / 'F N°77.pdf').write_bytes(b'no-es-pdf')
            (carpeta / 'F N°77 copia.pdf').write_bytes(b'no-es-pdf')

            data = detectar_semana(str(semana))
            items = [x for x in data['items'] if x['codigo'] == 'factura_duplicada']
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]['severidad'], 'danger')
            self.assertFalse((carpeta / '.factura_montos.json').exists())

    def test_detecta_sync_state_invalido(self):
        with tempfile.TemporaryDirectory() as d:
            semana = Path(d) / 'Semana 1'
            carpeta = semana / 'Factura'
            carpeta.mkdir(parents=True)
            (carpeta / 'F N°1.pdf').write_bytes(b'x')
            (carpeta / '.sync_state.json').write_text('{roto', encoding='utf-8')

            data = detectar_semana(str(semana))
            self.assertIn('sync_state_invalido', {x['codigo'] for x in data['items']})

    def test_endpoint_rechaza_escape_y_devuelve_revision(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            semana = raiz / 'Semana 1'
            (semana / 'Sin factura').mkdir(parents=True)

            app = Flask(__name__)
            app.config.update(TESTING=True)
            registrar_rutas_revision(app, str(raiz), ruta_segura)
            client = app.test_client()

            ok = client.get('/api/revision', query_string={'semana': semana.name})
            self.assertEqual(ok.status_code, 200)
            self.assertEqual(ok.get_json()['total'], 1)

            escape = client.get('/api/revision', query_string={'semana': '..'})
            self.assertEqual(escape.status_code, 400)


if __name__ == '__main__':
    unittest.main()
