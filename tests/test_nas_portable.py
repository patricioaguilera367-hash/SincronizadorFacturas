"""La optimización SMB debe preservar snapshots, permisos y JSON de portable V1.2."""

import json
import os
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import servidor
from cache_runtime import snapshot_semanas


class PortableNasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.obras = self.root / 'obras'
        self.obras.mkdir()
        self.facturas = self.root / 'facturas'
        self.semana = self.facturas / '1 Facturas semana 23OCT26'
        self.factura = self.semana / 'Empresa A'
        self.factura.mkdir(parents=True)
        (self.factura / '.OT.txt').write_text('OT1', encoding='utf-8')
        (self.factura / 'comprobante.pdf').write_bytes(b'factura')
        self.original = servidor.BASE_FACTURAS, servidor.BASE_OBRAS
        servidor.BASE_FACTURAS, servidor.BASE_OBRAS = str(self.facturas), str(self.obras)
        servidor.app.config.update(TESTING=True)
        self.client = servidor.app.test_client()

    def tearDown(self):
        servidor.BASE_FACTURAS, servidor.BASE_OBRAS = self.original
        self.tmp.cleanup()

    def test_existing_hidden_ot_remains_untouched_during_read(self):
        with patch.object(servidor, '_ocultar_archivo_windows') as hide:
            response = self.client.get('/api/facturas', query_string={'semana': self.semana.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]['ot_content'], 'OT1')
        hide.assert_not_called()

    def test_factura_has_one_directory_scan_and_one_state_read(self):
        servidor.actualizar_estado_sync(str(self.factura), ['OT1'])
        real_scandir, real_open = os.scandir, open
        scanned, state_reads = [], []

        def scandir(path):
            if os.fspath(path) == str(self.factura):
                scanned.append(path)
            return real_scandir(path)

        def tracked_open(path, mode='r', *args, **kwargs):
            if os.fspath(path) == str(self.factura / '.sync_state.json') and 'r' in mode:
                state_reads.append(path)
            return real_open(path, mode, *args, **kwargs)

        with patch.object(servidor.os, 'scandir', side_effect=scandir), patch('builtins.open', side_effect=tracked_open):
            response = self.client.get('/api/facturas', query_string={'semana': self.semana.name})
        self.assertEqual(response.get_json()[0]['badge_class'], 'badge-success')
        self.assertEqual(len(scanned), 1)
        self.assertEqual(len(state_reads), 1)

    def test_documents_skip_internal_manual_charge_and_hidden_ot(self):
        (self.factura / '.cobro_manual.json').write_text('{}', encoding='utf-8')
        servidor.actualizar_estado_sync(str(self.factura), ['OT1'])
        state = json.loads((self.factura / '.sync_state.json').read_text(encoding='utf-8'))
        self.assertEqual(set(state['archivos']), {'comprobante.pdf'})

    def test_reading_multiple_facturas_is_bounded_parallel_and_ordered(self):
        for nombre in ('Empresa B', 'Empresa C', 'Empresa D'):
            (self.semana / nombre).mkdir()
        gate = threading.Barrier(4, timeout=3)
        real = servidor._detalle_factura

        def concurrente(ruta, nombre):
            gate.wait()
            return real(ruta, nombre)

        with patch.object(servidor, '_detalle_factura', side_effect=concurrente):
            respuesta = self.client.get('/api/facturas', query_string={'semana': self.semana.name})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual([fila['nombre'] for fila in respuesta.get_json()],
                         ['Empresa A', 'Empresa B', 'Empresa C', 'Empresa D'])

    def test_partial_week_detail_does_not_delete_offline_snapshot_of_older_weeks(self):
        for numero in range(2, 7):
            (self.facturas / f'{numero} Facturas semana 23OCT26').mkdir()
        rapido = self.client.get('/api/semanas?rapido=1')
        self.assertEqual(rapido.status_code, 200)
        self.assertEqual(len(rapido.get_json()), 6)

        with patch.object(servidor, '_estado_semana', wraps=servidor._estado_semana) as details:
            limitado = self.client.get('/api/semanas?limite=2')
        self.assertEqual(limitado.status_code, 200)
        self.assertEqual([r['nombre'] for r in limitado.get_json()],
                         ['6 Facturas semana 23OCT26', '5 Facturas semana 23OCT26'])
        self.assertEqual(details.call_count, 2)
        self.assertEqual(len(snapshot_semanas(servidor._snapshot_path())), 6)

    def test_corrupt_sync_state_remains_an_error(self):
        (self.factura / '.sync_state.json').write_text('{mal', encoding='utf-8')
        respuesta = self.client.get('/api/facturas', query_string={'semana': self.semana.name})
        self.assertEqual(respuesta.get_json()[0]['badge_class'], 'badge-danger')

    def test_cached_week_uses_local_snapshot_without_contacting_nas(self):
        original = self.client.get('/api/facturas', query_string={'semana': self.semana.name})
        self.assertEqual(original.status_code, 200)

        with patch.object(servidor, '_comprobar_servidor', side_effect=AssertionError('NAS consulted')):
            with patch.object(servidor.os, 'scandir', side_effect=AssertionError('SMB scan')):
                cached = self.client.get('/api/facturas_cache', query_string={'semana': self.semana.name})

        self.assertEqual(cached.status_code, 200)
        self.assertEqual(cached.get_json(), original.get_json())
        self.assertEqual(cached.headers.get('X-Sincronizador-Cached'), '1')
        self.assertIsNone(cached.headers.get('X-Sincronizador-Offline'))

    def test_cached_week_rejects_invalid_names_and_unknown_weeks(self):
        invalid = self.client.get('/api/facturas_cache', query_string={'semana': '../otro'})
        absent = self.client.get('/api/facturas_cache', query_string={'semana': 'Semana sin snapshot'})
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(absent.status_code, 404)

    def test_invalid_sync_document_states_do_not_abort_whole_week(self):
        (self.factura / '.sync_state.json').write_text('{"estados": "no válido"}', encoding='utf-8')
        respuesta = self.client.get('/api/facturas', query_string={'semana': self.semana.name})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json()[0]['badge_class'], 'badge-danger')

    def test_diagnostic_header_breaks_down_backend_without_changing_json(self):
        servidor.actualizar_estado_sync(str(self.factura), ['OT1'])
        normal = self.client.get('/api/facturas', query_string={'semana': self.semana.name})
        perfilada = self.client.get('/api/facturas', query_string={'semana': self.semana.name, 'perf': '1'})

        self.assertEqual(normal.get_json(), perfilada.get_json())
        self.assertNotIn('X-Sincronizador-Diagnostico', normal.headers)
        datos = json.loads(perfilada.headers['X-Sincronizador-Diagnostico'])
        self.assertEqual(datos['facturas'], 1)
        for campo in ('conexion_ms', 'enumeracion_ms', 'procesamiento_ms',
                      'snapshot_ms', 'serializacion_ms', 'total_ms'):
            self.assertIsInstance(datos[campo], (float, int))
            self.assertGreaterEqual(datos[campo], 0)
        for campo in ('enumerar_archivos', 'leer_ot', 'leer_sync', 'evaluar_estado'):
            self.assertGreaterEqual(datos['operaciones_acumuladas_ms'][campo], 0)
        self.assertIn('Server-Timing', perfilada.headers)


if __name__ == '__main__':
    unittest.main()
