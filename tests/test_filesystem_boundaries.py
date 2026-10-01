import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import servidor


class FilesystemBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.facturas = root / "facturas"
        self.obras = root / "obras"
        self.factura = self.facturas / "Semana 01" / "Factura válida"
        self.factura.mkdir(parents=True)
        (self.factura / ".OT.txt").write_text("OT1", encoding="utf-8")
        (self.factura / "documento.txt").write_text("interno", encoding="utf-8")
        self.outside = root / "outside"
        self.outside.mkdir()
        (self.outside / "secreto.txt").write_text("no exponer", encoding="utf-8")
        self.outside_marker = self.outside / "marca.txt"
        self.outside_marker.write_text("intacto", encoding="utf-8")
        (self.obras / "OT1 obra" / "Pensiones y almuerzos").mkdir(parents=True)

        self.original_facturas = servidor.BASE_FACTURAS
        self.original_obras = servidor.BASE_OBRAS
        servidor.BASE_FACTURAS = str(self.facturas)
        servidor.BASE_OBRAS = str(self.obras)
        servidor.app.config.update(TESTING=True)
        self.client = servidor.app.test_client()

    def tearDown(self):
        servidor.BASE_FACTURAS = self.original_facturas
        servidor.BASE_OBRAS = self.original_obras
        self.tempdir.cleanup()

    def assert_rejected(self, response):
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(str(self.outside), response.get_data(as_text=True))

    def test_read_and_write_routes_reject_outside_invoice_paths(self):
        outside = str(self.outside)
        self.assert_rejected(self.client.get("/api/facturas", query_string={"semana": outside}))
        self.assert_rejected(self.client.post("/api/guardar", json={"ruta": outside, "contenido": "cambio"}))
        self.assert_rejected(self.client.post("/api/actualizar_estado_documento", json={"ruta": outside, "tipo": "factura", "estado": "recibida"}))
        self.assert_rejected(self.client.post("/api/toggle_ignorar", json={"ruta": outside}))
        self.assertEqual(self.outside_marker.read_text(encoding="utf-8"), "intacto")
        self.assertFalse((self.outside / ".sync_state.json").exists())
        self.assertFalse((self.outside / "ignorado.txt").exists())

    def test_upload_list_and_file_serving_reject_outside_paths(self):
        outside = str(self.outside)
        self.assert_rejected(self.client.get("/api/archivos", query_string={"ruta": outside}))
        self.assert_rejected(self.client.post("/api/upload", data={"ruta": outside, "file": (io.BytesIO(b"nuevo"), "nuevo.txt")}))
        self.assert_rejected(self.client.get("/api/ver_archivo", query_string={"ruta": outside, "archivo": "secreto.txt"}))
        self.assertFalse((self.outside / "nuevo.txt").exists())

    def test_rename_delete_and_new_invoice_reject_escaping_components(self):
        outside = str(self.outside)
        self.assert_rejected(self.client.post("/api/eliminar_factura", json={"ruta": outside}))
        self.assert_rejected(self.client.post("/api/renombrar_carpeta", json={"ruta_antigua": outside, "nuevo_nombre": "renombrada"}))
        self.assert_rejected(self.client.post("/api/nueva_factura", json={"semana": outside, "nombre": "nueva"}))
        self.assertTrue(self.outside.exists())
        self.assertEqual(self.outside_marker.read_text(encoding="utf-8"), "intacto")

    def test_sync_rejects_an_outside_destination_name_without_copying(self):
        outside_destination = self.outside / "copia"
        response = self.client.post("/api/sincronizar", json={
            "ruta": str(self.factura),
            "nombre": str(outside_destination),
            "contenido": "OT1",
        })
        self.assert_rejected(response)
        self.assertFalse(outside_destination.exists())

    def test_symlinked_invoice_path_cannot_escape_the_invoice_root(self):
        link = self.facturas / "Semana 01" / "enlace"
        try:
            os.symlink(self.outside, link, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"No se pueden crear enlaces simbólicos: {error}")

        self.assert_rejected(self.client.post("/api/guardar", json={"ruta": str(link), "contenido": "cambio"}))
        self.assertFalse((self.outside / ".OT.txt").exists())
    def test_hidden_ot_can_be_written_repeatedly(self):
        first = self.client.post("/api/guardar", json={"ruta": str(self.factura), "contenido": "OT-A"})
        second = self.client.post("/api/guardar", json={"ruta": str(self.factura), "contenido": "OT-B"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual((self.factura / ".OT.txt").read_text(encoding="utf-8"), "OT-B")

    def test_legacy_ot_is_read_and_migrated_on_next_write(self):
        nuevo = self.factura / ".OT.txt"
        viejo = self.factura / "OT.txt"
        if nuevo.exists():
            nuevo.unlink()
        viejo.write_text("OT-LEGACY", encoding="utf-8")

        response = self.client.get("/api/facturas", query_string={"semana": "Semana 01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["ot_content"], "OT-LEGACY")

        guardado = self.client.post("/api/guardar", json={"ruta": str(self.factura), "contenido": "OT-NUEVA"})
        self.assertEqual(guardado.status_code, 200)
        self.assertEqual(nuevo.read_text(encoding="utf-8"), "OT-NUEVA")
        self.assertFalse(viejo.exists())

    def test_legitimate_in_root_operations_keep_their_existing_success_shape(self):
        response = self.client.post("/api/guardar", json={"ruta": str(self.factura), "contenido": "OT2"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
        self.assertEqual((self.factura / ".OT.txt").read_text(encoding="utf-8"), "OT2")

    def test_open_folder_shortcuts_only_use_approved_shared_paths(self):
        week = self.factura.parent
        with patch.object(servidor, "_abrir_directorio_local") as abrir:
            root = self.client.post("/api/abrir_carpeta", json={"tipo": "facturas"})
            weekly = self.client.post("/api/abrir_carpeta", json={"tipo": "semana", "semana": week.name})
            invoice = self.client.post("/api/abrir_carpeta", json={"tipo": "factura", "ruta": str(self.factura)})
            ot = self.client.post("/api/abrir_carpeta", json={"tipo": "ot", "ot": "OT1"})

        self.assertEqual(root.status_code, 200)
        self.assertEqual(weekly.status_code, 200)
        self.assertEqual(invoice.status_code, 200)
        self.assertEqual(ot.status_code, 200)

        opened = [os.path.normcase(os.path.realpath(call.args[0])) for call in abrir.call_args_list]
        self.assertIn(os.path.normcase(os.path.realpath(self.facturas)), opened)
        self.assertIn(os.path.normcase(os.path.realpath(week)), opened)
        self.assertIn(os.path.normcase(os.path.realpath(self.factura)), opened)
        self.assertIn(os.path.normcase(os.path.realpath(self.obras / "OT1 obra")), opened)

        outside = self.client.post("/api/abrir_carpeta", json={"tipo": "factura", "ruta": str(self.outside)})
        self.assertEqual(outside.status_code, 400)

    def test_delete_rejects_the_invoice_root_without_removing_it(self):
        response = self.client.post("/api/eliminar_factura", json={"ruta": str(self.facturas)})
        self.assert_rejected(response)
        self.assertTrue(self.facturas.exists())
        self.assertTrue(self.factura.exists())

    def test_rename_rejects_the_invoice_root_without_moving_it(self):
        response = self.client.post("/api/renombrar_carpeta", json={"ruta_antigua": str(self.facturas), "nuevo_nombre": "facturas-renombradas"})
        self.assert_rejected(response)
        self.assertTrue(self.facturas.exists())
        self.assertFalse((self.facturas.parent / "facturas-renombradas").exists())

    def test_guardar_rejects_non_string_content_before_truncating_ot(self):
        response = self.client.post("/api/guardar", json={"ruta": str(self.factura), "contenido": ["no", "texto"]})
        self.assert_rejected(response)
        self.assertEqual((self.factura / ".OT.txt").read_text(encoding="utf-8"), "OT1")

    def test_sync_all_rejects_malformed_items_before_any_write(self):
        malformed_items = [
            {"ruta": str(self.factura), "nombre": "Factura válida", "contenido": "OT2"},
            {"ruta": str(self.factura), "nombre": "Factura válida", "contenido": 42, "index": 1},
            {"ruta": str(self.factura), "nombre": str(self.outside / "escape"), "contenido": "OT2", "index": 2},
        ]
        valid_item = {"ruta": str(self.factura), "nombre": self.factura.name, "contenido": "OT2", "index": 0}
        for item in malformed_items:
            with self.subTest(item=item):
                response = self.client.post("/api/sincronizar_todo", json=[valid_item, item])
                self.assert_rejected(response)
                self.assertEqual((self.factura / ".OT.txt").read_text(encoding="utf-8"), "OT1")

    def test_representative_in_root_routes_preserve_success_payloads(self):
        created = self.client.post("/api/nueva_factura", json={"semana": "Semana 01", "nombre": "Factura nueva"})
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.get_json(), {"status": "ok"})
        self.assertTrue((self.facturas / "Semana 01" / "Factura nueva").is_dir())

        listed = self.client.get("/api/archivos", query_string={"ruta": str(self.factura)})
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(set(listed.get_json()), {"documento.txt"})


    def test_ignore_only_blocks_synchronization(self):
        ignored = self.client.post("/api/toggle_ignorar", json={"ruta": str(self.factura)})
        self.assertEqual(ignored.status_code, 200)
        self.assertTrue((self.factura / "ignorado.txt").exists())

        # Seguimiento y edición siguen activos.
        listed = self.client.get("/api/facturas", query_string={"semana": "Semana 01"})
        self.assertEqual(listed.status_code, 200)
        item = listed.get_json()[0]
        self.assertTrue(item["ignorado"])
        self.assertNotEqual(item["badge_class"], "badge-ignored")

        saved = self.client.post("/api/guardar", json={"ruta": str(self.factura), "contenido": "OT2"})
        self.assertEqual(saved.status_code, 200)
        self.assertEqual((self.factura / ".OT.txt").read_text(encoding="utf-8"), "OT2")

        state = self.client.post("/api/actualizar_estado_documento", json={
            "ruta": str(self.factura), "tipo": "factura", "estado": "recibida"
        })
        self.assertEqual(state.status_code, 200)
        self.assertEqual(state.get_json()["estados"]["factura"], "recibida")

        # Sólo sincronizar queda bloqueado.
        single = self.client.post("/api/sincronizar", json={
            "ruta": str(self.factura), "nombre": self.factura.name, "contenido": "OT1"
        })
        self.assertEqual(single.status_code, 409)
        self.assertEqual(single.get_json()["status"], "error")
        self.assertIn("ignorada", single.get_json()["mensaje"].lower())

    def test_ignore_toggle_updates_only_its_row_in_ui(self):
        template = (Path(__file__).parents[1] / "templates" / "index.html").read_text(encoding="utf-8")
        start = template.index("async function toggleIgnorar")
        end = template.index("\n        function formatVisualOT", start)
        handler = template[start:end]

        self.assertIn("fact.ignorado = !!data.ignorado", handler)
        self.assertIn("aplicarEstadoIgnoradoFila(index)", handler)
        self.assertNotIn("cargarFacturas(", handler)
        self.assertNotIn("initSemanas(", handler)

        self.assertIn("data-ignore-chip", template)
        self.assertIn("🚫 Ignorada", template)
        self.assertIn("data-sync-index", template)
        self.assertIn("data-ignore-index", template)

    def test_non_structural_row_actions_do_not_rebuild_week_sidebar(self):
        template = (Path(__file__).parents[1] / "templates" / "index.html").read_text(encoding="utf-8")
        self.assertIn("initSemanas(true);", template)

        for handler_name in ("ciclarEstadoDocumento", "handleDrop", "guardar"):
            start = template.index(f"function {handler_name}") if f"function {handler_name}" in template else template.index(f"async function {handler_name}")
            next_async = template.find("\n        async function", start + 1)
            next_func = template.find("\n        function", start + 1)
            candidates = [x for x in (next_async, next_func) if x != -1]
            end = min(candidates) if candidates else len(template)
            handler = template[start:end]
            self.assertNotIn("initSemanas();", handler)

    def test_ignore_ui_keeps_editing_controls_enabled(self):
        template = (Path(__file__).parents[1] / "templates" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("ignored-box", template)
        self.assertNotIn("input.disabled = fact.ignorado", template)
        self.assertIn("sync.disabled = fact.ignorado", template)
        self.assertIn("if (fact.ignorado) return;", template)
        self.assertIn("Ignorar sólo desactiva la sincronización", template)

    def test_sync_all_keeps_the_existing_in_root_result_shape(self):
        response = self.client.post("/api/sincronizar_todo", json=[{
            "ruta": str(self.factura),
            "nombre": self.factura.name,
            "contenido": "OT1",
            "index": 7,
        }])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"resultados": [{"index": 7, "status": "ok", "errores": []}]})
        self.assertTrue((self.obras / "OT1 obra" / "Pensiones y almuerzos" / self.factura.name / "documento.txt").exists())

    def test_sync_single_persists_ot_before_matching_state(self):
        (self.factura / ".OT.txt").write_text("old", encoding="utf-8")
        response = self.client.post("/api/sincronizar", json={
            "ruta": str(self.factura), "nombre": self.factura.name, "contenido": "OT1"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
        self.assertEqual((self.factura / ".OT.txt").read_text(encoding="utf-8"), "OT1")
        self.assertEqual(json.loads((self.factura / ".sync_state.json").read_text(encoding="utf-8"))["ots"], ["OT1"])

    def test_sync_all_lists_obras_once_for_multiple_invoices(self):
        second = self.factura.parent / "Factura dos"
        second.mkdir()
        (second / ".OT.txt").write_text("OT1", encoding="utf-8")
        obras = os.path.normcase(os.path.realpath(self.obras))
        original_listdir = os.listdir
        calls = 0

        def listdir(path):
            nonlocal calls
            if os.path.normcase(os.path.realpath(path)) == obras:
                calls += 1
            return original_listdir(path)

        with patch.object(servidor.os, "listdir", side_effect=listdir):
            response = self.client.post("/api/sincronizar_todo", json=[
                {"ruta": str(self.factura), "nombre": self.factura.name, "contenido": "OT1", "index": 0},
                {"ruta": str(second), "nombre": second.name, "contenido": "OT1", "index": 1},
            ])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(calls, 1)
        self.assertEqual([item["status"] for item in response.get_json()["resultados"]], ["ok", "ok"])

    def test_sync_reports_ot_write_and_state_write_failures(self):
        original_open = open

        def fail_ot_write(path, mode="r", *args, **kwargs):
            if Path(path).name == ".OT.txt" and "w" in mode:
                raise OSError("OT write failed")
            return original_open(path, mode, *args, **kwargs)

        payload = {"ruta": str(self.factura), "nombre": self.factura.name, "contenido": "OT1"}
        with patch("builtins.open", side_effect=fail_ot_write):
            ot_failure = self.client.post("/api/sincronizar", json=payload)
        self.assertEqual(ot_failure.status_code, 200)
        self.assertEqual(ot_failure.get_json()["status"], "error")
        self.assertFalse((self.factura / ".sync_state.json").exists())

        with patch.object(servidor, "actualizar_estado_sync", side_effect=OSError("state write failed")):
            state_failure = self.client.post("/api/sincronizar", json=payload)
        self.assertEqual(state_failure.status_code, 200)
        self.assertEqual(state_failure.get_json()["status"], "error")

    def test_sync_uses_normalized_direct_ot_folder_without_walking_obras(self):
        ot = "206/NT-591"
        folder = self.obras / "206_NT_591"
        (folder / "Pensiones y almuerzos").mkdir(parents=True)
        payload = {"ruta": str(self.factura), "nombre": self.factura.name, "contenido": ot}

        with patch.object(servidor.os, "walk", side_effect=AssertionError("No debe recorrer obras")):
            response = self.client.post("/api/sincronizar", json=payload)

        self.assertEqual(response.get_json(), {"status": "ok"})
        self.assertTrue((folder / "Pensiones y almuerzos" / self.factura.name / "documento.txt").exists())

    def test_sync_uses_direct_ot_folder_when_obras_listing_is_denied(self):
        ot = "2026_NT_591"
        (self.obras / ot / "Pensiones y almuerzos").mkdir(parents=True)
        original_listdir = os.listdir

        def listdir(path):
            if path == servidor.BASE_OBRAS:
                raise PermissionError("root listing denied")
            return original_listdir(path)

        payload = {"ruta": str(self.factura), "nombre": self.factura.name, "contenido": ot}
        with patch.object(servidor.os, "listdir", side_effect=listdir):
            single = self.client.post("/api/sincronizar", json=payload)
            batch = self.client.post("/api/sincronizar_todo", json=[{**payload, "index": 4}])

        self.assertEqual(single.get_json(), {"status": "ok"})
        self.assertEqual(batch.get_json(), {"resultados": [{"index": 4, "status": "ok", "errores": []}]})
        self.assertTrue((self.obras / ot / "Pensiones y almuerzos" / self.factura.name / "documento.txt").exists())

    def test_sync_reports_a_matching_ot_folder_when_its_metadata_is_denied(self):
        ot = "2026_NT_591"
        blocked = self.obras / ot
        (blocked / "Pensiones y almuerzos").mkdir(parents=True)
        original_stat = os.stat
        blocked_path = os.path.normcase(os.path.realpath(blocked))

        def stat(path, *args, **kwargs):
            if os.path.normcase(os.path.realpath(path)) == blocked_path:
                raise PermissionError("OT metadata denied")
            return original_stat(path, *args, **kwargs)

        payload = {"ruta": str(self.factura), "nombre": self.factura.name, "contenido": ot}
        with patch.object(servidor.os, "stat", side_effect=stat):
            single = self.client.post("/api/sincronizar", json=payload)
            batch = self.client.post("/api/sincronizar_todo", json=[{**payload, "index": 4}])

        error = f"No se pudo acceder a la carpeta de la OT {ot}."
        self.assertEqual(single.get_json(), {"status": "warning", "errores": [error]})
        self.assertEqual(batch.get_json(), {"resultados": [{"index": 4, "status": "warning", "errores": [error]}]})
        self.assertFalse((blocked / "Pensiones y almuerzos" / self.factura.name).exists())

    def test_sync_handlers_refresh_existing_week_badges_in_place(self):
        template = (Path(__file__).parents[1] / "templates" / "index.html").read_text(encoding="utf-8")
        for handler in ("sincronizarIndividual", "sincronizarTodaLaSemana"):
            start = template.index(f"async function {handler}")
            end = template.find("\n        async function", start + 1)
            if end == -1:
                end = template.index("\n        </script>", start)
            self.assertIn("initSemanas(true);", template[start:end])
            self.assertNotIn("initSemanas();", template[start:end])

    def test_sync_defers_obras_metadata_and_skips_unsafe_match(self):
        (self.obras / "No coincide").mkdir()
        (self.obras / "OT1 unsafe").mkdir()
        original_route = servidor.ruta_aprobada
        original_exists = os.path.exists
        original_listdir = os.listdir
        obra_child_checks = []

        def ruta_aprobada(raiz, *partes):
            if raiz == servidor.BASE_OBRAS and partes:
                obra_child_checks.append(partes)
                if partes == ("OT1 unsafe",):
                    return None
            return original_route(raiz, *partes)

        def exists(path):
            if path == servidor.BASE_OBRAS:
                raise AssertionError("BASE_OBRAS existence check is redundant")
            return original_exists(path)

        def listdir(path):
            if path == servidor.BASE_OBRAS:
                return ["No coincide", "OT1 unsafe", "OT1 obra"]
            return original_listdir(path)

        with patch.object(servidor, "ruta_aprobada", side_effect=ruta_aprobada), patch.object(servidor.os.path, "exists", side_effect=exists), patch.object(servidor.os, "listdir", side_effect=listdir):
            response = self.client.post("/api/sincronizar", json={
                "ruta": str(self.factura), "nombre": self.factura.name, "contenido": "OT1"
            })

        self.assertEqual(response.get_json(), {"status": "ok"})
        self.assertNotIn(("No coincide",), obra_child_checks)
        self.assertIn(("OT1 unsafe",), obra_child_checks)
        self.assertIn(("OT1 obra",), obra_child_checks)

    def test_fast_week_discovery_skips_child_checks_and_detail_isolates_child_errors(self):
        second_week = self.facturas / "Semana 02"
        second_week.mkdir()
        original_listdir = os.listdir
        blocked_week = os.path.normcase(os.path.realpath(self.factura.parent))

        def listdir(path):
            if os.path.normcase(os.path.realpath(path)) == blocked_week:
                raise PermissionError("inaccessible week")
            return original_listdir(path)

        with patch.object(servidor.os, "listdir", side_effect=listdir):
            fast = self.client.get("/api/semanas?rapido=1")
            detailed = self.client.get("/api/semanas")

        self.assertEqual(fast.status_code, 200)
        self.assertEqual(
            fast.get_json(),
            [{"nombre": "Semana 01", "estado": "loading"}, {"nombre": "Semana 02", "estado": "loading"}],
        )
        self.assertEqual(detailed.status_code, 200)
        self.assertEqual(
            detailed.get_json(),
            [{"nombre": "Semana 01", "estado": "unavailable"}, {"nombre": "Semana 02", "estado": "none"}],
        )


    def test_delete_rejects_a_week_directory_without_removing_its_invoices(self):
        week = self.facturas / "Semana 01"
        response = self.client.post("/api/eliminar_factura", json={"ruta": str(week)})
        self.assert_rejected(response)
        self.assertTrue(week.exists())
        self.assertEqual((self.factura / ".OT.txt").read_text(encoding="utf-8"), "OT1")

    def test_rename_rejects_a_week_directory_without_moving_its_invoices(self):
        week = self.facturas / "Semana 01"
        response = self.client.post("/api/renombrar_carpeta", json={"ruta_antigua": str(week), "nuevo_nombre": "Semana renombrada"})
        self.assert_rejected(response)
        self.assertTrue(week.exists())
        self.assertFalse((self.facturas / "Semana renombrada").exists())
        self.assertTrue(self.factura.exists())


    def test_state_update_rejects_root_and_week_paths_without_state_files(self):
        for target in (self.facturas, self.facturas / "Semana 01"):
            with self.subTest(target=target):
                response = self.client.post("/api/actualizar_estado_documento", json={
                    "ruta": str(target), "tipo": "factura", "estado": "recibida"
                })
                self.assert_rejected(response)
                self.assertFalse((target / ".sync_state.json").exists())

    def test_ignore_toggle_rejects_root_and_week_paths_without_marker_files(self):
        for target in (self.facturas, self.facturas / "Semana 01"):
            with self.subTest(target=target):
                response = self.client.post("/api/toggle_ignorar", json={"ruta": str(target)})
                self.assert_rejected(response)
                self.assertFalse((target / "ignorado.txt").exists())

    def test_file_listing_rejects_root_and_week_paths(self):
        for target in (self.facturas, self.facturas / "Semana 01"):
            with self.subTest(target=target):
                self.assert_rejected(self.client.get("/api/archivos", query_string={"ruta": str(target)}))

    def test_upload_rejects_root_and_week_paths_without_writing(self):
        for target in (self.facturas, self.facturas / "Semana 01"):
            with self.subTest(target=target):
                response = self.client.post("/api/upload", data={
                    "ruta": str(target), "file": (io.BytesIO(b"bloqueado"), "bloqueado.txt")
                })
                self.assert_rejected(response)
                self.assertFalse((target / "bloqueado.txt").exists())

    def test_file_serving_rejects_root_and_week_paths(self):
        for target in (self.facturas, self.facturas / "Semana 01"):
            with self.subTest(target=target):
                (target / "solo-interno.txt").write_text("no servir", encoding="utf-8")
                response = self.client.get("/api/ver_archivo", query_string={
                    "ruta": str(target), "archivo": "solo-interno.txt"
                })
                self.assert_rejected(response)

    def test_rename_and_delete_keep_existing_valid_invoice_response_shapes(self):
        renamed = self.factura.parent / "Factura renombrada"
        rename = self.client.post("/api/renombrar_carpeta", json={
            "ruta_antigua": str(self.factura), "nuevo_nombre": renamed.name
        })
        self.assertEqual(rename.status_code, 200)
        self.assertEqual(rename.get_json()["status"], "ok")
        self.assertEqual(set(rename.get_json()), {"status", "nueva_ruta"})
        self.assertEqual(Path(rename.get_json()["nueva_ruta"]).resolve(), renamed.resolve())
        self.assertTrue(renamed.exists())

        delete = self.client.post("/api/eliminar_factura", json={"ruta": str(renamed)})
        self.assertEqual(delete.status_code, 200)
        self.assertEqual(delete.get_json(), {"status": "ok"})
        self.assertFalse(renamed.exists())


if __name__ == "__main__":
    unittest.main()
