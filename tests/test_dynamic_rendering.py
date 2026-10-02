from pathlib import Path
import unittest


HTML = Path(__file__).parents[1] / "templates" / "index.html"


class DynamicRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")

    def function_body(self, start, end):
        return self.source.split(start, 1)[1].split(end, 1)[0]

    def test_untrusted_week_row_and_file_values_use_dom_text_nodes(self):
        weeks = self.function_body("async function initSemanas()", "function filtrarSemanas()")
        rows = self.function_body("async function cargarFacturas", "async function copiarTablaExcel")
        files = self.function_body("async function cargarListaArchivos", "function handleDragOver")

        self.assertNotIn("li.innerHTML", weeks)
        self.assertNotIn("tbody.innerHTML +=", rows)
        self.assertNotIn("onclick=", rows)
        self.assertNotIn("fileList.innerHTML +=", files)
        self.assertIn("document.createTextNode(semanaObj.nombre)", weeks)
        self.assertIn("nombreCarpeta.textContent = fact.nombre", rows)
        self.assertIn("nombreArchivo.textContent = arch", files)
        self.assertIn("encodeURIComponent(ruta)", files)
        self.assertIn("encodeURIComponent(arch)", files)
        self.assertIn('addEventListener("click", () => toggleArchivos(index, fact.ruta))', rows)
        self.assertIn("fragment.append(row, detailsRow)", rows)
        self.assertIn("tbody.replaceChildren(fragment)", rows)

    def test_text_and_value_sinks_cover_markup_quotes_emoji_and_long_values(self):
        tags = self.function_body("function renderTags(index)", "function removeTag")
        planilla = self.function_body("function crearCeldaPlanilla", "function checkExpandirColumna")
        upload = self.function_body("async function handleDrop", "async function guardar")

        self.assertNotIn("innerHTML +=", tags)
        self.assertIn("label.textContent = visualOT", tags)
        self.assertIn("indicator.textContent =", tags)
        self.assertNotIn("bodyHtml", planilla)
        self.assertIn("nombre.textContent = fact.nombre", planilla)
        self.assertIn("input.value = value", planilla)
        self.assertIn("crearCeldaPlanilla(i, c, val)", planilla)
        self.assertNotIn("innerHTML", upload)
        self.assertIn("uploading.textContent =", upload)
        self.assertIn("file.name", upload)

    def test_large_list_assembly_uses_a_fragment_and_single_table_replacement(self):
        rows = self.function_body("async function cargarFacturas", "async function copiarTablaExcel")
        self.assertIn("const fragment = document.createDocumentFragment()", rows)
        self.assertEqual(rows.count("tbody.replaceChildren(fragment)"), 1)
        self.assertNotIn("safeRuta", rows)


if __name__ == "__main__":
    unittest.main()
