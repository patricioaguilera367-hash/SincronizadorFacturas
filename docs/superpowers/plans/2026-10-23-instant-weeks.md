# Instant Weeks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** cargar de inmediato una semana cacheada y verificarla en segundo plano sin permitir edición de datos obsoletos.

**Architecture:** una ruta Flask local devuelve el snapshot existente. La UI consulta caché y NAS sin bloquearse mutuamente; renderiza caché antes de la respuesta fresca si está disponible.

**Tech Stack:** Flask + JavaScript vanilla + unittest/Node.js.

**Spec:** `docs/superpowers/specs/2026-10-23-instant-weeks-design.md`

## Global Constraints

- Mantener NAS como fuente de verdad y el sistema offline como solo lectura.
- Sin dependencias nuevas; conservar el contrato JSON de `/api/facturas`.

## Review Focus

- Semana sin snapshot: no pintar un estado antiguo de otra semana.
- Error o timeout del NAS: mantener caché en solo lectura.
- Navegación rápida: una respuesta tardía no reescribe otra semana.
- Sincronización exitosa: refrescar datos y habilitar escritura.
- Snapshot local ausente/corrupto: no impedir lectura fresca.

### Task 1: Lectura rápida local

**Files:** `servidor.py`, `tests/test_nas_portable.py`.

- [x] Crear test de lectura exacta sin usar NAS, ausencia 404 y validación 400.
- [x] Ejecutar y observar fallo por ruta ausente.
- [x] Implementar `GET /api/facturas_cache?semana=...` sobre `snapshot_facturas`.
- [x] Ejecutar tests y confirmar verde.

### Task 2: Render instantáneo y verificación

**Files:** `templates/index.html`, `tests/test_stale_revalidate.py`.

- [x] Crear test dinámico Node.js: caché visible/solo lectura antes de respuesta NAS, desbloqueo al llegar, errores y cambios de semana.
- [x] Ejecutar y observar fallo por flujo ausente.
- [x] Extraer render existente sin duplicarlo; añadir caché corta en memoria, petición local y petición fresca concurrentes, y control de solo lectura temporal.
- [ ] Ejecutar tests completos y compilar Python; revisar diff y publicar en rama `feature/portable-v1.2.0`.
