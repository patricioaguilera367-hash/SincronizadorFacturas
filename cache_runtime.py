import csv
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.RLock()
SCHEMA_VERSION = 1


def _ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalizar_codigo_ot(valor):
    return re.sub(r"[^a-zA-Z0-9]+", "_", valor).strip("_").lower() if isinstance(valor, str) else ""


def coincide_codigo_ot(nombre, ot):
    codigo = normalizar_codigo_ot(nombre)
    ot = normalizar_codigo_ot(ot)
    return bool(ot) and (codigo == ot or codigo.startswith(f"{ot}_"))


def extraer_codigo_ot_nombre(nombre):
    """
    Extrae únicamente el prefijo OT que ya satisface la regla de matching actual.

    No infiere relaciones entre OT ni consecutividad. Sólo reconoce el formato
    que la app ya acepta: 000_XX_000 al comienzo del nombre normalizado.
    """
    codigo = normalizar_codigo_ot(nombre)
    match = re.match(r"^(\d{3}_[a-z]{2}_\d{3})(?:_|$)", codigo, re.IGNORECASE)
    if not match:
        return None
    candidato = match.group(1)
    return candidato if coincide_codigo_ot(nombre, candidato) else None


def _ruta(path):
    return Path(path)


def _leer_json(path, default):
    path = _ruta(path)
    try:
        with path.open("r", encoding="utf-8") as entrada:
            data = json.load(entrada)
        return data if isinstance(data, dict) else default
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def _guardar_json_atomico(path, data):
    path = _ruta(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporal = path.with_name(path.name + ".tmp")
    with temporal.open("w", encoding="utf-8") as salida:
        json.dump(data, salida, ensure_ascii=False, indent=2)
    os.replace(temporal, path)


def _rel_serializada(ruta_relativa):
    return str(ruta_relativa).replace("\\", "/").strip("/")


def _ruta_desde_relativa(base_obras, relativa):
    partes = [parte for parte in _rel_serializada(relativa).split("/") if parte]
    return os.path.join(base_obras, *partes)


def _relativa_desde_absoluta(base_obras, ruta):
    try:
        relativa = os.path.relpath(os.path.realpath(ruta), os.path.realpath(base_obras))
    except (OSError, ValueError, TypeError):
        return None
    if relativa == "." or relativa == ".." or relativa.startswith(".." + os.sep):
        return None
    return _rel_serializada(relativa)


def _indice_vacio(base_obras):
    return {
        "version": SCHEMA_VERSION,
        "root": str(base_obras),
        "updated_at": None,
        "last_scan_completed": None,
        "last_scan_status": "never",
        "entries": {},
    }


def cargar_indice(path, base_obras):
    with _LOCK:
        data = _leer_json(path, _indice_vacio(base_obras))
        if data.get("version") != SCHEMA_VERSION or not isinstance(data.get("entries"), dict):
            data = _indice_vacio(base_obras)
        data["root"] = str(base_obras)
        return data


def _entrada_indice(data, codigo):
    key = normalizar_codigo_ot(codigo)
    if not key:
        return None
    entries = data.setdefault("entries", {})
    entrada = entries.setdefault(
        key,
        {
            "codigo": key.upper(),
            "rutas": {},
        },
    )
    if not isinstance(entrada.get("rutas"), dict):
        entrada["rutas"] = {}
    return entrada


def _registrar_ruta_en_data(data, codigo, relativa, estado="activa", momento=None):
    momento = momento or _ahora()
    entrada = _entrada_indice(data, codigo)
    if entrada is None:
        return False

    relativa = _rel_serializada(relativa)
    if not relativa:
        return False

    rutas = entrada["rutas"]
    nueva = relativa not in rutas
    ruta_data = rutas.setdefault(
        relativa,
        {
            "estado": estado,
            "primera_vista": momento,
            "ultima_vista": momento,
            "ausente_desde": None,
        },
    )
    ruta_data["estado"] = estado
    ruta_data["ultima_vista"] = momento
    if estado == "activa":
        ruta_data["ausente_desde"] = None
    elif estado == "ausente" and not ruta_data.get("ausente_desde"):
        ruta_data["ausente_desde"] = momento
    return nueva


def sembrar_indice_desde_csv(path_indice, path_csv, base_obras):
    """
    Importa un snapshot opcional generado fuera del repositorio.

    Sólo se usa cuando aún no existe un índice con entradas. Las rutas quedan
    como "sin_verificar" hasta que el servidor pueda reconciliarlas.
    """
    path_csv = _ruta(path_csv)
    if not path_csv.exists():
        return {"importadas": 0, "usado": False}

    with _LOCK:
        data = cargar_indice(path_indice, base_obras)
        if data.get("entries"):
            return {"importadas": 0, "usado": False}

        try:
            momento = datetime.fromtimestamp(path_csv.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
        except OSError:
            momento = _ahora()

        base_normalizada = str(base_obras).replace("/", "\\").rstrip("\\")
        importadas = 0

        try:
            with path_csv.open("r", encoding="utf-8-sig", newline="") as entrada:
                lector = csv.DictReader(entrada)
                for row in lector:
                    nombre = str(row.get("Name") or "").strip()
                    completa = str(row.get("FullName") or "").strip()
                    if not nombre and completa:
                        nombre = completa.replace("/", "\\").rstrip("\\").split("\\")[-1]
                    codigo = extraer_codigo_ot_nombre(nombre)
                    if not codigo:
                        continue

                    relativa = ""
                    if completa:
                        completa_normalizada = completa.replace("/", "\\")
                        if completa_normalizada.lower().startswith((base_normalizada + "\\").lower()):
                            relativa = completa_normalizada[len(base_normalizada):].lstrip("\\")
                    if not relativa and nombre:
                        relativa = nombre

                    if _registrar_ruta_en_data(
                        data,
                        codigo,
                        relativa,
                        estado="sin_verificar",
                        momento=momento,
                    ):
                        importadas += 1
        except (OSError, csv.Error):
            return {"importadas": 0, "usado": False}

        data["updated_at"] = _ahora()
        data["seed_source"] = path_csv.name
        _guardar_json_atomico(path_indice, data)
        return {"importadas": importadas, "usado": True}


def reconciliar_indice_raiz(path_indice, base_obras):
    """
    Compara el índice con las carpetas de primer nivel.

    Una falla de red NO marca carpetas como ausentes. Sólo una enumeración
    completada correctamente puede producir el estado "ausente".
    """
    inicio = _ahora()
    try:
        with os.scandir(base_obras) as entradas:
            nombres = [
                item.name
                for item in entradas
                if item.is_dir(follow_symlinks=False)
            ]
    except OSError as exc:
        with _LOCK:
            data = cargar_indice(path_indice, base_obras)
            data["last_scan_status"] = "unavailable"
            data["updated_at"] = _ahora()
            data["last_error"] = str(exc)
            _guardar_json_atomico(path_indice, data)
        return {
            "ok": False,
            "agregadas": 0,
            "ausentes": 0,
            "total_raiz": 0,
            "error": str(exc),
        }

    with _LOCK:
        data = cargar_indice(path_indice, base_obras)
        momento = _ahora()
        presentes = set()
        agregadas = 0

        for nombre in nombres:
            codigo = extraer_codigo_ot_nombre(nombre)
            if not codigo:
                continue
            relativa = _rel_serializada(nombre)
            presentes.add(relativa.lower())
            if _registrar_ruta_en_data(data, codigo, relativa, "activa", momento):
                agregadas += 1

        ausentes = 0
        for entrada in data.get("entries", {}).values():
            rutas = entrada.get("rutas", {})
            for relativa, estado in rutas.items():
                # La reconciliación rápida sólo afirma ausencia en primer nivel.
                if "/" in relativa:
                    continue
                if relativa.lower() in presentes:
                    continue
                if estado.get("estado") in {"activa", "sin_verificar"}:
                    estado["estado"] = "ausente"
                    estado["ausente_desde"] = estado.get("ausente_desde") or momento
                    ausentes += 1

        data["updated_at"] = momento
        data["last_scan_started"] = inicio
        data["last_scan_completed"] = momento
        data["last_scan_status"] = "ok"
        data.pop("last_error", None)
        _guardar_json_atomico(path_indice, data)

        return {
            "ok": True,
            "agregadas": agregadas,
            "ausentes": ausentes,
            "total_raiz": len(nombres),
        }


def candidatos_indice(path_indice, base_obras, ot, incluir_ausentes=False):
    codigo = normalizar_codigo_ot(ot)
    if not codigo:
        return []

    with _LOCK:
        data = cargar_indice(path_indice, base_obras)
        entrada = data.get("entries", {}).get(codigo)
        if not entrada:
            return []

        prioridad = {"activa": 0, "sin_verificar": 1, "ausente": 2}
        candidatos = []
        for relativa, estado in entrada.get("rutas", {}).items():
            estado_nombre = estado.get("estado", "sin_verificar")
            if estado_nombre == "ausente" and not incluir_ausentes:
                continue
            nombre = os.path.basename(_ruta_desde_relativa(base_obras, relativa))
            if not coincide_codigo_ot(nombre, codigo):
                continue
            candidatos.append(
                {
                    "relativa": relativa,
                    "ruta": _ruta_desde_relativa(base_obras, relativa),
                    "estado": estado_nombre,
                    "ultima_vista": estado.get("ultima_vista"),
                    "ausente_desde": estado.get("ausente_desde"),
                }
            )

        candidatos.sort(key=lambda item: prioridad.get(item["estado"], 9))
        return candidatos


def registrar_ruta_encontrada(path_indice, base_obras, ot, ruta):
    relativa = _relativa_desde_absoluta(base_obras, ruta)
    if not relativa:
        return False

    nombre = os.path.basename(os.path.normpath(ruta))
    codigo = normalizar_codigo_ot(ot)
    if not coincide_codigo_ot(nombre, codigo):
        return False

    with _LOCK:
        data = cargar_indice(path_indice, base_obras)
        nueva = _registrar_ruta_en_data(data, codigo, relativa, "activa")
        data["updated_at"] = _ahora()
        _guardar_json_atomico(path_indice, data)
        return nueva


def marcar_ruta_ausente(path_indice, base_obras, ot, ruta):
    relativa = _relativa_desde_absoluta(base_obras, ruta)
    if not relativa:
        return False

    with _LOCK:
        data = cargar_indice(path_indice, base_obras)
        entrada = data.get("entries", {}).get(normalizar_codigo_ot(ot))
        if not entrada or relativa not in entrada.get("rutas", {}):
            return False

        estado = entrada["rutas"][relativa]
        momento = _ahora()
        estado["estado"] = "ausente"
        estado["ausente_desde"] = estado.get("ausente_desde") or momento
        data["updated_at"] = momento
        _guardar_json_atomico(path_indice, data)
        return True


def estadisticas_indice(path_indice, base_obras):
    with _LOCK:
        data = cargar_indice(path_indice, base_obras)
        activas = ausentes = sin_verificar = rutas = 0
        for entrada in data.get("entries", {}).values():
            for estado in entrada.get("rutas", {}).values():
                rutas += 1
                nombre = estado.get("estado", "sin_verificar")
                if nombre == "activa":
                    activas += 1
                elif nombre == "ausente":
                    ausentes += 1
                else:
                    sin_verificar += 1
        return {
            "ots": len(data.get("entries", {})),
            "rutas": rutas,
            "activas": activas,
            "ausentes": ausentes,
            "sin_verificar": sin_verificar,
            "last_scan_completed": data.get("last_scan_completed"),
            "last_scan_status": data.get("last_scan_status", "never"),
        }


def _snapshot_vacio():
    return {
        "version": SCHEMA_VERSION,
        "updated_at": None,
        "weeks": [],
        "facturas": {},
    }


def cargar_snapshot(path_snapshot):
    with _LOCK:
        data = _leer_json(path_snapshot, _snapshot_vacio())
        if data.get("version") != SCHEMA_VERSION:
            data = _snapshot_vacio()
        if not isinstance(data.get("weeks"), list):
            data["weeks"] = []
        if not isinstance(data.get("facturas"), dict):
            data["facturas"] = {}
        return data


def actualizar_snapshot_semanas(path_snapshot, semanas):
    with _LOCK:
        data = cargar_snapshot(path_snapshot)
        data["weeks"] = semanas if isinstance(semanas, list) else []
        data["updated_at"] = _ahora()
        _guardar_json_atomico(path_snapshot, data)
        return data["updated_at"]


def actualizar_snapshot_facturas(path_snapshot, semana, facturas):
    if not isinstance(semana, str) or not semana:
        return None
    with _LOCK:
        data = cargar_snapshot(path_snapshot)
        data["facturas"][semana] = facturas if isinstance(facturas, list) else []
        data["updated_at"] = _ahora()
        _guardar_json_atomico(path_snapshot, data)
        return data["updated_at"]


def snapshot_semanas(path_snapshot):
    return cargar_snapshot(path_snapshot).get("weeks", [])


def snapshot_facturas(path_snapshot, semana):
    return cargar_snapshot(path_snapshot).get("facturas", {}).get(semana)


def info_snapshot(path_snapshot):
    data = cargar_snapshot(path_snapshot)
    return {
        "updated_at": data.get("updated_at"),
        "weeks": len(data.get("weeks", [])),
        "semanas_con_detalle": len(data.get("facturas", {})),
    }
