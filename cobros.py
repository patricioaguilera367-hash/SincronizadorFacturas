"""Cobros manuales asociados a carpetas de semana.

Cada cobro sin factura vive en una carpeta real de la semana. Si una carpeta no
contiene una factura F N°, aparece como candidato de cobro manual. Guardar un
cobro nuevo crea la carpeta; guardar sobre una carpeta existente crea/actualiza
su metadata interna.
"""
import json
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from flask import jsonify, request

from factura_montos import es_factura

METADATA_COBRO = '.cobro_manual.json'
LOCK_COBRO = '.cobro_manual.lock'
TIPOS = {'transferencia', 'abono'}
ESTADOS = {'pendiente', 'realizado'}


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _componente(valor):
    return (
        isinstance(valor, str)
        and bool(valor.strip())
        and valor not in {'.', '..'}
        and not os.path.isabs(valor)
        and '/' not in valor
        and '\\' not in valor
    )


def _texto(valor, maximo):
    if valor is None:
        return ''
    if not isinstance(valor, str):
        raise ValueError('Texto inválido.')
    valor = ' '.join(valor.split()).strip()
    if len(valor) > maximo:
        raise ValueError('Uno de los textos es demasiado largo.')
    return valor


def _monto(valor, *, requerido=True):
    if valor is None and not requerido:
        return None
    if type(valor) is not int or valor <= 0 or valor > 10**12:
        raise ValueError('El monto debe ser un entero positivo en CLP.')
    return valor


def _ruta_metadata(carpeta):
    return os.path.join(carpeta, METADATA_COBRO)


def _leer_metadata(carpeta):
    try:
        with open(_ruta_metadata(carpeta), 'r', encoding='utf-8') as entrada:
            data = json.load(entrada)
        return data if isinstance(data, dict) else None
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return None


def _guardar_metadata(carpeta, data):
    fd, temporal = tempfile.mkstemp(prefix='.cobro-', suffix='.tmp', dir=carpeta)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as salida:
            json.dump(data, salida, ensure_ascii=False, indent=2)
        os.replace(temporal, _ruta_metadata(carpeta))
    finally:
        if os.path.exists(temporal):
            try:
                os.unlink(temporal)
            except OSError:
                pass


def _tiene_factura(carpeta):
    try:
        return any(
            es_factura(nombre) and os.path.isfile(os.path.join(carpeta, nombre))
            for nombre in os.listdir(carpeta)
        )
    except OSError:
        # Si no podemos inspeccionarla, no la tratamos como cobro manual.
        return True


def _leer_ot(carpeta):
    for nombre in ('.OT.txt', 'OT.txt'):
        try:
            with open(os.path.join(carpeta, nombre), 'r', encoding='utf-8') as entrada:
                return entrada.read().strip()
        except OSError:
            continue
    return ''


@contextmanager
def _bloqueo(carpeta, espera=4.0, stale=45.0):
    """Lock cooperativo por carpeta; también sirve entre clientes vía SMB."""
    ruta = os.path.join(carpeta, LOCK_COBRO)
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
                raise TimeoutError('Otro equipo está actualizando esta carpeta. Intenta nuevamente.')
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


def _registro(carpeta):
    meta = _leer_metadata(carpeta) or {}
    monto = meta.get('monto')
    if type(monto) is not int or monto <= 0:
        monto = None
    estado = meta.get('estado') if meta.get('estado') in ESTADOS else 'pendiente'
    tipo = meta.get('tipo') if meta.get('tipo') in TIPOS else 'transferencia'

    return {
        'carpeta': os.path.basename(carpeta),
        'ruta': carpeta,
        'detalle': _texto(meta.get('detalle', ''), 180),
        'tipo': tipo,
        'monto': monto,
        'estado': estado,
        'ot': _leer_ot(carpeta),
        'configurado': monto is not None,
        'actualizado': meta.get('actualizado'),
    }


def _presentar_semana(carpeta_semana):
    items = []
    for nombre in sorted(os.listdir(carpeta_semana), key=str.casefold):
        carpeta = os.path.join(carpeta_semana, nombre)
        if not os.path.isdir(carpeta) or os.path.islink(carpeta):
            continue
        if _tiene_factura(carpeta):
            continue
        items.append(_registro(carpeta))

    items.sort(key=lambda x: (
        x.get('estado') == 'realizado',
        x.get('monto') is not None,
        x.get('carpeta', '').casefold(),
    ))

    pendientes = [x for x in items if x.get('estado') == 'pendiente' and x.get('monto')]
    realizados = [x for x in items if x.get('estado') == 'realizado' and x.get('monto')]
    sin_monto = [x for x in items if not x.get('monto')]

    return {
        'items': items,
        'pendiente_total': sum(x['monto'] for x in pendientes),
        'realizado_total': sum(x['monto'] for x in realizados),
        'pendientes': len(pendientes),
        'realizados': len(realizados),
        'sin_monto': len(sin_monto),
    }


def registrar_rutas_cobros(app, base_facturas, ruta_aprobada):
    def semana_valida(nombre):
        if not _componente(nombre):
            return None
        ruta = ruta_aprobada(base_facturas, nombre)
        return ruta if ruta and os.path.isdir(ruta) else None

    def carpeta_valida(semana, nombre):
        if not _componente(nombre):
            return None
        ruta = ruta_aprobada(semana, nombre)
        return ruta if ruta and os.path.isdir(ruta) and not os.path.islink(ruta) else None

    @app.get('/api/cobros')
    def api_cobros():
        semana = semana_valida(request.args.get('semana', ''))
        if not semana:
            return jsonify(error='Semana no válida.'), 400
        try:
            return jsonify(_presentar_semana(semana))
        except OSError:
            return jsonify(error='No se pudieron leer las carpetas de la semana.'), 500

    @app.post('/api/cobros/guardar')
    def api_cobros_guardar():
        payload = request.get_json(silent=True) or {}
        semana = semana_valida(payload.get('semana', ''))
        if not semana:
            return jsonify(error='Semana no válida.'), 400

        nombre_nuevo = payload.get('carpeta')
        nombre_actual = payload.get('carpeta_actual')
        if isinstance(nombre_nuevo, str):
            nombre_nuevo = nombre_nuevo.strip()
        if isinstance(nombre_actual, str):
            nombre_actual = nombre_actual.strip()
        if not _componente(nombre_nuevo):
            return jsonify(error='El nombre de carpeta no es válido.'), 400

        tipo = payload.get('tipo', 'transferencia')
        estado = payload.get('estado', 'pendiente')
        try:
            detalle = _texto(payload.get('detalle', ''), 180)
            monto = _monto(payload.get('monto'))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        if tipo not in TIPOS or estado not in ESTADOS:
            return jsonify(error='Tipo o estado de cobro inválido.'), 400

        creada = False
        carpeta = None
        try:
            if nombre_actual:
                carpeta = carpeta_valida(semana, nombre_actual)
                if not carpeta:
                    return jsonify(error='La carpeta ya no existe.'), 404
                if _tiene_factura(carpeta):
                    return jsonify(error='Esta carpeta ya contiene una factura y usa el flujo de facturación.'), 409

                if nombre_nuevo != nombre_actual:
                    destino = ruta_aprobada(semana, nombre_nuevo)
                    if not destino:
                        return jsonify(error='El nuevo nombre no es válido.'), 400
                    if os.path.exists(destino):
                        return jsonify(error='Ya existe una carpeta con ese nombre.'), 409
                    os.rename(carpeta, destino)
                    carpeta = destino
            else:
                carpeta = ruta_aprobada(semana, nombre_nuevo)
                if not carpeta:
                    return jsonify(error='La carpeta no es válida.'), 400
                if os.path.exists(carpeta):
                    return jsonify(error='Esa carpeta ya existe; edítala desde la lista de cobros.'), 409
                os.mkdir(carpeta)
                creada = True

            with _bloqueo(carpeta):
                anterior = _leer_metadata(carpeta) or {}
                data = {
                    'version': 1,
                    'detalle': detalle,
                    'tipo': tipo,
                    'monto': monto,
                    'estado': estado,
                    'creado': anterior.get('creado') or _ahora(),
                    'actualizado': _ahora(),
                }
                _guardar_metadata(carpeta, data)

            return jsonify(status='ok', creada=creada, **_presentar_semana(semana))
        except TimeoutError as exc:
            return jsonify(error=str(exc)), 409
        except OSError:
            return jsonify(error='No se pudo crear o actualizar la carpeta de cobro.'), 500

    @app.post('/api/cobros/estado')
    def api_cobros_estado():
        payload = request.get_json(silent=True) or {}
        semana = semana_valida(payload.get('semana', ''))
        carpeta = carpeta_valida(semana, payload.get('carpeta')) if semana else None
        estado = payload.get('estado')
        if not carpeta or estado not in ESTADOS:
            return jsonify(error='Datos de cobro inválidos.'), 400
        if _tiene_factura(carpeta):
            return jsonify(error='Esta carpeta contiene una factura.'), 409

        try:
            with _bloqueo(carpeta):
                data = _leer_metadata(carpeta)
                if not data or type(data.get('monto')) is not int:
                    return jsonify(error='Primero ingresa el monto manual.'), 409
                data['estado'] = estado
                data['actualizado'] = _ahora()
                _guardar_metadata(carpeta, data)
            return jsonify(status='ok', **_presentar_semana(semana))
        except TimeoutError as exc:
            return jsonify(error=str(exc)), 409
        except OSError:
            return jsonify(error='No se pudo actualizar el cobro.'), 500

    @app.post('/api/cobros/limpiar')
    def api_cobros_limpiar():
        """Quita sólo los datos manuales; nunca elimina la carpeta ni sus archivos."""
        payload = request.get_json(silent=True) or {}
        semana = semana_valida(payload.get('semana', ''))
        carpeta = carpeta_valida(semana, payload.get('carpeta')) if semana else None
        if not carpeta:
            return jsonify(error='Carpeta inválida.'), 400

        try:
            with _bloqueo(carpeta):
                ruta = _ruta_metadata(carpeta)
                if os.path.exists(ruta):
                    os.remove(ruta)
            return jsonify(status='ok', **_presentar_semana(semana))
        except TimeoutError as exc:
            return jsonify(error=str(exc)), 409
        except OSError:
            return jsonify(error='No se pudo quitar el monto manual.'), 500
