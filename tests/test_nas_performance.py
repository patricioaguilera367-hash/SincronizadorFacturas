"""Regresiones de rendimiento para carpetas de facturas en unidades SMB."""

import json
import os
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import servidor


class NasPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.facturas = root / 'facturas'
        self.obras = root / 'obras'
        self.factura = self.facturas / '1 Facturas semana 23OCT26' / 'Empresa A'
        self.factura.mkdir(parents=True)
        self.obras.mkdir()
        (self.factura / '.OT.txt').write_text('206/NT-591', encoding='utf-8')
        (self.factura / 'comprobante.pdf').write_bytes(b'factura')
        self.original_facturas, self.original_obras = servidor.BASE_FACTURAS, servidor.BASE_OBRAS
        servidor.BASE_FACTURAS, servidor.BASE_OBRAS = str(self.facturas), str(self.obras)
        servidor.app.config.update(TESTING=True)
        self.client = servidor.app.test_client()
        servidor._indice_ot.clear()

    def tearDown(self):
        servidor.BASE_FACTURAS, servidor.BASE_OBRAS = self.original_facturas, self.original_obras
        servidor._indice_ot.clear()
        self.tempdir.cleanup()

    def test_reading_existing_hidden_ot_does_not_rewrite_windows_attributes(self):
        with patch.object(servidor, '_ocultar_archivo_windows') as hide:
            self.assertEqual(servidor.ruta_ot_metadata(str(self.factura)), str(self.factura / '.OT.txt'))
        hide.assert_not_called()

    def test_sync_state_excludes_internal_metadata_files(self):
        servidor.actualizar_estado_sync(str(self.factura), ['206/NT-591'])
        state = json.loads((self.factura / '.sync_state.json').read_text(encoding='utf-8'))
        self.assertEqual(list(state['archivos']), ['comprobante.pdf'])
        self.assertEqual(servidor.evaluar_estado_sync(str(self.factura), '206/NT-591')[0], 'badge-success')

    def test_existing_states_with_hidden_metadata_remain_synced(self):
        servidor.actualizar_estado_sync(str(self.factura), ['206/NT-591'])
        metadata = self.factura / '.sync_state.json'
        state = json.loads(metadata.read_text(encoding='utf-8'))
        state['archivos']['.OT.txt'] = {'size': 10, 'mtime': 0}
        metadata.write_text(json.dumps(state), encoding='utf-8')
        self.assertEqual(servidor.evaluar_estado_sync(str(self.factura), '206/NT-591')[0], 'badge-success')

    def test_corrupt_state_still_shows_error_not_pending(self):
        (self.factura / '.sync_state.json').write_text('{invalido', encoding='utf-8')
        response = self.client.get('/api/facturas', query_string={'semana': self.factura.parent.name})
        self.assertEqual(response.get_json()[0]['badge_class'], 'badge-danger')

    def test_facturas_reads_state_once_and_scans_directory_once(self):
        servidor.actualizar_estado_sync(str(self.factura), ['206/NT-591'])
        original_scandir = os.scandir
        original_open = open
        original_exists = os.path.exists
        scans, state_reads, redundant_exists = [], [], []

        def scandir(path):
            if os.fspath(path) == str(self.factura):
                scans.append(path)
            return original_scandir(path)

        def tracked_open(path, mode='r', *args, **kwargs):
            if os.fspath(path) == str(self.factura / '.sync_state.json') and 'r' in mode:
                state_reads.append(path)
            return original_open(path, mode, *args, **kwargs)

        def exists(path):
            if os.path.dirname(os.fspath(path)) == str(self.factura):
                redundant_exists.append(path)
            return original_exists(path)

        with patch.object(servidor.os, 'scandir', side_effect=scandir), patch('builtins.open', side_effect=tracked_open), patch.object(servidor.os.path, 'exists', side_effect=exists):
            result = self.client.get('/api/facturas', query_string={'semana': self.factura.parent.name})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json()[0]['badge_class'], 'badge-success')
        self.assertEqual(len(scans), 1)
        self.assertEqual(len(state_reads), 1)
        self.assertEqual(redundant_exists, [])

    def test_detailed_weeks_can_check_only_recent_weeks(self):
        for number in range(2, 9):
            (self.facturas / f'{number} Facturas semana 23OCT26').mkdir()
        with patch.object(servidor, '_estado_semana', wraps=servidor._estado_semana) as detail:
            result = self.client.get('/api/semanas?limite=2')
        self.assertEqual(result.status_code, 200)
        self.assertEqual([row['nombre'] for row in result.get_json()],
                         ['8 Facturas semana 23OCT26', '7 Facturas semana 23OCT26'])
        self.assertEqual(detail.call_count, 2)

    def test_concurrent_reading_preserves_invoice_order(self):
        for name in ['Empresa B', 'Empresa C', 'Empresa D']:
            path = self.factura.parent / name
            path.mkdir()
            (path / '.OT.txt').write_text('OT1', encoding='utf-8')
        gate = threading.Barrier(4, timeout=3)
        original = servidor._detalle_factura

        def synchronized(path, name):
            gate.wait()
            return original(path, name)

        with patch.object(servidor, '_detalle_factura', side_effect=synchronized):
            response = self.client.get('/api/facturas', query_string={'semana': self.factura.parent.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['nombre'] for row in response.get_json()],
                         ['Empresa A', 'Empresa B', 'Empresa C', 'Empresa D'])

    def test_ot_index_reuses_positive_matches_but_does_not_use_stale_path(self):
        nested = self.obras / 'region' / 'OT-501 obra'
        nested.mkdir(parents=True)
        with patch.object(servidor.os, 'walk', wraps=os.walk) as walk:
            first = servidor.buscar_carpetas_ot('OT-501')
            second = servidor.buscar_carpetas_ot('OT-501')
            self.assertEqual(walk.call_count, 1)
        self.assertEqual(first, second)
        self.assertEqual(first, [os.path.join('region', 'OT-501 obra')])

        nested.rename(self.obras / 'region' / 'OT-501 nueva')
        with patch.object(servidor.os, 'walk', wraps=os.walk) as walk:
            third = servidor.buscar_carpetas_ot('OT-501')
            self.assertEqual(walk.call_count, 1)
        self.assertEqual(third, [os.path.join('region', 'OT-501 nueva')])


if __name__ == '__main__':
    unittest.main()
