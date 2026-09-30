---
target: templates/index.html
total_score: 20
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 5
target_identity: "file:C:\\Users\\Supervisor\\Desktop\\SincronizadorWeb\\templates\\index.html"
target_fingerprint: "sha256:1f0f5fe683b90c575b7d1c68e01fdc31a21c4374d8407572f1e9b68455ac45d4"
target_path: "C:\\Users\\Supervisor\\Desktop\\SincronizadorWeb\\templates\\index.html"
timestamp: 2026-09-27T15-58-44Z
slug: templates-index-html
---
# Crítica de interfaz — templates/index.html

## Veredicto

**La lógica del producto es específica; su lenguaje visual todavía podría pertenecer a cualquier dashboard administrativo.** La secuencia real —semana → carpeta de factura → OT → archivos → sincronización— está bien representada. El diseño actual, en cambio, se apoya en Poppins, tarjetas blancas redondeadas, acento violeta, gradientes y métricas genéricas.

### North Star

**The Document Operations Desk** —un escritorio de operaciones documentales, organizado alrededor de revisar y resolver cada carpeta dentro de su semana—. Es una síntesis de la UI existente, no autorización para rediseñar ni cambiar comportamiento.

## Puntuación — heurísticas de Nielsen

| Heurística | Puntaje | Evidencia |
|---|---:|---|
| Visibilidad del estado del sistema | 3/4 | Hay carga, insignias por fila, progreso y estado de semana (:162-168, :826-833, :872-887); falta un resumen duradero de resultados de la sincronización y los errores quedan separados en alertas. |
| Correspondencia con el mundo real | 3/4 | Semana, factura, OT, carpeta y excepciones encajan con el trabajo (:130-157, :174-177); “OT”, “Sinc.” y “Actualizar Semana” requieren contexto. |
| Control y libertad | 2/4 | Modal cancelable y confirmación al eliminar (:185-201, :341-354); no hay deshacer para eliminación, edición ni sincronización. |
| Consistencia y estándares | 2/4 | Hay patrones repetidos de botones, tarjetas e insignias; conviven emojis, controles solo con icono, tooltips, prompts y alerts (:46-49, :77-91, :484-502). |
| Prevención de errores | 2/4 | Eliminar pide confirmación y se valida que exista una OT (:343, :836-840); la acción semanal no muestra el alcance previsto ni un resumen por carpeta antes de actuar. |
| Reconocimiento antes que recuerdo | 2/4 | Semana, tags OT y acciones visibles ayudan; los tres estados documentales se distinguen principalmente por icono/color y requieren recordar su significado (:214-230, :505-510). |
| Flexibilidad y eficiencia | 2/4 | Modo planilla, pegado desde Excel, exportación y sincronización por fila/semana son útiles (:532-614, :616-732); faltan selección múltiple y atajos para correcciones repetidas. |
| Diseño estético y minimalista | 2/4 | La estructura base es legible, pero cabecera, métricas, acciones de fila y badges compiten por atención (:37-61, :151-168, :498-510). |
| Ayuda para reconocer, diagnosticar y recuperarse de errores | 1/4 | Predominan alerts genéricos; no queda claro qué carpeta falló, qué se guardó ni cómo reintentar (:267, :322-395, :819-833). |
| Ayuda y documentación | 1/4 | Hay algunos títulos y una instrucción de carga (:154-157, :517-520), pero faltan leyenda de estados, guía de formato OT y ayuda contextual de tareas. |

**Lectura del puntaje:** la tabla principal suma **20/40** al recalcular sus diez filas. Un segundo pase ciego varió algunos ítems y dio **21/40**; los valores de estado del sistema, eficiencia y minimalismo variaron un punto. Es una señal direccional, no una medición objetiva.

## Hallazgos priorizados

### P1 — La sincronización semanal no hace visible su alcance ni deja un cierre tranquilizador

sincronizarTodaLaSemana() procesa varias carpetas elegibles en lote (:856-887). El control “Actualizar Semana” no adelanta de forma visible qué carpetas y destinos se tocarán ni ofrece un resumen persistente de éxitos y fallas.

**Impacto:** el momento de mayor consecuencia es también el de mayor incertidumbre; un OT incorrecto o un resultado parcial cuesta detectar.  
**Dirección:** hacer explícito que se sincroniza la semana, mostrar alcance y terminar con resultados por carpeta y reintento claro.

### P1 — La fila concentra tareas distintas y demasiados controles

Una misma fila combina OT, guardar, sincronizar, ignorar, renombrar/eliminar, tres estados documentales y el estado de sincronización (:484-510).

**Impacto:** cuesta responder “¿qué requiere atención?” y sube el riesgo de actuar en la carpeta equivocada.  
**Dirección:** priorizar la tarea principal por fila y agrupar acciones secundarias sin eliminar las capacidades actuales.

### P1 — Los estados documentales son compactos, pero visualmente ambiguos sin una clave persistente

Factura, solicitud de pago y comprobante usan círculos con icono y color (:214-230, :505-510). Los botones sí declaran aria-label y aria-pressed, lo cual es una buena base; la explicación visual depende más del icono, color o hover que de una leyenda siempre visible.

**Impacto:** el usuario nuevo debe adivinar; color e icono pequeños no bastan para escanear con confianza.  
**Dirección:** conservar el tamaño compacto, pero acompañarlo con leyenda permanente y estados accesibles que expliquen concepto y valor sin depender del color.

### P1 — Los errores interrumpen el flujo y no indican una recuperación concreta

Se usan alert() para varios fallos; mensajes como “Error de red” no siempre identifican carpeta, resultado guardado o siguiente paso (:267, :322-395, :819-833). El guardado no presenta una ruta visible de recuperación ante excepción.

**Impacto:** se pierde contexto y el usuario puede repetir o abandonar una acción sin saber si el archivo quedó actualizado.  
**Dirección:** asociar el error a la fila y la operación, preservar la entrada y ofrecer reintento cuando sea seguro.

### P1 — Semántica de teclado y foco incompleta

El menú lateral y algunas interacciones de carpeta/tag usan elementos clicables no semánticos; faltan estilos globales explícitos de foco visible. También faltan anuncios persistentes para algunos cambios asíncronos (:142-143, :417, :480-482).

**Impacto:** teclado y lector de pantalla pueden perder el foco o no percibir el resultado.  
**Dirección:** controles semánticos, foco claramente visible y anuncios accesibles para progreso/resultado. Los estados documentales ya ofrecen nombres accesibles.

### P2 — El producto no explica suficiente vocabulario ni sus estados vacíos

“OT”, “Modo Planilla”, “Excepción” y “Sinc.” presuponen conocimiento. No se ve una leyenda para estados ni un ejemplo del formato OT. Las vistas de semanas/carpetas tampoco muestran estados vacíos tan claros como el estado de carga inicial (:134-136, :290-292, :466-467).

## Carga cognitiva

**Alta: 5–6 de 8 señales**, según la diferencia entre las dos evaluaciones sobre “chunking”.

- **Falla:** foco único, jerarquía visual, una tarea a la vez, pocas opciones y memoria de trabajo.
- **Discutido:** agrupación por partes —la tabla sí tiene grupos y expansión, pero cada fila sigue acumulando decisiones—.
- **Pasa:** agrupación general en lateral/cabecera/métricas/tabla y divulgación progresiva de archivos/planilla.

## Recorrido emocional

1. **Entrada — incertidumbre:** “Selecciona una semana” orienta, pero no explica el primer paso.
2. **Selección — confianza moderada:** semana activa y métricas ayudan; falta leyenda de colores.
3. **Edición OT — control con fricción:** tags y planilla son potentes, pero no se explica el formato admitido.
4. **Carga/revisión — cautela:** hay estados de carga y zona de arrastre; descubrir la expansión de carpeta no es obvio.
5. **Sincronización — pico de tensión:** acción amplia sin vista previa del alcance.
6. **Cierre — alivio incompleto:** badges/progreso ayudan, pero un fallo no queda resumido con contexto y reintento.

## Fortalezas y señales de personas

- **Fortalezas:** modelo de semana→factura→OT→archivos→sync coherente; planilla/pegado/exportación aceleran trabajo; carga, badges y progreso ya forman una base de estados.
- **Alex (experto):** falta selección múltiple/atajos; el lote semanal es amplio pero poco controlable.
- **Jordan (primera vez):** abreviaturas, formato OT y acciones de icono no se explican lo suficiente.
- **Sam (accesibilidad):** algunos controles son div/otros elementos clicables; faltan foco visible y anuncios live; los estados documentales sí tienen ARIA.

## Señales adicionales

- El detector encontró **17 advertencias por corrida**: 13 de contraste bajo y 4 de encabezados salteados. Ejemplos: #A3AED0 sobre blanco 2.2:1 (repetido), sobre #F4F7FE 2.1:1; blanco sobre #868CFF 2.9:1; ámbar #F59E0B sobre blanco 2.1:1 y verde #01B574 sobre blanco 2.7:1. Los valores de texto no alcanzan 4.5:1 y estados no textuales 3:1 donde aplica.
- La hoja no declara media queries; el ajuste depende de flex y scroll. El control de tema es solo emoji, la modal y la planilla pueden ser anchas, y el título del documento difiere del encabezado visible (“Sincronizador Obras”/“Gestor Obras”).
- La identidad tiene pulido básico, pero Poppins + tarjetas redondeadas + violeta/gradiente no comunica por sí solo el carácter operativo de carpetas y sincronización.

## Pregunta para orientar la siguiente iteración

¿Qué querés priorizar manteniendo intacta la funcionalidad? **A)** seguridad y resumen de la sincronización semanal; **B)** lectura de filas y estados documentales compactos pero inequívocos; **C)** recuperación de errores y accesibilidad de teclado.
