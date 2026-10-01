"""Módulo aislado: lectura y registro de montos para documentos F N°... .

No modifica el flujo de sincronización de OT. Las imágenes quedan pendientes
para digitación manual: no se supone que el OCR de una foto sea fiable.
"""
import json
import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from threading import RLock

from flask import jsonify, request

LOG = logging.getLogger(__name__)
METADATA = '.factura_montos.json'
_LOCK = RLock()
# La coincidencia DEBE comenzar al principio: DETALLE F N°... no califica.
FACTURA = re.compile(r'^F\s*N\s*[°º]\s*([0-9]+)(?![0-9])', re.I)
PDF = {'.pdf'}
FOTOS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif', '.heic'}
VALIDOS = PDF | FOTOS
ETIQUETAS = {
    'neto': [r'MONTO\s+NETO', r'VALOR\s+NETO', r'NETO'],
    'iva': [r'I\s*\.?\s*V\s*\.?\s*A\s*\.?\s*(?:\(?19\s*%\)?)?'],
    'total': [r'(?:MONTO\s+)?TOTAL\s+(?:A\s+PAGAR)?', r'TOTAL'],
}
IMPORTE = re.compile(r'(?<![\w\d])\$?\s*(\d{1,3}(?:[.,]\d{3})+|\d{1,10})(?!\d)')


def es_factura(nombre):
    if not isinstance(nombre, str):
        return False
    return bool(FACTURA.match(nombre)) and os.path.splitext(nombre)[1].lower() in VALIDOS


def numero_factura(nombre):
    m = FACTURA.match(nombre)
    return str(int(m.group(1))) if m else None


def leer_pdf(ruta):
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError('Instala PyMuPDF: python -m pip install pymupdf') from exc
    doc = fitz.open(ruta)
    try:
        if doc.needs_pass:
            raise ValueError('PDF protegido con contraseña')
        if len(doc) > 15:
            raise ValueError('PDF demasiado largo para una factura')
        return '\n'.join(pagina.get_text(sort=True) for pagina in doc)
    finally:
        doc.close()


def numero_clp(texto):
    """Facturas chilenas CLP: 123.529 / 123529 / 123,529."""
    texto = texto.strip().replace(' ', '')
    if '.' in texto and ',' in texto:
        return None  # formato ambiguo: revisión manual
    if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', texto):
        return int(re.sub(r'[.,]', '', texto))
    if re.fullmatch(r'\d{1,10}', texto):
        return int(texto)
    return None


def importes_despues_etiqueta(linea, tipo):
    """Busca cifras después de una etiqueta, no antes de ella."""
    for etiqueta in ETIQUETAS[tipo]:
        for match in re.finditer(r'(?<![A-Z])' + etiqueta + r'(?![A-Z])', linea, flags=re.I):
            resto = linea[match.end():]
            # OCR/tabla puede añadir etiquetas de otros campos a la derecha.
            resto = re.split(r'(?<![A-Z])(?:MONTO\s+NETO|VALOR\s+NETO|NETO|I\s*\.?V\s*\.?A|TOTAL)(?![A-Z])', resto, maxsplit=1, flags=re.I)[0]
            hallados = [(numero_clp(m.group(1)), m.start()) for m in IMPORTE.finditer(resto[:55])]
            hallados = [(n, p) for n, p in hallados if n is not None]
            if hallados:
                # Si aparecen montos adicionales en la misma línea, evitamos elegir arbitrariamente.
                valores = {n for n, _ in hallados}
                if len(valores) == 1:
                    yield hallados[0][0]


def extraer_importes(texto):
    if not texto or not texto.strip():
        return None, 'PDF sin texto seleccionable (escaneado); ingresa los montos manualmente.'
    lineas = [re.sub(r'\s+', ' ', l).strip() for l in texto.splitlines() if l.strip()]
    encontrados = {tipo: set() for tipo in ETIQUETAS}
    for tipo in ETIQUETAS:
        for i, linea in enumerate(lineas):
            # Etiqueta al final de línea con cantidad debajo: permitir línea siguiente
            for numero in importes_despues_etiqueta(linea, tipo):
                encontrados[tipo].add(numero)
            if re.fullmatch(r'(?:' + '|'.join(ETIQUETAS[tipo]) + r')\s*[:$\s]*', linea, flags=re.I) and i + 1 < len(lineas):
                siguiente = re.fullmatch(r'\$?\s*(\d{1,3}(?:[.,]\d{3})+|\d{1,10})', lineas[i + 1])
                if siguiente:
                    n = numero_clp(siguiente.group(1))
                    if n is not None:
                        encontrados[tipo].add(n)
    if any(len(v) != 1 for v in encontrados.values()):
        return None, 'No se pudieron identificar tres montos únicos; revisar manualmente.'
    montos = {tipo: next(iter(valores)) for tipo, valores in encontrados.items()}
    if any(n < 0 for n in montos.values()):
        return None, 'Importes inválidos.'
    if abs(montos['neto'] + montos['iva'] - montos['total']) > 2:
        return None, 'Neto + IVA no coincide con total; revisar posibles impuestos adicionales.'
    return montos, None


def _archivo_metadata(carpeta):
    return os.path.join(carpeta, METADATA)


def _leer_metadata(carpeta):
    try:
        with open(_archivo_metadata(carpeta), encoding='utf-8') as entrada:
            contenido = json.load(entrada)
        if contenido.get('version') == 1 and isinstance(contenido.get('documentos'), dict):
            return contenido
    except (FileNotFoundError, ValueError, OSError, TypeError):
        pass
    return {'version': 1, 'documentos': {}}


def _guardar_metadata(carpeta, contenido):
    # Escritura atómica dentro de la misma carpeta SMB para no dejar JSON truncado.
    descriptor, tmp = tempfile.mkstemp(prefix='.montos-', suffix='.tmp', dir=carpeta)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as salida:
            json.dump(contenido, salida, ensure_ascii=False, indent=2)
        os.replace(tmp, _archivo_metadata(carpeta))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _huella(ruta):
    stat = os.stat(ruta)
    return {'tamano': stat.st_size, 'mtime_ns': stat.st_mtime_ns}


def _extraer_uno(ruta):
    nombre = os.path.basename(ruta)
    base = {'archivo': nombre, 'numero': numero_factura(nombre), 'huella': _huella(ruta), 'actualizado': datetime.now(timezone.utc).isoformat()}
    if os.path.splitext(nombre)[1].lower() not in PDF:
        return {**base, 'estado': 'manual_pendiente', 'motivo': 'Imagen: ingresa los montos manualmente.', 'montos': None}
    try:
        montos, motivo = extraer_importes(leer_pdf(ruta))
        return {**base, 'estado': 'extraido' if montos else 'manual_pendiente', 'motivo': motivo, 'montos': montos}
    except Exception as exc:
        LOG.warning('No se pudo leer la factura PDF %s: %s', nombre, exc)
        return {**base, 'estado': 'manual_pendiente', 'motivo': str(exc), 'montos': None}


def _listado(carpeta):
    return sorted([n for n in os.listdir(carpeta) if es_factura(n) and os.path.isfile(os.path.join(carpeta, n))], key=str.casefold)


def actualizar_carpeta(carpeta, forzar=False):
    """Actualiza pendientes y documentos cambiados; respeta importes manuales vigentes."""
    with _LOCK:
        datos = _leer_metadata(carpeta)
        archivos = _listado(carpeta)
        agrupados = {}
        for nombre in archivos:
            agrupados.setdefault(numero_factura(nombre), []).append(nombre)
        documentos = datos['documentos']
        cambios = False
        for nombre in archivos:
            ruta = os.path.join(carpeta, nombre)
            huella = _huella(ruta)
            anterior = documentos.get(nombre)
            if anterior and anterior.get('huella') == huella and anterior.get('estado') == 'manual':
                continue  # nunca reemplazar digitación manual sin que el archivo cambie
            if anterior and anterior.get('huella') == huella and not forzar:
                continue
            documentos[nombre] = _extraer_uno(ruta)
            cambios = True
        # No descartar historiales si el archivo se elimina, pero no contarlos en la vista.
        if cambios:
            _guardar_metadata(carpeta, datos)
        salida = []
        for numero, nombres in agrupados.items():
            duplicados = len(nombres) > 1
            for nombre in nombres:
                registro = dict(documentos[nombre])
                if duplicados:
                    registro['estado'] = 'duplicado'
                    registro['motivo'] = 'Mismo número de factura en más de un archivo. Revisar antes de sumar.'
                salida.append(registro)
        return salida


def actualizar_archivo_cargado(carpeta, ruta):
    """Se invoca solo al subir una factura válida. Sin OCR en fotos."""
    if es_factura(os.path.basename(ruta)):
        with _LOCK:
            datos = _leer_metadata(carpeta)
            datos['documentos'][os.path.basename(ruta)] = _extraer_uno(ruta)
            _guardar_metadata(carpeta, datos)


def resumen(carpeta):
    registros = actualizar_carpeta(carpeta)
    suma = {'neto': 0, 'iva': 0, 'total': 0}
    pendientes = 0
    for registro in registros:
        if registro['estado'] not in {'extraido', 'manual'} or not registro.get('montos'):
            pendientes += 1
            continue
        for clave in suma:
            suma[clave] += registro['montos'][clave]
    return {'documentos': registros, 'sumas': suma, 'pendientes': pendientes}


def registrar_rutas_montos(app, base_facturas, validar_factura, ruta_aprobada):
    """Los controladores reutilizan el validador de carpetas del proyecto."""
    def carpeta_valida(valor):
        aprobada = validar_factura(valor)
        if not aprobada or not os.path.isdir(aprobada):
            return None
        return aprobada

    @app.get('/api/montos')
    def api_montos():
        semana = request.args.get('semana', '')
        if not isinstance(semana, str) or not semana or semana in {'.', '..'} or '/' in semana or '\\' in semana:
            return jsonify(error='Semana no válida'), 400
        ruta_semana = ruta_aprobada(base_facturas, semana)
        if not ruta_semana or not os.path.isdir(ruta_semana):
            return jsonify(error='Semana no encontrada'), 404
        try:
            filas = []
            suma = {'neto': 0, 'iva': 0, 'total': 0}
            pendientes = 0
            for nombre in sorted(os.listdir(ruta_semana), key=str.casefold):
                carpeta = ruta_aprobada(ruta_semana, nombre)
                if not carpeta or not os.path.isdir(carpeta) or os.path.islink(carpeta):
                    continue
                if os.path.exists(os.path.join(carpeta, 'ignorado.txt')):
                    continue
                resultado = resumen(carpeta)
                ot = ''
                try:
                    with open(os.path.join(carpeta, 'OT.txt'), encoding='utf-8') as entrada:
                        ot = entrada.read().strip()
                except OSError:
                    pass
                for doc in resultado['documentos']:
                    filas.append({**doc, 'carpeta': nombre, 'ruta': carpeta, 'ot': ot})
                for tipo in suma:
                    suma[tipo] += resultado['sumas'][tipo]
                pendientes += resultado['pendientes']
            return jsonify(filas=filas, sumas=suma, pendientes=pendientes)
        except OSError:
            LOG.exception('Error leyendo resumen de montos')
            return jsonify(error='No se pudo acceder a los archivos de esta semana.'), 500

    @app.post('/api/montos/actualizar')
    def api_montos_actualizar():
        data = request.get_json(silent=True) or {}
        carpeta = carpeta_valida(data.get('ruta'))
        if not carpeta:
            return jsonify(error='Carpeta de factura inválida'), 400
        try:
            return jsonify(resultado=resumen_forzado(carpeta))
        except OSError:
            LOG.exception('Error actualizando montos')
            return jsonify(error='No se pudieron actualizar los montos.'), 500

    @app.post('/api/montos/actualizar_semana')
    def api_montos_actualizar_semana():
        data = request.get_json(silent=True) or {}
        semana = data.get('semana', '')
        if not isinstance(semana, str) or not semana or semana in {'.', '..'} or '/' in semana or '\\' in semana:
            return jsonify(error='Semana inválida'), 400
        ruta_semana = ruta_aprobada(base_facturas, semana)
        if not ruta_semana or not os.path.isdir(ruta_semana):
            return jsonify(error='Semana no encontrada'), 404
        try:
            actualizadas = 0
            for nombre in os.listdir(ruta_semana):
                carpeta = ruta_aprobada(ruta_semana, nombre)
                if not carpeta or not os.path.isdir(carpeta) or os.path.islink(carpeta):
                    continue
                if os.path.isfile(os.path.join(carpeta, 'ignorado.txt')):
                    continue
                actualizar_carpeta(carpeta, forzar=True)
                actualizadas += 1
            return jsonify(status='ok', carpetas=actualizadas)
        except OSError:
            LOG.exception('Error actualizando montos de semana')
            return jsonify(error='No se pudo completar la actualización.'), 500

    @app.post('/api/montos/manual')
    def api_montos_manual():
        data = request.get_json(silent=True) or {}
        carpeta = carpeta_valida(data.get('ruta'))
        archivo = data.get('archivo')
        if not carpeta or not isinstance(archivo, str) or os.path.basename(archivo) != archivo or not es_factura(archivo):
            return jsonify(error='Archivo o carpeta inválidos'), 400
        destino = ruta_aprobada(carpeta, archivo)
        if not destino or not os.path.isfile(destino):
            return jsonify(error='La factura no existe'), 404
        montos = data.get('montos')
        if not isinstance(montos, dict) or any(type(montos.get(k)) is not int or montos[k] < 0 or montos[k] > 10**12 for k in ('neto', 'iva', 'total')):
            return jsonify(error='Los importes deben ser enteros positivos en CLP'), 400
        with _LOCK:
            datos = _leer_metadata(carpeta)
            datos['documentos'][archivo] = {
                'archivo': archivo, 'numero': numero_factura(archivo), 'huella': _huella(destino),
                'actualizado': datetime.now(timezone.utc).isoformat(), 'estado': 'manual',
                'motivo': ('Revisado manualmente: el total difiere de neto + IVA (pueden existir impuestos adicionales).'
                            if abs(montos['neto'] + montos['iva'] - montos['total']) > 2 else None),
                'montos': {k: montos[k] for k in ('neto', 'iva', 'total')},
            }
            try:
                _guardar_metadata(carpeta, datos)
            except OSError:
                LOG.exception('No se pudieron guardar montos manuales')
                return jsonify(error='No se pudieron guardar los importes.'), 500
        return jsonify(status='ok')


def resumen_forzado(carpeta):
    # Reanaliza sólo documentos no manuales, y conserva digitaciones válidas.
    actualizar_carpeta(carpeta, forzar=True)
    return resumen(carpeta)
