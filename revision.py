"""Cola de revisión no destructiva para situaciones fuera del patrón esperado.

Este módulo no corrige ni borra nada. Sólo detecta estados que merecen revisión
humana para evitar que una inferencia silenciosa termine alterando datos.
"""
import json
import os
from collections import Counter

from flask import jsonify, request

from factura_montos import es_factura, numero_factura

COBRO_MANUAL = '.cobro_manual.json'
OT_NUEVO = '.OT.txt'
OT_LEGACY = 'OT.txt'
SYNC_STATE = '.sync_state.json'


def _leer_json(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as entrada:
            data = json.load(entrada)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _item(carpeta, codigo, mensaje, severidad='warning', sugerencia='Revisar manualmente.'):
    return {
        'carpeta': os.path.basename(carpeta),
        'ruta': carpeta,
        'codigo': codigo,
        'mensaje': mensaje,
        'severidad': severidad,
        'sugerencia': sugerencia,
    }


def detectar_carpeta(carpeta):
    hallazgos = []
    try:
        nombres = os.listdir(carpeta)
    except OSError:
        return [_item(
            carpeta,
            'carpeta_inaccesible',
            'No se pudo leer la carpeta.',
            'danger',
            'Comprueba permisos o conexión al servidor.',
        )]

    archivos = [n for n in nombres if os.path.isfile(os.path.join(carpeta, n))]
    facturas = [n for n in archivos if es_factura(n)]
    manual_path = os.path.join(carpeta, COBRO_MANUAL)
    tiene_manual = os.path.isfile(manual_path)

    documentos_visibles = [
        n for n in archivos
        if n.lower() not in {
            '.ot.txt', 'ot.txt', '.sync_state.json', 'ignorado.txt',
            '.factura_montos.json', '.cobro_manual.json', '.cobro_manual.lock',
        }
    ]

    if not facturas:
        manual = _leer_json(manual_path) if tiene_manual else None
        monto = manual.get('monto') if isinstance(manual, dict) else None

        if tiene_manual and manual is None:
            hallazgos.append(_item(
                carpeta,
                'cobro_manual_invalido',
                'Los datos del cobro manual no se pueden leer.',
                'danger',
                'Abre la carpeta y vuelve a ingresar el monto manual.',
            ))
        elif type(monto) is not int or monto <= 0:
            mensaje = (
                'Carpeta vacía sin factura ni monto manual.'
                if not documentos_visibles
                else 'Carpeta sin factura reconocida y sin monto manual.'
            )
            hallazgos.append(_item(
                carpeta,
                'sin_factura_sin_monto',
                mensaje,
                'warning',
                'Confirma si falta una factura o ingresa el monto manual en $.',
            ))
    else:
        if tiene_manual:
            hallazgos.append(_item(
                carpeta,
                'cobro_manual_con_factura',
                'La carpeta ya contiene una factura, pero conserva datos de cobro manual.',
                'warning',
                'La app no suma el cobro manual; revisa si esos datos antiguos deben conservarse.',
            ))

        numeros = [numero_factura(nombre) for nombre in facturas]
        repetidos = sorted(numero for numero, cantidad in Counter(numeros).items() if numero and cantidad > 1)
        if repetidos:
            hallazgos.append(_item(
                carpeta,
                'factura_duplicada',
                'Hay números de factura repetidos: ' + ', '.join(repetidos) + '.',
                'danger',
                'Revisa los archivos duplicados antes de usar los totales.',
            ))

        # La cola de revisión no analiza PDFs ni escribe metadata.
        # Sólo inspecciona resultados que ya existen.
        montos_path = os.path.join(carpeta, '.factura_montos.json')
        if os.path.isfile(montos_path):
            montos_meta = _leer_json(montos_path)
            if montos_meta is None:
                hallazgos.append(_item(
                    carpeta,
                    'metadata_montos_invalida',
                    'Los datos guardados del análisis de facturas no se pueden leer.',
                    'warning',
                    'Abre $ y vuelve a actualizar los montos.',
                ))
            else:
                documentos = montos_meta.get('documentos', {})
                if isinstance(documentos, dict):
                    vistos = set()
                    for nombre in facturas:
                        doc = documentos.get(nombre)
                        if not isinstance(doc, dict):
                            continue
                        estado = str(doc.get('estado') or '')
                        if estado in {'extraido', 'manual'}:
                            continue
                        clave = (estado, doc.get('motivo') or '')
                        if clave in vistos:
                            continue
                        vistos.add(clave)
                        motivo = doc.get('motivo') or 'La factura requiere revisión.'
                        hallazgos.append(_item(
                            carpeta,
                            'factura_' + (estado or 'desconocida'),
                            motivo,
                            'danger' if estado == 'duplicado' else 'warning',
                            'Abre $ y revisa o corrige los datos de la factura.',
                        ))

    if os.path.isfile(os.path.join(carpeta, OT_NUEVO)) and os.path.isfile(os.path.join(carpeta, OT_LEGACY)):
        hallazgos.append(_item(
            carpeta,
            'ot_metadata_duplicada',
            'Existen .OT.txt y OT.txt al mismo tiempo.',
            'warning',
            'La app usa .OT.txt; revisa el archivo legado si el contenido difiere.',
        ))

    state_path = os.path.join(carpeta, SYNC_STATE)
    if os.path.isfile(state_path) and _leer_json(state_path) is None:
        hallazgos.append(_item(
            carpeta,
            'sync_state_invalido',
            'El estado de sincronización no se puede leer.',
            'warning',
            'No se modifica automáticamente; revisa la carpeta y vuelve a sincronizar cuando corresponda.',
        ))

    return hallazgos


def detectar_semana(carpeta_semana):
    items = []
    for nombre in sorted(os.listdir(carpeta_semana), key=str.casefold):
        carpeta = os.path.join(carpeta_semana, nombre)
        if not os.path.isdir(carpeta) or os.path.islink(carpeta):
            continue
        items.extend(detectar_carpeta(carpeta))

    orden = {'danger': 0, 'warning': 1, 'info': 2}
    items.sort(key=lambda x: (orden.get(x['severidad'], 9), x['carpeta'].casefold(), x['codigo']))
    return {
        'items': items,
        'total': len(items),
        'danger': sum(1 for x in items if x['severidad'] == 'danger'),
        'warning': sum(1 for x in items if x['severidad'] == 'warning'),
    }


def registrar_rutas_revision(app, base_facturas, ruta_aprobada):
    @app.get('/api/revision')
    def api_revision():
        semana = request.args.get('semana', '')
        if (
            not isinstance(semana, str)
            or not semana.strip()
            or semana in {'.', '..'}
            or '/' in semana
            or '\\' in semana
        ):
            return jsonify(error='Semana no válida.'), 400

        ruta = ruta_aprobada(base_facturas, semana)
        if not ruta or not os.path.isdir(ruta):
            return jsonify(error='Semana no encontrada.'), 404

        try:
            return jsonify(detectar_semana(ruta))
        except OSError:
            return jsonify(error='No se pudo revisar la semana.'), 500
