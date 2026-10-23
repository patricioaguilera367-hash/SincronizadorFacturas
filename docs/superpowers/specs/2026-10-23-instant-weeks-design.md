# Semanas instantáneas — diseño acordado

**Objetivo:** al seleccionar una semana, mostrar su último estado conocido inmediatamente; validar el estado real en el NAS en segundo plano y sustituirlo sin intervención del usuario.

**Restricciones:** mantener NAS como fuente de verdad; jamás editar o sincronizar desde datos sin verificar; aprovechar el snapshot local existente; seguir funcionando sin conexión como solo lectura; sin nuevas dependencias ni base de datos.

**Alternativas consideradas:** (1) seguir esperando siempre al NAS — datos frescos, pero 200–800 ms de espera; (2) caché sólo en memoria — instantánea después de la primera visita, pero no sirve tras reiniciar; (3) snapshot persistente existente + memoria corta + actualización en segundo plano — elegida porque sirve en ambos casos y el backend sigue validando contra NAS.

**Diseño:** exponer una lectura local de snapshot sin comprobar SMB; en la UI mostrar caché y marcarla temporalmente solo lectura mientras `/api/facturas` carga en paralelo. La respuesta fresca reemplaza filas y desbloquea operaciones. Si falla la consulta, conservar caché visible pero bloqueada o dejar reintentar si no hay caché. Ignorar respuestas tardías de semanas anteriores.

**No objetivos:** modificar rutas de escritura, ejecutar código en el NAS, garantizar tiempos exactos o instalar infraestructura.
