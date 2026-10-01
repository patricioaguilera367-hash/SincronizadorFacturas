import os
import shutil
import re
import json
import sys
from pathlib import Path
from datetime import date, timedelta
from flask import Flask, jsonify, request, render_template, send_file

def _directorio_app():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _directorio_recursos():
    return Path(getattr(sys, '_MEIPASS', _directorio_app()))


APP_DIR = _directorio_app()
RESOURCE_DIR = _directorio_recursos()
CONFIG_PATH = APP_DIR / 'config.json'

CONFIG_DEFAULT = {
    'servidor': '192.168.99.61',
    'recurso': 'obras',
    'ruta_facturas': ['Facturas pensiones', 'Facturas pensiones'],
    'puerto': 5001,
}


def cargar_configuracion():
    config = dict(CONFIG_DEFAULT)

    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open('r', encoding='utf-8-sig') as entrada:
                cargada = json.load(entrada)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f'No se pudo leer {CONFIG_PATH}: {exc}') from exc

        if not isinstance(cargada, dict):
            raise RuntimeError('config.json debe contener un objeto JSON.')
        config.update(cargada)

    servidor = str(config.get('servidor', '')).strip().strip('\\/')
    recurso = str(config.get('recurso', '')).strip().strip('\\/')
    ruta_facturas = config.get('ruta_facturas')
    puerto = config.get('puerto', 5001)

    if not servidor or '\\' in servidor or '/' in servidor:
        raise RuntimeError('El campo servidor de config.json no es válido.')
    if not recurso or '\\' in recurso or '/' in recurso:
        raise RuntimeError('El campo recurso de config.json no es válido.')
    if not isinstance(ruta_facturas, list) or not ruta_facturas or any(
        not isinstance(parte, str)
        or not parte.strip()
        or parte in {'.', '..'}
        or '\\' in parte
        or '/' in parte
        for parte in ruta_facturas
    ):
        raise RuntimeError('ruta_facturas debe ser una lista de carpetas relativas válidas.')
    if type(puerto) is not int or not (1 <= puerto <= 65535):
        raise RuntimeError('El puerto de config.json debe estar entre 1 y 65535.')

    base_obras = rf"\\\\{servidor}\\{recurso}"
    base_facturas = os.path.join(base_obras, *[parte.strip() for parte in ruta_facturas])

    return {
        **config,
        'servidor': servidor,
        'recurso': recurso,
        'ruta_facturas': [parte.strip() for parte in ruta_facturas],
        'puerto': puerto,
        'base_obras': base_obras,
        'base_facturas': base_facturas,
    }


CONFIG = cargar_configuracion()
BASE_OBRAS = CONFIG['base_obras']
BASE_FACTURAS = CONFIG['base_facturas']
APP_HOST = '127.0.0.1'
APP_PORT = CONFIG['puerto']

app = Flask(__name__, template_folder=str(RESOURCE_DIR / 'templates'))

FERIADOS_VIERNES = [
    date(2026, 4, 3), date(2026, 5, 1), date(2026, 9, 18), 
    date(2026, 12, 25), date(2027, 1, 1), date(2027, 3, 26)
]
MESES = { 1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR', 5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC' }
MESES_INV = {v: k for k, v in MESES.items()}

ESTADOS_DOCUMENTOS = {
    'factura': ('pendiente', 'recibida'),
    'solicitud_pago': ('pendiente', 'enviado'),
    'comprobante_pago': ('pendiente', 'recibido', 'enviado'),
}


def componente_aprobado(valor):
    return (
        isinstance(valor, str)
        and bool(valor.strip())
        and valor not in {'.', '..'}
        and not os.path.isabs(valor)
        and '/' not in valor
        and '\\' not in valor
    )


def normalizar_codigo_ot(valor):
    return re.sub(r'[^a-zA-Z0-9]+', '_', valor).strip('_').lower() if isinstance(valor, str) else ''


def coincide_codigo_ot(nombre, ot):
    codigo = normalizar_codigo_ot(nombre)
    return codigo == ot or codigo.startswith(f'{ot}_')


def ruta_aprobada(raiz, *partes):
    if not isinstance(raiz, str) or any(
        not isinstance(parte, str) for parte in partes
    ):
        return None

    def normalizar_para_comparar(ruta):
        ruta = os.path.normpath(ruta)
        normalizada = os.path.normcase(ruta)

        if normalizada.startswith('\\\\?\\unc\\'):
            ruta = '\\\\' + ruta[8:]
        elif normalizada.startswith('\\\\?\\'):
            ruta = ruta[4:]

        return os.path.normcase(ruta)

    try:
        raiz_real = os.path.realpath(raiz)
        candidata = os.path.realpath(
            os.path.join(raiz_real, *partes)
        )

        raiz_comparable = normalizar_para_comparar(raiz_real)
        candidata_comparable = normalizar_para_comparar(candidata)

        # Comprobar que la ruta permanece dentro de la raíz
        relativa = os.path.relpath(
            candidata_comparable,
            raiz_comparable
        )

        if relativa == ".":
            return candidata

        # Impedir el acceso a directorios fuera de la raíz
        if relativa == ".." or relativa.startswith(".." + os.sep):
            return None

        return candidata

    except (OSError, ValueError) as e:
        print(f"[ERROR RUTA] {type(e).__name__}: {e}", flush=True)
        return None


def ruta_factura_aprobada(ruta):
    candidata = ruta_aprobada(BASE_FACTURAS, ruta)
    raiz = os.path.normcase(os.path.realpath(BASE_FACTURAS))
    if not candidata: return None
    try:
        partes = [parte for parte in os.path.relpath(candidata, raiz).split(os.sep) if parte not in {'.', ''}]
        return candidata if len(partes) == 2 else None
    except ValueError:
        return None


def datos_sincronizacion_aprobados(data, requiere_index=False):
    if not isinstance(data, dict): return None
    ruta = ruta_factura_aprobada(data.get('ruta'))
    if not ruta or not os.path.isdir(ruta) or not componente_aprobado(data.get('nombre')) or not isinstance(data.get('contenido'), str):
        return None
    if requiere_index and type(data.get('index')) is not int:
        return None
    return {**data, 'ruta': ruta}


def error_ruta_invalida():
    return jsonify({"error": "Ruta no válida."}), 400

def normalizar_estados_documentos(state):
    estados = state.get('estados', {}) if isinstance(state, dict) else {}
    actuales_guardados = estados.get('actual', {})
    sincronizados_guardados = estados.get('sincronizado', {})
    actuales, sincronizados = {}, {}
    for tipo, opciones in ESTADOS_DOCUMENTOS.items():
        actual = actuales_guardados.get(tipo, opciones[0])
        if actual not in opciones: actual = opciones[0]
        sincronizado = sincronizados_guardados.get(tipo, actual)
        if sincronizado not in opciones: sincronizado = actual
        actuales[tipo] = actual
        sincronizados[tipo] = sincronizado
    return {'actual': actuales, 'sincronizado': sincronizados}

def obtener_fecha_semana(ultima_fecha=None):
    if ultima_fecha:
        fecha_temp = ultima_fecha + timedelta(days=1)
        while fecha_temp.weekday() != 4: fecha_temp += timedelta(days=1)
        viernes = fecha_temp
    else:
        hoy = date.today()
        dias_para_viernes = (4 - hoy.weekday()) % 7
        viernes = hoy + timedelta(days=dias_para_viernes)
    if viernes in FERIADOS_VIERNES: viernes -= timedelta(days=1)
    return f"{viernes.day:02d}{MESES[viernes.month]}{str(viernes.year)[-2:]}"

# V1.1.1 metadata OT oculta
OT_METADATA_NOMBRE = '.OT.txt'
OT_METADATA_LEGACY = 'OT.txt'


def _ocultar_archivo_windows(ruta):
    """Marca un archivo como Hidden en Windows sin romper la app si falla."""
    if os.name != 'nt' or not ruta or not os.path.exists(ruta):
        return

    try:
        import ctypes

        FILE_ATTRIBUTE_HIDDEN = 0x2
        INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

        kernel32 = ctypes.windll.kernel32
        atributos = kernel32.GetFileAttributesW(str(ruta))

        if atributos != INVALID_FILE_ATTRIBUTES:
            kernel32.SetFileAttributesW(
                str(ruta),
                atributos | FILE_ATTRIBUTE_HIDDEN
            )
    except Exception:
        pass


def ruta_ot_metadata(ruta_factura):
    """Ruta canónica del archivo interno .OT.txt."""
    return ruta_aprobada(ruta_factura, OT_METADATA_NOMBRE)


def leer_ot_metadata(ruta_factura):
    """Lee .OT.txt y mantiene compatibilidad con OT.txt antiguo."""
    nueva = ruta_ot_metadata(ruta_factura)
    vieja = ruta_aprobada(ruta_factura, OT_METADATA_LEGACY)

    for candidata in (nueva, vieja):
        if candidata and os.path.exists(candidata):
            try:
                with open(candidata, 'r', encoding='utf-8') as entrada:
                    return entrada.read().strip()
            except OSError:
                continue

    return ''


def _preparar_archivo_oculto_para_escritura_windows(ruta):
    """
    Quita temporalmente el atributo Hidden antes de truncar/recrear el archivo.

    CREATE_ALWAYS puede devolver Access Denied sobre un archivo Hidden en
    Windows. Devuelve los atributos originales para restaurarlos después.
    """
    if os.name != 'nt' or not ruta or not os.path.exists(ruta):
        return None

    try:
        import ctypes

        FILE_ATTRIBUTE_HIDDEN = 0x2
        INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

        kernel32 = ctypes.windll.kernel32
        atributos = kernel32.GetFileAttributesW(str(ruta))
        if atributos == INVALID_FILE_ATTRIBUTES:
            return None

        if atributos & FILE_ATTRIBUTE_HIDDEN:
            kernel32.SetFileAttributesW(
                str(ruta),
                atributos & ~FILE_ATTRIBUTE_HIDDEN
            )

        return atributos
    except Exception:
        return None


def guardar_ot_metadata(ruta_factura, contenido):
    """
    Guarda siempre en .OT.txt.

    En Windows quita Hidden sólo durante la escritura y lo restaura al final.
    Si existe OT.txt antiguo, se elimina únicamente después de escribir el
    archivo nuevo correctamente.
    """
    nueva = ruta_ot_metadata(ruta_factura)
    if not nueva:
        raise ValueError('Ruta OT no válida.')

    atributos_previos = _preparar_archivo_oculto_para_escritura_windows(nueva)

    try:
        with open(nueva, 'w', encoding='utf-8') as salida:
            salida.write(contenido)
    finally:
        # El archivo interno siempre debe terminar oculto, incluso si ya lo era.
        if os.path.exists(nueva):
            _ocultar_archivo_windows(nueva)

    vieja = ruta_aprobada(ruta_factura, OT_METADATA_LEGACY)
    if vieja and os.path.normcase(vieja) != os.path.normcase(nueva) and os.path.exists(vieja):
        try:
            os.remove(vieja)
        except OSError:
            # No afecta el funcionamiento: .OT.txt tiene prioridad de lectura.
            pass

    return nueva


def evaluar_estado_sync(ruta_factura, ot_content):
    if not ot_content.strip(): return "badge-none", "-"
    state_path = ruta_aprobada(ruta_factura, '.sync_state.json')
    if not state_path or not os.path.exists(state_path): return "badge-loading", "⏳ Pendiente de sincronización"
    try:
        with open(state_path, 'r', encoding='utf-8') as f: state = json.load(f)
        current_ots = [ot.strip() for ot in ot_content.split(',') if ot.strip()]
        if set(current_ots) != set(state.get('ots', [])): return "badge-danger", "⚠ Código OT modificado"
        estados = normalizar_estados_documentos(state)
        if estados['actual'] != estados['sincronizado']: return "badge-danger", "⚠ Estado de documento modificado"
        archivos_actuales = {}
        for item in os.listdir(ruta_factura):
            if item.lower() in ['ot.txt', '.ot.txt', '.sync_state.json', 'ignorado.txt', '.factura_montos.json']: continue
            path = ruta_aprobada(ruta_factura, item)
            if path and os.path.isfile(path): archivos_actuales[item] = {'size': os.path.getsize(path), 'mtime': int(os.path.getmtime(path))}
        archivos_sync = state.get('archivos', {})
        for item, info in archivos_actuales.items():
            if item not in archivos_sync: return "badge-danger", "⚠ Archivo agregado"
            if info['size'] != archivos_sync[item]['size'] or info['mtime'] != archivos_sync[item]['mtime']: return "badge-danger", "⚠ Archivo modificado"
        if len(archivos_actuales) < len(archivos_sync): return "badge-danger", "⚠ Archivo eliminado"
        return "badge-success", "✓ Sincronizado"
    except Exception: return "badge-danger", "❌ No se pudo verificar el estado"

def actualizar_estado_sync(ruta_factura, ots):
    state_path = ruta_aprobada(ruta_factura, '.sync_state.json')
    if not state_path: raise ValueError('Ruta de estado no válida.')
    try:
        with open(state_path, 'r', encoding='utf-8') as f: state_anterior = json.load(f)
    except Exception:
        state_anterior = {}
    estados_actuales = normalizar_estados_documentos(state_anterior)['actual']
    state = {'ots': ots, 'archivos': {}, 'estados': {'actual': estados_actuales, 'sincronizado': estados_actuales}}
    for item in os.listdir(ruta_factura):
        if item.lower() in ['ot.txt', '.ot.txt', '.sync_state.json', 'ignorado.txt', '.factura_montos.json']: continue
        path = ruta_aprobada(ruta_factura, item)
        if path and os.path.isfile(path): state['archivos'][item] = {'size': os.path.getsize(path), 'mtime': int(os.path.getmtime(path))}
    with open(state_path, 'w', encoding='utf-8') as f: json.dump(state, f, ensure_ascii=False)

def sincronizar_carpetas_python(origen, destino):
    if os.path.islink(destino): raise ValueError('Destino no válido.')
    os.makedirs(destino, exist_ok=True)
    for item in os.listdir(origen):
        s_path = ruta_aprobada(origen, item)
        d_path = ruta_aprobada(destino, item)
        if not s_path or not d_path: continue
        if item.lower() in ['ot.txt', '.ot.txt', '.sync_state.json', 'ignorado.txt', '.factura_montos.json']: continue
        if os.path.isdir(s_path): sincronizar_carpetas_python(s_path, d_path)
        else:
            if os.path.exists(d_path):
                if os.path.getsize(s_path) != os.path.getsize(d_path):
                    base, ext = os.path.splitext(item)
                    contador = 1
                    nuevo_d_path = ruta_aprobada(destino, f"{base} ({contador}){ext}")
                    while os.path.exists(nuevo_d_path):
                        contador += 1
                        nuevo_d_path = ruta_aprobada(destino, f"{base} ({contador}){ext}")
                    shutil.copy2(s_path, nuevo_d_path)
            else: shutil.copy2(s_path, d_path)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/semanas', methods=['GET'])
def get_semanas():
    try:
        semanas = []
        rapido = request.args.get('rapido') == '1'
        for d in os.listdir(BASE_FACTURAS):
            ruta_semana = ruta_aprobada(BASE_FACTURAS, d)
            if ruta_semana and os.path.isdir(ruta_semana):
                if rapido:
                    semanas.append({"nombre": d, "estado": "loading"})
                    continue
                estado = "success"
                try:
                    carpetas = [f for f in os.listdir(ruta_semana) if ruta_aprobada(ruta_semana, f) and os.path.isdir(ruta_aprobada(ruta_semana, f))]
                    if not carpetas:
                        estado = "none"
                    else:
                        for f in carpetas:
                            ruta_factura = ruta_aprobada(ruta_semana, f)
                            ot_content = leer_ot_metadata(ruta_factura)
                            sync_json = ruta_aprobada(ruta_factura, '.sync_state.json')
                            ignorado_path = ruta_aprobada(ruta_factura, 'ignorado.txt')
                            
                            if ignorado_path and os.path.exists(ignorado_path): 
                                continue 
                                
                            if not ot_content:
                                estado = "danger"
                                break
                            elif not sync_json or not os.path.exists(sync_json):
                                if estado != "danger": estado = "warning"
                except OSError:
                    estado = "unavailable"
                semanas.append({"nombre": d, "estado": estado})
        return jsonify(semanas)
    except Exception: return jsonify({"error": "No se pudieron cargar las semanas."}), 500

@app.route('/api/facturas', methods=['GET'])
def get_facturas():
    semana = request.args.get('semana')
    if not componente_aprobado(semana): return error_ruta_invalida()
    ruta_semana = ruta_aprobada(BASE_FACTURAS, semana)
    facturas_data = []
    if ruta_semana and os.path.exists(ruta_semana):
        for f in os.listdir(ruta_semana):
            ruta_factura = ruta_aprobada(ruta_semana, f)
            if ruta_factura and os.path.isdir(ruta_factura):
                ignorado_path = ruta_aprobada(ruta_factura, "ignorado.txt")
                ot_content = leer_ot_metadata(ruta_factura)
                
                ignorado = bool(ignorado_path and os.path.exists(ignorado_path))
                if ignorado: clase_b, texto_b = "badge-ignored", "🚫 Ignorado"
                else: clase_b, texto_b = evaluar_estado_sync(ruta_factura, ot_content)
                try:
                    with open(ruta_aprobada(ruta_factura, '.sync_state.json'), 'r', encoding='utf-8') as file_state:
                        estado_documentos = normalizar_estados_documentos(json.load(file_state))['actual']
                except Exception:
                    estado_documentos = normalizar_estados_documentos({})['actual']
                facturas_data.append({"nombre": f, "ruta": ruta_factura, "ot_content": ot_content, "badge_class": clase_b, "badge_text": texto_b, "ignorado": ignorado, "estados": estado_documentos})
    return jsonify(facturas_data)

@app.route('/api/actualizar_estado_documento', methods=['POST'])
def actualizar_estado_documento():
    data = request.json or {}
    ruta, tipo, estado = data.get('ruta'), data.get('tipo'), data.get('estado')
    ruta = ruta_factura_aprobada(ruta)
    if not ruta: return error_ruta_invalida()
    if not ruta or not os.path.isdir(ruta): return jsonify({"error": "No existe la carpeta en el servidor."}), 404
    if tipo not in ESTADOS_DOCUMENTOS or estado not in ESTADOS_DOCUMENTOS[tipo]:
        return jsonify({"error": "Estado de documento no válido."}), 400
    state_path = ruta_aprobada(ruta, '.sync_state.json')
    if not state_path: return error_ruta_invalida()
    try:
        try:
            with open(state_path, 'r', encoding='utf-8') as f: state = json.load(f)
        except Exception:
            state = {}
        estados = normalizar_estados_documentos(state)
        estados['actual'][tipo] = estado
        state['estados'] = estados
        with open(state_path, 'w', encoding='utf-8') as f: json.dump(state, f, ensure_ascii=False)
        ot_content = leer_ot_metadata(ruta)
        badge_class, badge_text = evaluar_estado_sync(ruta, ot_content)
        return jsonify({"status": "ok", "estados": estados['actual'], "badge_class": badge_class, "badge_text": badge_text})
    except Exception:
        return jsonify({"error": "No se pudo actualizar el estado del documento."}), 500

@app.route('/api/toggle_ignorar', methods=['POST'])
def toggle_ignorar():
    ruta = ruta_factura_aprobada((request.json or {}).get('ruta'))
    if not ruta: return error_ruta_invalida()
    if not os.path.exists(ruta): return jsonify({"error": "No existe la carpeta en el servidor."}), 404
    ignorado_path = ruta_aprobada(ruta, 'ignorado.txt')
    if not ignorado_path: return error_ruta_invalida()
    try:
        if os.path.exists(ignorado_path):
            os.remove(ignorado_path) 
            return jsonify({"status": "ok", "ignorado": False})
        else:
            with open(ignorado_path, 'w', encoding='utf-8') as f: f.write('1') 
            return jsonify({"status": "ok", "ignorado": True})
    except Exception:
        return jsonify({"error": "No se pudo cambiar el estado ignorado."}), 500

@app.route('/api/nueva_semana', methods=['POST'])
def nueva_semana():
    try:
        max_num, ultima_fecha_str = 0, None
        for d in os.listdir(BASE_FACTURAS):
            if os.path.isdir(ruta_aprobada(BASE_FACTURAS, d)):
                match = re.match(r'^(\d+).*?semana\s+(\d{2})([A-Z]{3})(\d{2})', d, re.IGNORECASE)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
                        ultima_fecha_str = (2000 + int(match.group(4)), match.group(3).upper(), int(match.group(2)))
        ultima_fecha = date(ultima_fecha_str[0], MESES_INV[ultima_fecha_str[1]], ultima_fecha_str[2]) if ultima_fecha_str and ultima_fecha_str[1] in MESES_INV else None
        fecha_str = obtener_fecha_semana(ultima_fecha)
        nombre_carpeta = f"{max_num + 1 if max_num > 0 else 1} Facturas semana {fecha_str}"
        os.makedirs(ruta_aprobada(BASE_FACTURAS, nombre_carpeta), exist_ok=True)
        return jsonify({"status": "ok", "semana": nombre_carpeta})
    except Exception: return jsonify({"error": "No se pudo crear la próxima semana."}), 500

@app.route('/api/nueva_factura', methods=['POST'])
def nueva_factura():
    try:
        data = request.json or {}
        semana, nombre = data.get('semana'), data.get('nombre')
        if not componente_aprobado(semana) or not componente_aprobado(nombre): return error_ruta_invalida()
        ruta_semana = ruta_aprobada(BASE_FACTURAS, semana)
        ruta = ruta_aprobada(ruta_semana, nombre) if ruta_semana else None
        if not ruta: return error_ruta_invalida()
        if os.path.exists(ruta): return jsonify({"error": "Ya existe una carpeta de factura con ese nombre."}), 400
        os.makedirs(ruta, exist_ok=True)
        return jsonify({"status": "ok"})
    except Exception: return jsonify({"error": "No se pudo crear la carpeta de factura."}), 500

@app.route('/api/eliminar_factura', methods=['POST'])
def eliminar_factura():
    try:
        ruta = ruta_factura_aprobada((request.json or {}).get('ruta'))
        if not ruta: return error_ruta_invalida()
        if not os.path.exists(ruta): return jsonify({"error": "La carpeta de factura ya no existe."}), 404
        shutil.rmtree(ruta)
        return jsonify({"status": "ok"})
    except PermissionError: return jsonify({"error": "Permiso denegado."}), 403
    except Exception: return jsonify({"error": "No se pudo eliminar la carpeta de factura."}), 500

@app.route('/api/renombrar_carpeta', methods=['POST'])
def renombrar_carpeta():
    data = request.json or {}
    ruta_antigua, nuevo_nombre = ruta_factura_aprobada(data.get('ruta_antigua')), data.get('nuevo_nombre')
    if not ruta_antigua or not componente_aprobado(nuevo_nombre): return error_ruta_invalida()
    ruta_nueva = ruta_aprobada(os.path.dirname(ruta_antigua), nuevo_nombre)
    if not ruta_nueva: return error_ruta_invalida()
    if os.path.exists(ruta_nueva): return jsonify({"error": "Ya existe una carpeta de factura con ese nombre."}), 400
    try:
        os.rename(ruta_antigua, ruta_nueva)
        state_path = ruta_aprobada(ruta_nueva, '.sync_state.json')
        if state_path and os.path.exists(state_path): os.remove(state_path)
        return jsonify({"status": "ok", "nueva_ruta": ruta_nueva})
    except Exception: return jsonify({"error": "No se pudo renombrar la carpeta de factura."}), 500

@app.route('/api/archivos', methods=['GET'])
def listar_archivos():
    ruta = ruta_factura_aprobada(request.args.get('ruta'))
    if not ruta: return error_ruta_invalida()
    archivos = []
    if os.path.exists(ruta):
        for f in os.listdir(ruta):
            ruta_archivo = ruta_aprobada(ruta, f)
            if ruta_archivo and os.path.isfile(ruta_archivo) and f.lower() not in ['ot.txt', '.ot.txt', '.sync_state.json', 'ignorado.txt', '.factura_montos.json']: archivos.append(f)
    return jsonify(archivos)

@app.route('/api/upload', methods=['POST'])
def subir_archivo():
    file, ruta = request.files.get('file'), ruta_factura_aprobada(request.form.get('ruta'))
    if not ruta: return error_ruta_invalida()
    if file and os.path.exists(ruta):
        nombre = file.filename.replace('/', '').replace('\\', '')
        destino = ruta_aprobada(ruta, nombre) if componente_aprobado(nombre) else None
        if not destino: return error_ruta_invalida()
        if nombre.lower() in {'ot.txt', '.ot.txt', '.sync_state.json', 'ignorado.txt', '.factura_montos.json'}:
            return jsonify({'error': 'Nombre reservado.'}), 400
        file.save(destino)
        from factura_montos import es_factura, actualizar_archivo_cargado
        if es_factura(nombre):
            try:
                actualizar_archivo_cargado(ruta, destino)
            except Exception:
                app.logger.exception('La factura se cargó, pero no se pudo extraer el monto')
        return jsonify({"status": "ok", "archivo": nombre})
    return jsonify({"error": "No se pudo subir el archivo."}), 400

@app.route('/api/ver_archivo', methods=['GET'])
def ver_archivo():
    ruta = ruta_factura_aprobada(request.args.get('ruta'))
    archivo = request.args.get('archivo')
    if not ruta or not componente_aprobado(archivo): return error_ruta_invalida()
    ruta_completa = ruta_aprobada(ruta, archivo)
    if not ruta_completa: return error_ruta_invalida()
    return send_file(ruta_completa) if os.path.exists(ruta_completa) else ("Archivo no encontrado", 404)

@app.route('/api/guardar', methods=['POST'])
def guardar_ot():
    try:
        data = request.json or {}
        contenido = data.get('contenido')
        if not isinstance(contenido, str): return error_ruta_invalida()
        ruta = ruta_factura_aprobada(data.get('ruta'))
        if not ruta: return error_ruta_invalida()
        guardar_ot_metadata(ruta, contenido)
        return jsonify({"status": "ok"})
    except Exception: return jsonify({"error": "No se pudieron guardar los códigos OT."}), 500

def listar_carpetas_obras(ots=None):
    try:
        os.listdir(BASE_OBRAS)
        objetivos = {normalizar_codigo_ot(ot) for ot in ots} if ots is not None else None
        objetivos_originales = set(objetivos) if objetivos is not None else None
        carpetas = []
        carpeta_facturas = os.path.normcase(os.path.basename(os.path.dirname(BASE_FACTURAS)))
        raiz_encontrada = False
        # ponytail: Recursive lookup runs only after direct OT lookup fails; add an OT index if the share grows enough to make this slow.
        for raiz, directorios, _ in os.walk(BASE_OBRAS, topdown=True, followlinks=False):
            if not raiz_encontrada:
                raiz_encontrada = True
                directorios[:] = [d for d in directorios if os.path.normcase(d) != carpeta_facturas]
            for nombre in list(directorios):
                ruta = os.path.join(raiz, nombre)
                if os.path.islink(ruta):
                    directorios.remove(nombre)
                    continue
                relativa = os.path.relpath(ruta, BASE_OBRAS)
                encontrados = {ot for ot in objetivos_originales or () if coincide_codigo_ot(nombre, ot)}
                if objetivos is not None and not encontrados:
                    continue
                aprobada = ruta_aprobada(BASE_OBRAS, *relativa.split(os.sep))
                carpetas.append(relativa)
                if objetivos is not None:
                    objetivos.difference_update(encontrados)
                if not aprobada:
                    directorios.remove(nombre)
            if objetivos is not None and not objetivos:
                return carpetas
        return carpetas if raiz_encontrada else None
    except Exception:
        return None

@app.route('/api/sincronizar_todo', methods=['POST'])
def sincronizar_todo():
    datos = request.json
    if not isinstance(datos, list): return error_ruta_invalida()
    facturas = [datos_sincronizacion_aprobados(fact, requiere_index=True) for fact in datos]
    if any(fact is None for fact in facturas): return error_ruta_invalida()
    cache_obras = {"ots_pendientes": {
        normalizar_codigo_ot(ot)
        for fact in facturas
        for ot in fact['contenido'].split(',')
        if ot.strip()
    }}
    resultados = []
    for fact in facturas:
        if fact['contenido'].strip():
            respuesta = procesar_sincronizacion(fact, cache_obras)
            res = respuesta[0].get_json() if isinstance(respuesta, tuple) else respuesta.get_json()
            errores = res.get('errores', [])
            if res['status'] == 'error' and res.get('mensaje'): errores = [res['mensaje']]
            resultados.append({"index": fact['index'], "status": res['status'], "errores": errores})
    return jsonify({"resultados": resultados})

@app.route('/api/sincronizar', methods=['POST'])
def sincronizar(): return procesar_sincronizacion(request.json)

def procesar_sincronizacion(data, cache_obras=None):
    data = datos_sincronizacion_aprobados(data)
    if not data: return error_ruta_invalida()
    origen, factura_nombre = data['ruta'], data['nombre']
    ots = [ot.strip() for ot in data.get('contenido', '').split(',') if ot.strip()]
    try:
        guardar_ot_metadata(origen, data['contenido'])
    except Exception:
        return jsonify({"status": "error", "mensaje": "No se pudieron guardar los codigos OT."})

    cache_obras = cache_obras if cache_obras is not None else {}
    errores = []
    try:
        for ot in ots:
            sincronizada = False
            fallo_copia = False
            ot_encontrada = False
            metadata_denegada = False
            candidatos_directos = [normalizar_codigo_ot(ot).upper()]
            if componente_aprobado(ot): candidatos_directos.append(ot)
            for candidato in dict.fromkeys(candidatos_directos):
                destino_base = ruta_aprobada(BASE_OBRAS, candidato)
                if not destino_base: continue
                try:
                    os.stat(destino_base)
                except FileNotFoundError:
                    continue
                except OSError:
                    ot_encontrada = True
                    metadata_denegada = True
                    continue
                if not os.path.isdir(destino_base): continue
                ot_encontrada = True
                destino_final = ruta_aprobada(destino_base, "Pensiones y almuerzos", factura_nombre)
                if destino_final:
                    try:
                        sincronizar_carpetas_python(origen, destino_final)
                        sincronizada = True
                        break
                    except Exception:
                        fallo_copia = True
            if not sincronizada:
                if 'carpetas' not in cache_obras:
                    cache_obras['carpetas'] = listar_carpetas_obras(cache_obras.get('ots_pendientes', [ot]))
                carpetas_obras = cache_obras['carpetas']
                if carpetas_obras is None:
                    return jsonify({"status": "error", "mensaje": "No se pudo acceder a las carpetas de obras."})
                ot_clean = normalizar_codigo_ot(ot)
                for c in carpetas_obras:
                    nombre_carpeta = os.path.basename(c)
                    if not coincide_codigo_ot(nombre_carpeta, ot_clean): continue
                    ot_encontrada = True
                    destino_base = ruta_aprobada(BASE_OBRAS, *c.split(os.sep))
                    if not destino_base: continue
                    try:
                        os.stat(destino_base)
                    except OSError:
                        continue
                    if not os.path.isdir(destino_base): continue
                    destino_final = ruta_aprobada(destino_base, "Pensiones y almuerzos", factura_nombre)
                    if not destino_final: continue
                    try:
                        sincronizar_carpetas_python(origen, destino_final)
                        sincronizada = True
                        break
                    except Exception:
                        fallo_copia = True
            if not sincronizada:
                if fallo_copia: errores.append(f"No se pudo copiar la carpeta de factura en la OT {ot}.")
                elif ot_encontrada:
                    sufijo = "." if metadata_denegada else " en obras."
                    errores.append(f"No se pudo acceder a la carpeta de la OT {ot}{sufijo}")
                else: errores.append(f"La OT {ot} no existe en obras.")
    except Exception:
        return jsonify({"status": "error", "mensaje": "No se pudo completar la sincronización."})
    if errores: return jsonify({"status": "warning", "errores": errores})
    try:
        actualizar_estado_sync(origen, ots)
    except Exception:
        return jsonify({"status": "error", "mensaje": "No se pudo registrar el estado de sincronizacion."})
    return jsonify({"status": "ok"})
# Módulo opcional e independiente para importes de facturas.
from factura_montos import registrar_rutas_montos
registrar_rutas_montos(app, BASE_FACTURAS, ruta_factura_aprobada, ruta_aprobada)

if __name__ == '__main__':
    app.run(host=APP_HOST, debug=False, use_reloader=False, port=APP_PORT)
