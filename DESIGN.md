---
name: "Sincronizador Obras"
description: "Consola interna para coordinar semanas, carpetas de facturas, OT y sincronización."
colors:
  bg-body: "#f4f7fe"
  bg-surface: "#ffffff"
  secondary: "#eef2f9"
  primary: "#4318FF"
  primary-hover: "#3311db"
  primary-subtle: "#eeeaff"
  action-text: "#4318FF"
  on-primary: "#ffffff"
  focus-ring: "#4318FF"
  selection-surface: "#e8e3ff"
  success: "#007a4d"
  success-subtle: "#e7f5ed"
  warning: "#8a4b00"
  warning-subtle: "#fff4d6"
  danger: "#b42318"
  danger-subtle: "#fdecea"
  text-main: "#2b3674"
  text-muted: "#5d698f"
  border: "#e0e5f2"
  status-success-text: "#007A4D"
  status-success-bg: "#e7f5ed"
  status-warning-text: "#8a4b00"
  status-warning-bg: "#fff4d6"
  status-danger-text: "#B42318"
  status-danger-bg: "#fdecea"
  status-loading-text: "#3D16DB"
  status-loading-bg: "#eeeaff"
  status-ignored-text: "#4B5A7D"
  status-ignored-bg: "#e9edf5"
  status-sent-text: "#4318FF"
  status-sent-bg: "#eeeaff"
typography:
  body:
    fontFamily: "Poppins, sans-serif"
    fontSize: "1rem"
    lineHeight: "1.5"
  title:
    fontFamily: "Poppins, sans-serif"
    fontSize: "clamp(1.5rem, 2.1vw, 2rem)"
    lineHeight: "1.2"
  label:
    fontFamily: "Poppins, sans-serif"
    fontSize: "0.75rem"
    lineHeight: "1.35"
    letterSpacing: "0.08em"
rounded:
  compact: "8px"
  action: "12px"
  chip: "16px"
  panel: "20px"
  circular: "50%"
spacing:
  compact: "8px"
  control: "10px"
  action: "12px"
  section: "25px"
  page: "30px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.compact}"
    padding: "10px 14px"
  button-master:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.action}"
    padding: "12px 20px"
  tag:
    backgroundColor: "{colors.primary-subtle}"
    textColor: "{colors.action-text}"
    rounded: "{rounded.chip}"
    padding: "4px 10px"
  week-item-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    borderInlineStart: "1px solid {colors.on-primary}"
    state: "button[aria-pressed=true]"
    rounded: "{rounded.action}"
    padding: "14px 16px"
  status-control:
    rounded: "{rounded.circular}"
    size: "23px"
---

# Sistema de diseño: Sincronizador Obras

## Overview

**Norte creativo: "The Document Operations Desk"**

Esta línea base describe la interfaz existente; no prescribe un rediseño. **Hecho observado:** la pantalla agrupa una semana seleccionada, sus carpetas de factura, las OT asociadas, los archivos desplegables y las acciones de sincronización. **Intención inferida:** la metáfora elegida resume ese flujo operativo como un escritorio de documentos donde el trabajo se revisa y resuelve por fila.

La interfaz prioriza densidad operativa: barra lateral fija para semanas, cabecera de acciones, métricas resumidas y una tabla principal con acciones locales. Las superficies tinta encuadran navegación, cabecera y encabezados; el violeta reserva la selección y la acción. El modo oscuro conserva la misma estructura con pares semánticos propios.

**Características clave:**
- Hecho observado: navegación, cabecera y encabezados de tabla comparten una superficie tinta; métricas y filas mantienen una lectura más quieta.
- Hecho observado: violeta para selección, acciones y OT; verde, ámbar y rojo para progreso y excepción.
- Intención inferida: la fila de factura es la unidad de trabajo que conecta carpeta, OT, archivos y sincronización.

### Ink-and-violet ledger

La identidad usa tres superficies de escritorio semánticas que reutilizan la paleta por tema: `--desk-surface`, `--desk-text` y `--desk-muted`. La navegación semanal, la cabecera y toda la fila de encabezados de la tabla comparten la superficie tinta; eso crea una ruta visible hacia la cola de documentos sin inventar colores ni efectos.

La semana activa es una selección violeta sólida con texto `--on-primary` y un marcador de inicio de 1 px del mismo token. Las métricas bajan a una tira secundaria sin elevación y la tabla alterna filas secundarias para conservar un ritmo de libro mayor. Los estados siguen mostrando texto, iconos o nombres accesibles además de sus colores semánticos.

## Colors

Esta es una consola de operación: la paleta prioriza lectura y orientación, no expresión de marketing. La temperatura es fría y contenida; las superficies neutrales dominan y cada color conserva una función de acción, selección o estado.

El violeta `#4318FF` es una convención heredada e inferida de la interfaz, no un color de marca aprobado. Se reserva para la acción principal, la semana activa, el foco y los enlaces. Las etiquetas OT usan un fondo violeta suave con texto contrastante para que las muchas etiquetas de la tabla no compitan con la sincronización.

| Rol | Uso | Tratamiento |
|---|---|---|
| Canvas y superficie | Fondo general, paneles, tabla y campos | Capas frías azul-neutro; el modo oscuro define sus propios valores. |
| Escritorio tinta | Navegación, cabecera y encabezados de tabla | `--desk-surface`, `--desk-text` y `--desk-muted` reutilizan swatches existentes por tema y conservan contraste AA. |
| Acción y selección | CTA principal, semana activa, foco, enlaces y cambios pegados | Violeta sólido para acción/selección; tintes suaves para edición y OT. |
| Éxito | Sincronización registrada, documentos recibidos y progreso | Verde con pares explícitos de primer plano y superficie en ambos temas. |
| Atención | Pendiente y avisos devueltos por la API | Ámbar; el aviso de sincronización conserva texto e icono. |
| Error / destructivo | Errores y acción de eliminación | Rojo, acompañado por el mensaje existente. Las clases `badge-danger` que el backend asigna a cambios de OT/archivos conservan su mapeo actual; reclasificarlas excede este ajuste. |
| Excepción | Elementos ignorados | Slate neutral, con etiqueta explícita. |
| Bordes y foco | Separadores, campos y controles | Borde neutral; anillo de foco violeta con valores específicos para modo claro/oscuro. |

El modo oscuro recompone superficies, texto, foco y pares semánticos por separado; no invierte mecánicamente los valores claros. El texto informativo cumple al menos `4.5:1`; iconos y anillos interactivos, `3:1`. Los estados mantienen etiquetas visibles o accesibles además del color.

## Typography

**Familia autoritativa:** Poppins con los pesos ya cargados `400`, `500`, `600` y `700`, seguida por `sans-serif`. No se incorpora una segunda familia ni pesos que no estén disponibles.

La escala prioriza la lectura de una consola operativa: `1rem` para cuerpo, `0.9375rem` para datos y campos, `0.875rem` para navegación y acciones, `0.8125rem` para metadatos y estados, y `0.75rem` para etiquetas. Los títulos de página responden entre `1.5rem` y `2rem`; los títulos de sección usan `1.25rem`. El cuerpo mantiene interlineado `1.5`; los grupos densos usan `1.35` y los títulos `1.2`.

### Roles y contraste

| Rol | Uso | Tratamiento |
|---|---|---|
| Título de página | Semana seleccionada | 700, escala fluida, interlineado compacto y seguimiento ligeramente cerrado. |
| Título de sección | Gestor y planilla | 700, `1.25rem`, interlineado compacto. |
| Cuerpo y datos | Filas, archivos, campos y planilla | `0.9375rem` a `1rem`, peso 400 explícito; los nombres de carpeta usan 600 e interlineado denso para conservar escaneabilidad. |
| Etiquetas y metadatos | Encabezados de tabla, métricas y ayudas | 600, mayúsculas solo en etiquetas, seguimiento positivo e interlineado denso. |
| Navegación y acciones | Semanas y botones | 500–600, `0.875rem`; el peso y el color de acción distinguen la función sin inflar el tamaño. |
| Estado y métricas | Insignias y cifras resumidas | 600 para estado; 700 y cifras tabulares para métricas, de modo que los cambios numéricos no desplacen la lectura. |

El texto principal conserva el azul oscuro; el auxiliar de modo claro usa `#5D698F` para mantener contraste AA sobre el canvas y las superficies. En modo oscuro, texto, estados y superficies usan pares propios por tema. Las insignias de sincronización usan superficies explícitas, no transparencias dependientes del fondo.

### Densidad y accesibilidad

La vista no contiene prosa editorial extensa; cuando aparece texto explicativo, el ancho disponible y el interlineado del cuerpo evitan una medida incómoda. En tabla y controles se conserva la densidad, pero los campos siguen cerca de `1rem` y no bloquean el zoom del navegador. Los títulos, acciones y etiquetas admiten texto español largo y el reflujo de los puntos de corte existentes sin recorte intencional.

Las métricas dejan de ser encabezados: son datos asociados a una etiqueta. La marca lateral es texto de identidad, no un encabezado de sección; así, la jerarquía empieza por el título de página y continúa con las secciones sin saltos visuales o semánticos.

## Layout

El escritorio conserva una barra lateral y una cola tabular densa; el contenido principal se centra con un ancho máximo de `1840px` en monitores grandes. A `1080px` la cabecera pasa a una columna y la tabla reduce su espaciado. Entre `901px` y `1080px`, la tabla mantiene sus columnas dentro de un desplazamiento horizontal contenido para proteger los controles. Hasta `900px`, la barra lateral se vuelve superior y cada fila usa etiquetas `data-label` para mantener carpeta, OT, estado y acciones en un orden legible.

## Elevation & Depth

La profundidad se reserva para cabecera, tabla y modal. Las métricas son una tira secundaria sin elevación; la barra lateral lleva una sombra lateral tenue y el botón maestro no añade una sombra violeta decorativa. El modal añade capa oscura semitransparente, desenfoque de fondo y nivel de apilamiento alto.

**La regla de superficie de trabajo.** En la interfaz actual, la elevación distingue contenedores de trabajo y acciones maestras; las filas y los campos se separan principalmente con bordes y tonos de fondo.

## Shapes

Las formas son rectángulos suavemente redondeados: campos y botones compactos, acciones de cabecera y zonas de carga más amplias, y paneles principales muy redondeados. Las OT usan píldoras; los controles de estado y el interruptor de modo usan círculos. Los bordes son finos, salvo botones de contorno, zona de carga y foco de planilla.

## Components

### Buttons
- **Acción primaria:** el botón de fila combina fondo de acción y texto sobre acción; hereda la forma y el espaciado compactos del botón base.
- **Acción maestra:** el botón de sincronización semanal usa violeta sólido y texto blanco; el hover oscurece el mismo token. El degradado se eliminó para sostener contraste consistente.
- **Contorno y fantasma:** las acciones de cabecera usan borde violeta; guardar e ignorar usan fondo secundario. Sus hover cambian fondo y/o contraste.
- **Alta de semana:** es un caso específico observado: fondo claro, borde discontinuo y transición a fondo violeta al pasar el cursor.

### Navigation
- **Lista de semanas:** cada elemento tiene un indicador semántico y una etiqueta accesible de estado; la semana activa usa `--primary` sólido con texto `--on-primary` y un marcador de inicio de 1 px, y expone su estado mediante un botón con `aria-pressed`.
- **Menú lateral:** el control visual de tres barras es un `button.menu-icon` semántico con nombre accesible; activa y desactiva la navegación lateral.

### Scrollbars y movimiento
- **Scrollbars:** `.week-list`, `.main-content`, `.modal-body` y el `body` móvil usan el scrollbar nativo fino con pulgar `--border`, pista transparente y realce `--text-muted` al pasar el cursor. El control sigue visible sin hover y vuelve al modo del sistema bajo `forced-colors`.
- **Movimiento:** los cambios de tema transicionan solo color, fondo y borde durante `180 ms`; las sombras no se animan. La selección semanal usa el marcador compartido `selected-week`; el detalle transfiere el nombre único `folder-detail` entre el botón de carpeta y su fila. `document.startViewTransition` envuelve solo cambios DOM síncronos: las solicitudes de datos quedan fuera y la raíz no cruza toda la tabla. La barra lateral conserva su transición independiente. La planilla entra con un breve desplazamiento y el velo aparece con una transición de opacidad; las etiquetas y el detalle expandido usan el mismo desplazamiento corto cuando no hay View Transitions, sin rebote. Copiar y cargar archivos cambian a estados de éxito verdaderos, y pegar mantiene su realce violeta temporal. Sin soporte de View Transitions o con `prefers-reduced-motion`, el estado se actualiza directamente sin animación compartida.

### Tags / OT
- **Campo de OT:** contenedor flexible que aloja etiquetas y una entrada sin borde. El foco dentro del contenedor cambia borde y fondo.
- **Etiqueta:** píldora de fondo violeta suave y texto contrastante; su entrada es breve y el control de cierre cambia de color al pasar el cursor.

### Status Controls
- **Estados de documentos:** botones circulares con iconos SVG para factura, solicitud y comprobante. Cada control tiene `aria-label`, `aria-pressed`, `title` y estado deshabilitado; pendiente, recibido y enviado usan pares semánticos de texto/borde y fondo explícitos en ambos temas.
- **Insignia de sincronización:** muestra texto de estado con variantes de éxito, aviso, peligro, carga e ignorado. Las respuestas `warning` de la API usan ámbar; los `badge-danger` ya emitidos por el backend mantienen su clasificación actual.

### Cards / Containers
- **Paneles de trabajo:** cabecera y encabezado de tabla usan la superficie tinta; las métricas forman una tira secundaria sin elevación y la tabla conserva una superficie de datos legible con ritmo alternado.
- **Archivos:** la fila expandida contiene zona de arrastre con borde discontinuo; los archivos se muestran como ítems sobre el fondo de trabajo.

### Inputs / Fields
- **Búsqueda de semanas:** campo con borde fino que cambia borde y fondo al foco.
- **Planilla:** celda sin borde visible que usa la superficie de selección y el token de foco en el anillo interior.

### Accessibility notes
- **Hecho observado:** los controles de estado incluyen nombre accesible y no dependen solo del color; los botones de acción de fila usan títulos, pero no `aria-label` explícito.
- Los controles con foco de teclado usan el anillo de color por tema. Algunos elementos interactivos siguen siendo `div` con `onclick` y requieren un trabajo de semántica/teclado independiente.
- Los breakpoints de trabajo son `1080px` para compactar la cabecera/tabla y `900px` para apilar navegación y convertir filas en tarjetas etiquetadas. En dispositivos con puntero grueso, los botones de estado y las acciones de icono conservan objetivos de al menos `44px`; el foco de teclado y las acciones siguen visibles.

## Do's and Don'ts

### Do:
- **Haz** conservar la lectura semanal: semana → carpeta de factura → OT → archivos → sincronización.
- **Haz** usar las variantes semánticas existentes para selección y estado, acompañándolas con texto, icono o nombre accesible cuando el código ya lo hace.
- **Haz** mantener la densidad de tabla y la expansión de archivos como patrón de inspección por fila.

### Don't:
- **No** interpretes “The Document Operations Desk” como autorización para cambiar interfaz, flujo, paleta o jerarquía.
- **No** conviertas colores de estado en una única fuente de significado: los hallazgos actuales de foco y semántica siguen siendo limitaciones a corregir en trabajo posterior autorizado.
- **No** asumas una experiencia móvil o de teclado completa: no está probada ni completamente codificada en la implementación observada.
