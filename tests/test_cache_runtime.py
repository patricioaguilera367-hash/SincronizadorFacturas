import csv
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import cache_runtime


class CacheRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "obras"
        self.root.mkdir()
        self.index = Path(self.tempdir.name) / "data" / "indice_ot.json"
        self.snapshot = Path(self.tempdir.name) / "data" / "snapshot_app.json"

    def tearDown(self):
        self.tempdir.cleanup()

    def test_root_reconciliation_indexes_only_existing_matching_prefix(self):
        principal = self.root / "206_NT_001 206_NT_002 proyecto"
        principal.mkdir()
        (self.root / "carpeta sin ot").mkdir()

        result = cache_runtime.reconciliar_indice_raiz(self.index, self.root)
        self.assertTrue(result["ok"])

        first = cache_runtime.candidatos_indice(self.index, self.root, "206/NT-001")
        second = cache_runtime.candidatos_indice(self.index, self.root, "206/NT-002")

        self.assertEqual(len(first), 1)
        self.assertEqual(Path(first[0]["ruta"]).name, principal.name)
        # No se infieren relaciones/consecutividad ni una segunda OT.
        self.assertEqual(second, [])

    def test_completed_scan_marks_historical_root_path_absent(self):
        folder = self.root / "206_NT_010 proyecto"
        folder.mkdir()
        cache_runtime.reconciliar_indice_raiz(self.index, self.root)

        folder.rmdir()
        result = cache_runtime.reconciliar_indice_raiz(self.index, self.root)
        self.assertTrue(result["ok"])

        active = cache_runtime.candidatos_indice(self.index, self.root, "206_NT_010")
        history = cache_runtime.candidatos_indice(
            self.index,
            self.root,
            "206_NT_010",
            incluir_ausentes=True,
        )
        self.assertEqual(active, [])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["estado"], "ausente")
        self.assertTrue(history[0]["ausente_desde"])

    def test_failed_scan_never_marks_cached_path_absent(self):
        folder = self.root / "206_NT_020 proyecto"
        folder.mkdir()
        cache_runtime.reconciliar_indice_raiz(self.index, self.root)

        with patch.object(cache_runtime.os, "scandir", side_effect=OSError("sin red")):
            result = cache_runtime.reconciliar_indice_raiz(self.index, self.root)

        self.assertFalse(result["ok"])
        active = cache_runtime.candidatos_indice(self.index, self.root, "206_NT_020")
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["estado"], "activa")

    def test_seed_csv_is_history_until_server_reconciles_it(self):
        folder = self.root / "206_NT_030 proyecto"
        folder.mkdir()
        csv_path = Path(self.tempdir.name) / "indice_obras.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=["Name", "FullName"])
            writer.writeheader()
            writer.writerow({"Name": folder.name, "FullName": str(folder)})

        seeded = cache_runtime.sembrar_indice_desde_csv(
            self.index,
            csv_path,
            self.root,
        )
        self.assertTrue(seeded["usado"])

        before = cache_runtime.candidatos_indice(self.index, self.root, "206_NT_030")
        self.assertEqual(before[0]["estado"], "sin_verificar")

        cache_runtime.reconciliar_indice_raiz(self.index, self.root)
        after = cache_runtime.candidatos_indice(self.index, self.root, "206_NT_030")
        self.assertEqual(after[0]["estado"], "activa")

    def test_snapshot_roundtrip_is_read_only_context_data(self):
        weeks = [{"nombre": "Semana 01", "estado": "warning"}]
        facturas = [{
            "nombre": "Factura A",
            "ruta": "ruta-cacheada",
            "ot_content": "206_NT_040",
            "badge_class": "badge-loading",
            "badge_text": "Pendiente",
            "ignorado": False,
            "estados": {"factura": "pendiente"},
        }]

        cache_runtime.actualizar_snapshot_semanas(self.snapshot, weeks)
        cache_runtime.actualizar_snapshot_facturas(
            self.snapshot,
            "Semana 01",
            facturas,
        )

        self.assertEqual(cache_runtime.snapshot_semanas(self.snapshot), weeks)
        self.assertEqual(
            cache_runtime.snapshot_facturas(self.snapshot, "Semana 01"),
            facturas,
        )
        info = cache_runtime.info_snapshot(self.snapshot)
        self.assertEqual(info["weeks"], 1)
        self.assertEqual(info["semanas_con_detalle"], 1)
        self.assertTrue(info["updated_at"])


if __name__ == "__main__":
    unittest.main()
