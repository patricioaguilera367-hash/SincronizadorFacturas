"""El usuario puede ver un snapshot antes de que responda el NAS, sin poder editarlo."""

import json
from pathlib import Path
import shutil
import subprocess
import unittest


HTML = Path(__file__).parents[1] / 'templates' / 'index.html'


@unittest.skipUnless(shutil.which('node'), 'Node.js requerido para probar la UI real')
class StaleRevalidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = HTML.read_text(encoding='utf-8')
        cls.week_script = source.split('async function cargarFacturas', 1)[1].split('async function copiarTablaExcel', 1)[0]
        cls.week_script = 'async function cargarFacturas' + cls.week_script

    def run_case(self, case):
        script = """
const assert = require('node:assert/strict');
const nodes = new Map();
function makeNode() {
    return {
        children: [], style: {}, dataset: {}, inert: false, textContent: '', hidden: true,
        classList: {add(){}, remove(){}, toggle(){}},
        append(...children) {this.children.push(...children);},
        appendChild(child) {this.children.push(child);},
        replaceChildren(...children) {this.children = children;},
        setAttribute(){}, addEventListener(){}, focus(){},
    };
}
const document = {
    getElementById(id) {
        if (!nodes.has(id)) nodes.set(id, makeNode());
        return nodes.get(id);
    },
    createDocumentFragment: makeNode,
    createElement: makeNode,
    createTextNode(text) { return {textContent: text}; },
    querySelectorAll() {return [];},
};
const window = { matchMedia: () => ({matches: false}) };
let facturasActuales = [], tagsData = {}, estadosSyncOT = {};
let semanaSeleccionada = '', carpetaSeleccionada = '', folderRequestToken = 0;
let weekRequestToken = 0, modoOffline = false, snapshotActualizado = null;
const cacheSemanasCliente = new Map();
const estadosDocumentos = { factura: ['pendiente'], solicitud_pago: ['pendiente'], comprobante_pago: ['pendiente'] };
function renderEstadoDocumento() {return makeNode();}
function renderTags() {}
function updateStats() {}
function cargarRevision() {}
function initSemanas() {}
function aplicarModoOffline(offline) {modoOffline = offline;}
function updateWithViewTransition(callback) {callback();}
function mostrarEstadoTabla(message) {document.getElementById('tablaBody').textContent = message;}
function makeRows(nombre) {return [{nombre, ruta: 'ruta/'+nombre, ot_content: '206_NT_591', badge_class: 'badge-loading', badge_text: 'Pendiente', ignorado: false, estados: {factura: 'pendiente', solicitud_pago: 'pendiente', comprobante_pago: 'pendiente'}}];}
function response(rows, offline='0') {return {ok:true, headers:{get:key=>key==='X-Sincronizador-Offline'?offline:null}, json:async()=>rows};}
function deferred() {let resolve, reject; const promise = new Promise((res,rej)=>{resolve=res;reject=rej;}); return {promise, resolve, reject};}
const remote = new Map();
const cacheData = new Map();
const calls = [];
const fetchConTimeout = async url => {
    calls.push('nas:'+url);
    const semana = new URL('http://local'+url).searchParams.get('semana');
    if (!remote.has(semana)) remote.set(semana,deferred());
    return remote.get(semana).promise;
};
const fetch = async url => {
    calls.push('cache:'+url);
    const semana = new URL('http://local'+url).searchParams.get('semana');
    return cacheData.has(semana)
      ? {ok:true, json:async()=>cacheData.get(semana)}
      : {ok:false, json:async()=>({error:'sin snapshot'})};
};
async function respuestaJson(res) {
    const offline = res.headers.get('X-Sincronizador-Offline');
    if (offline !== null) aplicarModoOffline(offline==='1');
    if (!res.ok) throw Error('No se pudieron cargar las facturas.');
    return res.json();
}
const flush = async() => {for(let i=0;i<5;i++) await new Promise(resolve=>setImmediate(resolve));};
eval(%s);
(async()=>{%s})().catch(e=>{console.error(e); process.exitCode=1;});
""" % (json.dumps(self.week_script, ensure_ascii=False), case)
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cache_appears_before_nas_and_unlocks_only_after_validation(self):
        self.run_case("""
cacheData.set('Semana A',makeRows('Guardada'));
const pending = cargarFacturas('Semana A');
await flush();
assert.equal(facturasActuales[0]?.nombre,'Guardada');
assert.equal(document.getElementById('contenedorTabla').inert,true);
assert.equal(document.getElementById('botonesAccion').inert,true);
assert.equal(document.getElementById('estadoActualizacionSemana').hidden,false);
remote.get('Semana A').resolve(response(makeRows('Actual')));
await pending;
assert.equal(facturasActuales[0].nombre,'Actual');
assert.equal(document.getElementById('contenedorTabla').inert,false);
assert.equal(document.getElementById('botonesAccion').inert,false);
assert.equal(document.getElementById('estadoActualizacionSemana').hidden,true);
""")

    def test_nas_failure_preserves_cache_but_never_enables_editing(self):
        self.run_case("""
cacheData.set('Semana A',makeRows('Guardada'));
const pending = cargarFacturas('Semana A');
await flush();
remote.get('Semana A').reject(Error('NAS desconectado'));
await pending;
assert.equal(facturasActuales[0].nombre,'Guardada');
assert.equal(document.getElementById('contenedorTabla').inert,true);
assert.match(document.getElementById('estadoActualizacionSemana').textContent,/No se pudo verificar/i);
""")

    def test_newer_week_wins_even_when_old_nas_response_arrives_last(self):
        self.run_case("""
cacheData.set('Semana A',makeRows('Guardada A'));
cacheData.set('Semana B',makeRows('Guardada B'));
const first = cargarFacturas('Semana A');
await flush();
const second = cargarFacturas('Semana B');
await flush();
remote.get('Semana B').resolve(response(makeRows('Actual B')));
await second;
remote.get('Semana A').resolve(response(makeRows('Actual A')));
await first;
assert.equal(semanaSeleccionada,'Semana B');
assert.equal(facturasActuales[0].nombre,'Actual B');
assert.equal(document.getElementById('contenedorTabla').inert,false);
""")

    def test_missing_snapshot_still_loads_live_data(self):
        self.run_case("""
const pending = cargarFacturas('Semana A');
await flush();
assert.equal(facturasActuales.length,0);
remote.get('Semana A').resolve(response(makeRows('Actual')));
await pending;
assert.equal(facturasActuales[0].nombre,'Actual');
assert.equal(document.getElementById('contenedorTabla').inert,false);
""")


if __name__ == '__main__':
    unittest.main()
