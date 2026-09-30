from pathlib import Path
import shutil
import subprocess
import unittest


HTML = Path(__file__).parents[1] / "templates" / "index.html"


class AsyncRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")

    def body(self, start, end):
        return self.source.split(start, 1)[1].split(end, 1)[0]

    def test_week_and_folder_loads_recover_and_ignore_stale_responses(self):
        weeks = self.body("async function initSemanas()", "function filtrarSemanas")
        invoices = self.body("async function cargarFacturas", "async function copiarTablaExcel")
        files = self.body("async function cargarListaArchivos", "function handleDragOver")

        self.assertIn("let weekRequestToken = 0;", self.source)
        self.assertIn("const requestToken = ++weekRequestToken;", invoices)
        self.assertIn("if (requestToken !== weekRequestToken || semana !== semanaSeleccionada)", invoices)
        self.assertIn("No se pudieron cargar las facturas.", invoices)
        self.assertIn("Reintentar", self.source)
        self.assertIn("try {", weeks)
        self.assertIn("No se pudieron cargar las semanas.", weeks)
        self.assertIn("No hay semanas disponibles.", weeks)
        self.assertIn("let folderRequestToken = 0;", self.source)
        self.assertIn("const requestToken = ++folderRequestToken;", files)
        self.assertIn("if (requestToken !== folderRequestToken || ruta !== carpetaSeleccionada)", files)
        self.assertIn("No se pudieron cargar los archivos.", files)

    def test_detailed_week_refresh_keeps_existing_buttons(self):
        weeks = self.body("async function initSemanas()", "function filtrarSemanas")
        detailed = weeks.split("if (detallado) {", 1)[1].split("if (semanas.length === 0)", 1)[0]

        self.assertIn("button.dataset.semana = semanaObj.nombre", weeks)
        self.assertIn("actualizarEstadoSemana(button, semanaObj.estado)", detailed)
        self.assertNotIn("replaceChildren", detailed)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the renderer check")
    def test_initial_week_render_executes_without_undefined_bindings(self):
        helper = self.source.split("function actualizarEstadoSemana", 1)[1].split("async function initSemanas()", 1)[0]
        init = self.body("async function initSemanas()", "function filtrarSemanas")
        script = f"""
const makeNode = () => ({{
  children: [], dataset: {{}}, className: '', textContent: '',
  append(...nodes) {{ this.children.push(...nodes); }},
  appendChild(node) {{ this.children.push(node); }},
  replaceChildren(...nodes) {{ this.children = nodes; }},
  setAttribute() {{}},
  addEventListener() {{}},
  querySelector(selector) {{ return this.children.find(node => node.className && node.className.includes(selector.slice(1))); }}
}});
const list = makeNode();
const buttons = [];
const descendants = node => (node.children || []).flatMap(child => [child, ...descendants(child)]);
global.document = {{
  getElementById: () => list,
  getElementsByClassName: name => descendants(list).filter(node => node.className && node.className.includes(name)),
  createDocumentFragment: makeNode,
  createElement: tag => {{ const node = makeNode(); if (tag === 'button') buttons.push(node); return node; }},
  createTextNode: text => ({{ textContent: text }})
}};
let weeksRequestToken = 0;
const mostrarEstadoSemanas = () => {{}};
const respuestaJson = async response => response.json();
const fetch = async () => ({{ json: async () => [{{ nombre: 'Semana 01', estado: 'loading' }}] }});
function actualizarEstadoSemana{helper}
async function initSemanas(){init}
(async () => {{
  await initSemanas();
  const button = buttons[0];
  if (!button || button.dataset.semana !== 'Semana 01') throw new Error('week button was not rendered');
  if (!button.querySelector('.status-dot').className.includes('loading')) throw new Error('week status was not rendered');
}})().catch(error => {{ console.error(error); process.exit(1); }});
"""
        result = subprocess.run(["node", "-e", script], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mutating_actions_release_controls_and_prevent_duplicates(self):
        self.assertIn("const submissionsInFlight = new Set();", self.source)
        self.assertIn("function beginSubmission(key)", self.source)
        self.assertIn("function endSubmission(key)", self.source)

        for start, end in (
            ("async function crearNuevaSemana()", "async function crearNuevaFactura"),
            ("async function eliminarCarpeta", "async function renombrarCarpeta"),
            ("async function guardar", "async function sincronizarIndividual"),
            ("async function sincronizarIndividual", "async function sincronizarTodaLaSemana"),
            ("async function sincronizarTodaLaSemana", "</script>"),
        ):
            with self.subTest(function=start):
                action = self.body(start, end)
                self.assertIn("beginSubmission", action)
                self.assertIn("finally", action)
                self.assertIn("endSubmission", action)


if __name__ == "__main__":
    unittest.main()
