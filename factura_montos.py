"""Montos y datos resumidos de facturas F N°... para SincronizadorFacturas.

V1.1.1:
- Extrae Neto / IVA / Total desde PDF con texto.
- Extrae emisor y comuna cuando el formato lo permite.
- Muestra un nombre corto para personas: primer nombre + primer apellido.
- Conserva razón social completa para empresas.
- Los cambios manuales de emisor/comuna persisten en .factura_montos.json.
- No toca el flujo de sincronización de OT.
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

# Si aparece alguno de estos marcadores, no intentamos reducir la razón social
# a "primer nombre + apellido".
MARCADORES_EMPRESA = (
    ' SPA', ' S.P.A', ' LTDA', ' LIMITADA', ' EIRL', ' E.I.R.L', ' S.A.', ' S.A ',
    ' SOCIEDAD ', ' EMPRESA ', ' COMERCIAL ', ' CONSTRUCTORA ', ' TRANSPORTES ',
    ' SERVICIOS ', ' INGENIERIA ', ' INGENIERÍA ', ' DISTRIBUIDORA ',
    ' COMERCIALIZADORA ', ' IMPORTADORA ', ' EXPORTADORA ', ' ASOCIACION ',
    ' ASOCIACIÓN ', ' FUNDACION ', ' FUNDACIÓN ', ' COOPERATIVA ', ' CORPORACION ',
    ' CORPORACIÓN ', ' MUNICIPALIDAD ', ' UNIVERSIDAD ', ' CLINICA ', ' CLÍNICA ',
    ' RESTAURANT ', ' RESTAURANTE ', ' INVERSIONES ', ' AGRICOLA ', ' AGRÍCOLA ',
)
PARTICULAS_APELLIDO = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'VAN', 'VON', 'DA', 'DAS', 'DO', 'DOS'}


def es_factura(nombre):
    if not isinstance(nombre, str):
        return False
    return bool(FACTURA.match(nombre)) and os.path.splitext(nombre)[1].lower() in VALIDOS


def numero_factura(nombre):
    m = FACTURA.match(nombre)
    return m.group(1) if m else None  # conserva ceros a la izquierda


# Extractor estructural DTE SII V1.1.1
class TextoPDF(str):
    """Texto extraído del PDF con metadatos de layout de la primera página."""
    def __new__(cls, contenido, *, lineas_layout=None, ancho=None, alto=None):
        obj = super().__new__(cls, contenido)
        obj.lineas_layout = lineas_layout or []
        obj.ancho_pagina = ancho
        obj.alto_pagina = alto
        return obj


def _lineas_layout_pagina(pagina):
    """Líneas con coordenadas/estilo para separar columnas visuales del DTE."""
    datos = pagina.get_text("dict", sort=True)
    resultado = []

    for bloque in datos.get("blocks", []):
        if bloque.get("type") != 0:
            continue

        for linea in bloque.get("lines", []):
            spans = linea.get("spans", [])
            texto = "".join(span.get("text", "") for span in spans)
            texto = re.sub(r"\s+", " ", texto).strip()
            if not texto:
                continue

            bbox = linea.get("bbox") or bloque.get("bbox")
            if not bbox:
                continue

            colores = [
                span.get("color")
                for span in spans
                if isinstance(span.get("color"), int)
            ]
            fuentes = [str(span.get("font", "")) for span in spans]

            resultado.append({
                "texto": texto,
                "x0": float(bbox[0]),
                "y0": float(bbox[1]),
                "x1": float(bbox[2]),
                "y1": float(bbox[3]),
                "color": colores[0] if colores else None,
                "negrita": any("bold" in fuente.lower() for fuente in fuentes),
            })

    resultado.sort(key=lambda item: (round(item["y0"], 1), item["x0"]))
    return resultado


def leer_pdf(ruta):
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError(
            'Instala PyMuPDF: python -m pip install pymupdf'
        ) from exc

    doc = pymupdf.open(ruta)
    try:
        if doc.needs_pass:
            raise ValueError('PDF protegido con contraseña')
        if len(doc) > 15:
            raise ValueError('PDF demasiado largo para una factura')

        textos = [pagina.get_text(sort=True) for pagina in doc]
        pagina0 = doc[0]

        return TextoPDF(
            '\n'.join(textos),
            lineas_layout=_lineas_layout_pagina(pagina0),
            ancho=float(pagina0.rect.width),
            alto=float(pagina0.rect.height),
        )
    finally:
        doc.close()


def _lineas(texto):
    return [re.sub(r'\s+', ' ', l).strip() for l in (texto or '').splitlines() if l.strip()]


def _es_ruido_emisor(linea):
    u = linea.upper()
    ruido = (
        'FACTURA ELECTRONICA', 'FACTURA ELECTRÓNICA', 'BOLETA ELECTRONICA',
        'R.U.T', 'RUT:', 'S.I.I', 'SII -', 'TELÉFONO', 'TELEFONO', 'EMAIL',
        'E-MAIL', 'WWW.', 'HTTP', 'GIRO:', 'GIRO ', 'N°', 'Nº', 'NO.',
    )
    return any(x in u for x in ruido)


def _candidato_nombre(linea):
    if not linea or _es_ruido_emisor(linea):
        return False
    if len(linea) > 120:
        return False
    letras = re.findall(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+', linea)
    if len(letras) < 2:
        return False
    # Evita escoger direcciones obvias como nombre del emisor.
    u = f' {linea.upper()} '
    if any(x in u for x in (' DIRECCION ', ' DIRECCIÓN ', ' CALLE ', ' AV. ', ' AVENIDA ', ' PJE. ', ' PASAJE ', ' CAMINO ', ' RUTA ')):
        return False
    return True


def abreviar_emisor(emisor):
    """Para personas: primer nombre + primer apellido. Empresas: razón social completa."""
    if not isinstance(emisor, str):
        return None
    limpio = re.sub(r'\s+', ' ', emisor).strip(' ,;:-')
    if not limpio:
        return None
    u = f' {limpio.upper()} '
    if any(m in u for m in MARCADORES_EMPRESA):
        return limpio
    tokens = limpio.split()
    if len(tokens) <= 2:
        return limpio

    def sacar_apellido(restantes):
        if not restantes:
            return []
        grupo = [restantes.pop()]
        while restantes and restantes[-1].upper().strip('.,') in PARTICULAS_APELLIDO:
            grupo.insert(0, restantes.pop())
        return grupo

    restantes = tokens[:]
    _segundo = sacar_apellido(restantes)
    primero = sacar_apellido(restantes)
    if not primero or not restantes:
        return limpio
    return f"{restantes[0]} {' '.join(primero)}"


def _normalizar_texto_layout(valor):
    return re.sub(
        r'\s+',
        ' ',
        str(valor or '').replace('\ufffe', '-')
    ).strip()


def _es_linea_roja(linea):
    """Señal adicional del DTE SII clásico; no es requisito para extraer."""
    color = linea.get('color')
    if not isinstance(color, int):
        return False

    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    return r >= 180 and g <= 100 and b <= 100


def _comuna_desde_zona_emisor(textos):
    """
    Extrae la comuna sólo desde la zona del EMISOR.

    La dirección del DTE SII normalmente termina en "- COMUNA". La dirección
    puede contener otros guiones y puede ocupar más de una línea, por lo que
    se usa el ÚLTIMO guion del bloque completo, no una lista de casos concretos.
    """
    if not textos:
        return None

    normalizados = [
        _normalizar_texto_layout(texto)
        for texto in textos
        if _normalizar_texto_layout(texto)
    ]
    zona = re.sub(r'\s+', ' ', ' '.join(normalizados)).strip()
    if not zona:
        return None

    # Formatos que traigan una etiqueta explícita.
    for patron in (
        r'\bCOMUNA\s*:?\s*([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ .\'-]{1,45})$',
        r'\bCIUDAD\s*:?\s*([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ .\'-]{1,45})$',
    ):
        m = re.search(patron, zona, re.I)
        if m:
            return re.sub(r'\s+', ' ', m.group(1)).strip(' .,-')

    # Regla estructural del bloque de dirección:
    # "HJ N 1 EX-COM. JOSE HUENCHUNAO- TIRUA"        -> TIRUA
    # "LORD COCHRANNE 640- GORBEA"                   -> GORBEA
    # "6 PONIENTE 111 LS CEREZOS-LABRANZA- TEMUCO"  -> TEMUCO
    separadores = list(re.finditer(r'[-–]', zona))
    if separadores:
        ultimo = separadores[-1]
        candidata = zona[ultimo.end():].strip(' .,-')
        if re.fullmatch(
            r'[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ .\']{1,45}',
            candidata,
            re.I,
        ):
            return re.sub(r'\s+', ' ', candidata).strip()

    # Respaldo: comuna sola en la última línea del bloque.
    if len(normalizados) >= 2:
        candidata = normalizados[-1].strip(' .,-')
        if re.fullmatch(
            r'[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ .\']{1,35}',
            candidata,
            re.I,
        ):
            return candidata

    return None


def _extraer_identidad_layout(texto):
    """
    Extrae Emisor/Comuna usando la geometría de la primera página.

    No interpreta toda la página como texto lineal: primero localiza la columna
    del emisor con las anclas "Giro:" y "SEÑOR(ES)", por lo que no mezcla
    "S.I.I. - TEMUCO" ni la COMUNA del receptor con los datos del emisor.
    """
    lineas = getattr(texto, 'lineas_layout', None)
    ancho = getattr(texto, 'ancho_pagina', None)

    if not lineas or not ancho:
        return None

    # Ancla que marca el comienzo del receptor.
    receptor_y = None
    for linea in lineas:
        if re.search(
            r'\bSE[NÑ]OR(?:\(ES\)|ES)?\s*:',
            linea['texto'],
            re.I,
        ):
            receptor_y = linea['y0']
            break

    if receptor_y is None:
        receptor_y = float('inf')

    # Giro del emisor: sólo zona izquierda y antes del receptor.
    giros = [
        linea
        for linea in lineas
        if linea['y0'] < receptor_y
        and linea['x0'] < ancho * 0.68
        and re.search(r'\bGIRO\s*:', linea['texto'], re.I)
    ]

    if not giros:
        return None

    giro = min(giros, key=lambda item: item['y0'])

    # Nombre del emisor: misma columna, inmediatamente arriba de Giro.
    anteriores = [
        linea
        for linea in lineas
        if linea['y1'] <= giro['y0'] + 1.5
        and giro['y0'] - linea['y0'] <= 70
        and abs(linea['x0'] - giro['x0']) <= max(35.0, ancho * 0.06)
        and linea['x1'] < ancho * 0.70
        and _candidato_nombre(linea['texto'])
    ]

    emisor = None
    if anteriores:
        estilizadas = [
            linea
            for linea in anteriores
            if _es_linea_roja(linea) or linea.get('negrita')
        ]
        candidatos = estilizadas or anteriores

        # Elegimos la primera línea del encabezado del emisor. Esto evita tomar
        # nombres de fantasía secundarios como "HOSPEDAJE E.I.R.L." en lugar
        # del nombre legal de la persona.
        emisor = min(candidatos, key=lambda item: item['y0'])['texto']

    # eMail marca el final natural del bloque Giro/Dirección del emisor.
    emails = [
        linea
        for linea in lineas
        if linea['y0'] > giro['y0']
        and linea['y0'] < receptor_y + 12
        and linea['x0'] < ancho * 0.68
        and re.search(r'\be[\s-]*mail\b|\bcorreo\b', linea['texto'], re.I)
    ]
    email_y = min((linea['y0'] for linea in emails), default=receptor_y)

    # Sólo bloques de la misma columna visual entre Giro y eMail.
    zona_emisor = [
        linea
        for linea in lineas
        if linea['y0'] > giro['y0'] + 1
        and linea['y0'] < email_y - 0.5
        and abs(linea['x0'] - giro['x0']) <= max(45.0, ancho * 0.08)
        and linea['x1'] < ancho * 0.70
    ]
    zona_emisor.sort(key=lambda item: (item['y0'], item['x0']))

    comuna = _comuna_desde_zona_emisor(
        [linea['texto'] for linea in zona_emisor]
    )

    # Folio interno para diagnóstico / validación futura.
    folio_pdf = None
    for linea in lineas:
        if linea['y0'] >= receptor_y:
            continue

        m = re.search(
            r'\bN\s*[°º]\s*([0-9]+)\b',
            linea['texto'],
            re.I,
        )
        if m:
            folio_pdf = m.group(1)
            break

    if not emisor and not comuna:
        return None

    return {
        'emisor_original': emisor,
        'emisor_corto': abreviar_emisor(emisor) if emisor else None,
        'comuna': comuna,
        'metodo_identidad': 'layout_sii',
        'folio_pdf': folio_pdf,
    }


def extraer_identidad(texto):
    """
    Extrae identidad del emisor.

    Prioridad:
      1) Layout/posición del DTE SII.
      2) Texto lineal como fallback para PDFs que no conserven geometría.
    """
    por_layout = _extraer_identidad_layout(texto)
    if por_layout and (
        por_layout.get('emisor_original')
        or por_layout.get('comuna')
    ):
        return por_layout

    # Fallback conservador para PDFs sin información de layout.
    lineas = _lineas(texto)
    if not lineas:
        return {
            'emisor_original': None,
            'emisor_corto': None,
            'comuna': None,
            'metodo_identidad': 'sin_datos',
            'folio_pdf': None,
        }

    corte = len(lineas)
    receptor = re.compile(
        r'\bSE[NÑ]OR(?:\(ES\)|ES)?\s*:'
        r'|\bRECEPTOR\b'
        r'|\bRAZ[ÓO]N\s+SOCIAL\s+RECEPTOR\b',
        re.I,
    )

    for i, linea in enumerate(lineas):
        if receptor.search(linea):
            corte = i
            break

    cabecera = lineas[:corte]

    emisor = None
    for i, linea in enumerate(cabecera):
        if re.search(r'\bGIRO\s*:', linea, re.I):
            candidatos = [
                candidato
                for candidato in cabecera[:i]
                if _candidato_nombre(candidato)
            ]
            if candidatos:
                emisor = candidatos[0]
            break

    if not emisor:
        for linea in cabecera[:15]:
            if _candidato_nombre(linea):
                emisor = linea
                break

    # Nunca usar S.I.I. como fuente de comuna.
    sin_sii = [
        linea
        for linea in cabecera
        if not re.search(r'\bS\.?\s*I\.?\s*I\.?\b', linea, re.I)
    ]
    comuna = _comuna_desde_zona_emisor(sin_sii)

    folio_pdf = None
    for linea in cabecera:
        m = re.search(
            r'\bN\s*[°º]\s*([0-9]+)\b',
            linea,
            re.I,
        )
        if m:
            folio_pdf = m.group(1)
            break

    return {
        'emisor_original': emisor,
        'emisor_corto': abreviar_emisor(emisor) if emisor else None,
        'comuna': comuna,
        'metodo_identidad': 'texto_fallback',
        'folio_pdf': folio_pdf,
    }


def numero_clp(texto):
    texto = texto.strip().replace(' ', '')
    if '.' in texto and ',' in texto:
        return None
    if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', texto):
        return int(re.sub(r'[.,]', '', texto))
    if re.fullmatch(r'\d{1,10}', texto):
        return int(texto)
    return None


def importes_despues_etiqueta(linea, tipo):
    for etiqueta in ETIQUETAS[tipo]:
        for match in re.finditer(r'(?<![A-Z])' + etiqueta + r'(?![A-Z])', linea, flags=re.I):
            resto = linea[match.end():]
            resto = re.split(r'(?<![A-Z])(?:MONTO\s+NETO|VALOR\s+NETO|NETO|I\s*\.?V\s*\.?A|TOTAL)(?![A-Z])', resto, maxsplit=1, flags=re.I)[0]
            hallados = [(numero_clp(m.group(1)), m.start()) for m in IMPORTE.finditer(resto[:55])]
            hallados = [(n, p) for n, p in hallados if n is not None]
            if hallados:
                valores = {n for n, _ in hallados}
                if len(valores) == 1:
                    yield hallados[0][0]


def extraer_importes(texto):
    if not texto or not texto.strip():
        return None, 'PDF sin texto seleccionable (escaneado); ingresa los datos manualmente.'
    lineas = _lineas(texto)
    encontrados = {tipo: set() for tipo in ETIQUETAS}
    for tipo in ETIQUETAS:
        for i, linea in enumerate(lineas):
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
    if abs(montos['neto'] + montos['iva'] - montos['total']) > 2:
        return None, 'Neto + IVA no coincide con total; revisar posibles impuestos adicionales.'
    return montos, None


def _archivo_metadata(carpeta):
    return os.path.join(carpeta, METADATA)


def _leer_metadata(carpeta):
    try:
        with open(_archivo_metadata(carpeta), encoding='utf-8') as entrada:
            contenido = json.load(entrada)
        if isinstance(contenido.get('documentos'), dict):
            contenido['version'] = 2
            return contenido
    except (FileNotFoundError, ValueError, OSError, TypeError, AttributeError):
        pass
    return {'version': 2, 'documentos': {}}


def _guardar_metadata(carpeta, contenido):
    contenido['version'] = 2
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
    base = {
        'archivo': nombre,
        'numero': numero_factura(nombre),
        'huella': _huella(ruta),
        'actualizado': datetime.now(timezone.utc).isoformat(),
        'manual_campos': {},
    }
    if os.path.splitext(nombre)[1].lower() not in PDF:
        return {**base, 'estado': 'manual_pendiente', 'motivo': 'Imagen: ingresa los datos manualmente.', 'montos': None,
                'datos_extraidos': {'emisor_original': None, 'emisor_corto': None, 'comuna': None}}
    try:
        texto = leer_pdf(ruta)
        identidad = extraer_identidad(texto)
        montos, motivo = extraer_importes(texto)
        return {**base, 'estado': 'extraido' if montos else 'manual_pendiente', 'motivo': motivo, 'montos': montos,
                'datos_extraidos': identidad}
    except Exception as exc:
        LOG.warning('No se pudo leer la factura PDF %s: %s', nombre, exc)
        return {**base, 'estado': 'manual_pendiente', 'motivo': str(exc), 'montos': None,
                'datos_extraidos': {'emisor_original': None, 'emisor_corto': None, 'comuna': None}}


def _fusionar_manual(anterior, nuevo):
    if not isinstance(anterior, dict):
        return nuevo
    manual_campos = anterior.get('manual_campos') if isinstance(anterior.get('manual_campos'), dict) else {}
    nuevo['manual_campos'] = dict(manual_campos)
    # Compatibilidad V1.1: si los importes fueron digitados manualmente, se conservan
    # incluso al reanalizar el PDF.
    if anterior.get('estado') == 'manual' and isinstance(anterior.get('montos'), dict):
        nuevo['montos'] = dict(anterior['montos'])
        nuevo['estado'] = 'manual'
        if abs(nuevo['montos']['neto'] + nuevo['montos']['iva'] - nuevo['montos']['total']) > 2:
            nuevo['motivo'] = 'Revisado manualmente: el total difiere de neto + IVA (pueden existir impuestos adicionales).'
        else:
            nuevo['motivo'] = None
    return nuevo


def _listado(carpeta):
    return sorted([n for n in os.listdir(carpeta) if es_factura(n) and os.path.isfile(os.path.join(carpeta, n))], key=str.casefold)


def actualizar_carpeta(carpeta, forzar=False):
    """Reanaliza lo necesario y conserva overrides manuales."""
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
            tiene_identidad_v2 = isinstance((anterior or {}).get('datos_extraidos'), dict)
            if anterior and anterior.get('huella') == huella and not forzar and tiene_identidad_v2:
                continue
            nuevo = _fusionar_manual(anterior, _extraer_uno(ruta))
            documentos[nombre] = nuevo
            cambios = True
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
                salida.append(_presentar(registro))
        return salida


def _presentar(registro):
    auto = registro.get('datos_extraidos') if isinstance(registro.get('datos_extraidos'), dict) else {}
    manual = registro.get('manual_campos') if isinstance(registro.get('manual_campos'), dict) else {}
    salida = dict(registro)
    salida['emisor_original'] = auto.get('emisor_original')
    salida['emisor_auto'] = auto.get('emisor_corto')
    salida['comuna_auto'] = auto.get('comuna')
    salida['emisor'] = manual.get('emisor_corto') or auto.get('emisor_corto')
    salida['comuna'] = manual.get('comuna') or auto.get('comuna')
    salida['emisor_manual'] = bool(manual.get('emisor_corto'))
    salida['comuna_manual'] = bool(manual.get('comuna'))
    return salida


def actualizar_archivo_cargado(carpeta, ruta):
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


def _texto_manual(valor, maximo=100):
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError('Campo manual inválido')
    valor = re.sub(r'\s+', ' ', valor).strip()
    if len(valor) > maximo:
        raise ValueError('Campo manual demasiado largo')
    return valor or None


def _leer_ot_metadata(carpeta):
    """Lee .OT.txt y mantiene compatibilidad de solo lectura con OT.txt antiguo."""
    for nombre in ('.OT.txt', 'OT.txt'):
        ruta = os.path.join(carpeta, nombre)
        try:
            with open(ruta, encoding='utf-8') as entrada:
                return entrada.read().strip()
        except OSError:
            continue
    return ''


def registrar_rutas_montos(app, base_facturas, validar_factura, ruta_aprobada):
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
                # V1.1.1: el resumen monetario incluye también carpetas ignoradas
                # en el flujo de OT. Ignorado sólo afecta sincronización/seguimiento,
                # nunca el total que se enviará a cobro.
                resultado = resumen(carpeta)
                ot = _leer_ot_metadata(carpeta)
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
                # Las carpetas ignoradas también deben actualizar sus montos.
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
        tiene_emisor = 'emisor' in data
        tiene_comuna = 'comuna' in data
        try:
            emisor_corto = _texto_manual(data.get('emisor'), 120) if tiene_emisor else None
            comuna = _texto_manual(data.get('comuna'), 80) if tiene_comuna else None
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

        montos = data.get('montos')
        if montos is not None:
            if not isinstance(montos, dict) or any(type(montos.get(k)) is not int or montos[k] < 0 or montos[k] > 10**12 for k in ('neto', 'iva', 'total')):
                return jsonify(error='Los importes deben ser enteros positivos en CLP'), 400

        with _LOCK:
            datos = _leer_metadata(carpeta)
            registro = datos['documentos'].get(archivo)
            if not isinstance(registro, dict) or registro.get('huella') != _huella(destino):
                registro = _extraer_uno(destino)
            auto = registro.get('datos_extraidos') if isinstance(registro.get('datos_extraidos'), dict) else {}
            manual = registro.get('manual_campos') if isinstance(registro.get('manual_campos'), dict) else {}

            # Si el cliente envía el campo, lo actualizamos. Clientes V1.1 que sólo
            # envían montos no borran correcciones de emisor/comuna.
            if tiene_emisor:
                if emisor_corto and emisor_corto != auto.get('emisor_corto'):
                    manual['emisor_corto'] = emisor_corto
                else:
                    manual.pop('emisor_corto', None)
            if tiene_comuna:
                if comuna and comuna != auto.get('comuna'):
                    manual['comuna'] = comuna
                else:
                    manual.pop('comuna', None)
            registro['manual_campos'] = manual

            if montos is not None:
                registro['montos'] = {k: montos[k] for k in ('neto', 'iva', 'total')}
                registro['estado'] = 'manual'
                registro['motivo'] = ('Revisado manualmente: el total difiere de neto + IVA (pueden existir impuestos adicionales).'
                                      if abs(montos['neto'] + montos['iva'] - montos['total']) > 2 else None)
            registro['actualizado'] = datetime.now(timezone.utc).isoformat()
            datos['documentos'][archivo] = registro
            try:
                _guardar_metadata(carpeta, datos)
            except OSError:
                LOG.exception('No se pudieron guardar datos manuales')
                return jsonify(error='No se pudieron guardar los datos.'), 500
        return jsonify(status='ok')


def resumen_forzado(carpeta):
    actualizar_carpeta(carpeta, forzar=True)
    return resumen(carpeta)
