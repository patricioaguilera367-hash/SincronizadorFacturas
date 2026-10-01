"""Cobros sin factura por semana.

Guarda transferencias/abonos que no tienen DTE asociado en un JSON interno
dentro de la carpeta semanal. El archivo vive en el servidor compartido para
que todos los clientes vean el mismo estado.
"""
import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from flask import jsonify, request

METADATA_COBROS = '.cobros_pendientes.json'
LOCK_COBROS = '.cobros_pendientes.lock'
TIPOS = {'transferencia', 'abono'}
ESTADOS = {'pendiente', 'realizado'}


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _texto(valor, maximo, *, requerido=False):
    if valor is None:
        valor = ''
    if not isinstance(valor, str):
        raise ValueError('Texto inválido.')
    valor = ' '.join(valor.split()).strip()
    if requerido and not valor:
        raise ValueError('Falta un campo obligatorio.')
    if len(valor) > maximo:
        raise ValueError('Uno de los textos es demasiado largo.')
    return valor


def _monto(valor):
    if type(valor) is not int or valor <= 0 or valor > 10**12:
        raise ValueError('El monto debe ser un entero positivo en CLP.')
    return valor


def _ruta_metadata(carpeta_semana):
    return os.path.join(carpeta_semana, METADATA_COBROS)


def _leer(carpeta_semana):
    try:
        with open(_ruta_metadata(carpeta_semana), 'r', encoding='utf-8') as entrada:
            data = json.load(entrada)
        items = data.get('items', []) if isinstance(data, dict) else []
        return {'version': 1, 'items': [x for x in items if isinstance(x, dict)]}
    except (FileNotFoundError, OSError, ValueError, TypeError, AttributeError):
        return {'version': 1, 'items': []}


def _guardar(carpeta_semana, data):
    data = {'version': 1, 'items': data.get('items', [])}
    fd, temporal = tempfile.mkstemp(prefix='.cobros-', suffix='.tmp', dir=carpeta_semana)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as salida:
            json.dump(data, salida, ensure_ascii=False, indent=2)
        os.replace(temporal, _ruta_metadata(carpeta_semana))
    finally:
        if os.path.exists(temporal):
            try:
                os.unlink(temporal)
            except OSError:
                pass


@contextmanager
def _bloqueo(carpeta_semana, espera=4.0, stale=45.0):
    """Lock cooperativo por archivo, válido también entre PCs sobre SMB."""
    ruta = os.path.join(carpeta_semana, LOCK_COBROS)
    limite = time.monotonic() + espera
    descriptor = None

    while descriptor is None:
        try:
            descriptor = os.open(ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f'{os.getpid()} {_ahora()}'.encode('utf-8'))
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(ruta) > stale:
                    os.unlink(ruta)
                    continue
            except OSError:
                pass
            if time.monotonic() >= limite:
                raise TimeoutError('Otro equipo está actualizando los cobros. Intenta nuevamente.')
            time.sleep(0.08)

    try:
        yield
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        try:
            os.unlink(ruta)
        except OSError:
            pass


def _presentar(data):
    items = list(data.get('items', []))
    items.sort(key=lambda x: (x.get('estado') == 'realizado', x.get('creado', ''), x.get('nombre', '').casefold()))
    pendientes = [x for x in items if x.get('estado') == 'pendiente']
    realizados = [x for x in items if x.get('estado') == 'realizado']
    return {
        'items': items,
        'pendiente_total': sum(int(x.get('monto', 0)) for x in pendientes),
        'realizado_total': sum(int(x.get('monto', 0)) for x in realizados),
        'pendientes': len(pendientes),
        'realizados': len(realizados),
    }


def _item_desde_payload(payload, anterior=None):
    anterior = anterior or {}
    tipo = payload.get('tipo', anterior.get('tipo', 'transferencia'))
    estado = payload.get('estado', anterior.get('estado', 'pendiente'))
    if tipo not in TIPOS:
        raise ValueError('Tipo de cobro inválido.')
    if estado not in ESTADOS:
        raise ValueError('Estado de cobro inválido.')

    return {
        'id': anterior.get('id') or uuid.uuid4().hex,
        'tipo': tipo,
        'nombre': _texto(payload.get('nombre', anterior.get('nombre')), 120, requerido=True),
        'detalle': _texto(payload.get('detalle', anterior.get('detalle', '')), 180),
        'ot': _texto(payload.get('ot', anterior.get('ot', '')), 80),
        'monto': _monto(payload.get('monto', anterior.get('monto'))),
        'estado': estado,
        'creado': anterior.get('creado') or _ahora(),
        'actualizado': _ahora(),
    }


def registrar_rutas_cobros(app, base_facturas, ruta_aprobada):
    def semana_valida(nombre):
        if (
            not isinstance(nombre, str)
            or not nombre.strip()
            or nombre in {'.', '..'}
            or '/' in nombre
            or '\\' in nombre
        ):
            return None
        ruta = ruta_aprobada(base_facturas, nombre)
        return ruta if ruta and os.path.isdir(ruta) else None

    @app.get('/api/cobros')
    def api_cobros():
        semana = semana_valida(request.args.get('semana', ''))
        if not semana:
            return jsonify(error='Semana no válida.'), 400
        return jsonify(_presentar(_leer(semana)))

    @app.post('/api/cobros/guardar')
    def api_cobros_guardar():
        payload = request.get_json(silent=True) or {}
        semana = semana_valida(payload.get('semana', ''))
        if not semana:
            return jsonify(error='Semana no válida.'), 400

        try:
            with _bloqueo(semana):
                data = _leer(semana)
                identificador = payload.get('id')
                anterior = None
                if identificador:
                    anterior = next((x for x in data['items'] if x.get('id') == identificador), None)
                    if anterior is None:
                        return jsonify(error='Cobro no encontrado.'), 404
                    data['items'] = [x for x in data['items'] if x.get('id') != identificador]
                data['items'].append(_item_desde_payload(payload, anterior))
                _guardar(semana, data)
                return jsonify(status='ok', **_presentar(data))
        except (ValueError, TimeoutError) as exc:
            return jsonify(error=str(exc)), 400
        except OSError:
            return jsonify(error='No se pudo guardar el cobro en el servidor.'), 500

    @app.post('/api/cobros/estado')
    def api_cobros_estado():
        payload = request.get_json(silent=True) or {}
        semana = semana_valida(payload.get('semana', ''))
        estado = payload.get('estado')
        identificador = payload.get('id')
        if not semana or not isinstance(identificador, str) or estado not in ESTADOS:
            return jsonify(error='Datos de cobro inválidos.'), 400

        try:
            with _bloqueo(semana):
                data = _leer(semana)
                item = next((x for x in data['items'] if x.get('id') == identificador), None)
                if item is None:
                    return jsonify(error='Cobro no encontrado.'), 404
                item['estado'] = estado
                item['actualizado'] = _ahora()
                _guardar(semana, data)
                return jsonify(status='ok', **_presentar(data))
        except TimeoutError as exc:
            return jsonify(error=str(exc)), 409
        except OSError:
            return jsonify(error='No se pudo actualizar el cobro.'), 500

    @app.post('/api/cobros/eliminar')
    def api_cobros_eliminar():
        payload = request.get_json(silent=True) or {}
        semana = semana_valida(payload.get('semana', ''))
        identificador = payload.get('id')
        if not semana or not isinstance(identificador, str):
            return jsonify(error='Datos de cobro inválidos.'), 400

        try:
            with _bloqueo(semana):
                data = _leer(semana)
                originales = len(data['items'])
                data['items'] = [x for x in data['items'] if x.get('id') != identificador]
                if len(data['items']) == originales:
                    return jsonify(error='Cobro no encontrado.'), 404
                _guardar(semana, data)
                return jsonify(status='ok', **_presentar(data))
        except TimeoutError as exc:
            return jsonify(error=str(exc)), 409
        except OSError:
            return jsonify(error='No se pudo eliminar el cobro.'), 500
