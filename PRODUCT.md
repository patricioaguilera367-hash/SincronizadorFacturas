# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary user is inferred to be internal operations or administration staff who organize invoice folders, associate them with work orders (OTs), and track payment-document progress. This inference comes from the Spanish operational UI, invoice terminology, and shared-folder workflow; the exact role split between administration and site supervision remains an open decision.

## Product Purpose

Gestor Obras is an internal web tool for organizing weekly invoice folders and synchronizing their files with the corresponding work-order folders. It makes invoice-folder completeness and synchronization status visible while reducing manual copying and folder navigation. Success means a user can select a week, update its invoice folders and OTs, synchronize the right files to the right works, and immediately see what still needs attention.

## Positioning

Its distinct mechanism is folder-first synchronization driven by OT codes: an invoice folder is the working unit, and the server maps each OT to a matching work folder before copying its contents. The same working view also tracks payment-document statuses and metadata drift.

## Operating Context

- Windows internal-network workflow using UNC paths to shared folders.
- The server reads invoice data from `\\192.168.99.61\obras\Facturas pensiones\Facturas pensiones` and work folders from `\\192.168.99.61\obras`.
- `INICIAR_APP.bat` starts the Flask server on `http://localhost:5001` with the local Python executable.
- Users work in a browser and operate on weekly folders, invoice folders, OT codes, uploaded files, and synchronization actions.
- Synchronization writes hidden `.sync_state.json` metadata and excludes that metadata plus `OT.txt` and `ignorado.txt` from copied work-folder content.

## Diagnóstico de rutas (solo lectura)

`INICIAR_APP.bat` ofrece la opción **Trazar rutas OT y facturas (solo lectura)** para aislar problemas de acceso antes de intentar una sincronización. Muestra la identidad actual de Windows y siempre imprime la ruta probada, el resultado y el error recibido.

| Opción | Qué comprueba | Límite y resultado |
|---|---|---|
| Rutas base | Las rutas documentadas de Facturas y Obras. | Distingue accesible, inaccesible, no encontrada y error. |
| Buscar OT | Carpetas bajo `\\192.168.99.61\obras` cuyo nombre coincide después de ignorar caracteres no alfanuméricos; muestra tanto la OT ingresada como el nombre localizado. | Omite el subárbol `Facturas pensiones`; solo lectura, profundidad máxima 4 y hasta 1500 carpetas. Distingue no encontrada, inaccesible, error de lectura y límite alcanzado. |
| Ruta de factura | Una ruta relativa proporcionada por el usuario bajo la base documentada de Facturas. | Rechaza rutas absolutas, UNC y `..`; distingue la primera ruta faltante o inaccesible que impide continuar. |

El menú muestra la identidad actual de Windows y no copia, crea, elimina ni modifica archivos, incluida la carpeta compartida UNC. Tampoco ejecuta la sincronización: solo indica si sus rutas de entrada son legibles y si una OT puede localizarse dentro del alcance revisado. `servidor.py` está fuera de alcance, por lo que el menú no puede instrumentar sus rutas internas, su lógica de emparejamiento ni sus resultados de sincronización; para ello se debe revisar el registro del servidor en una tarea autorizada aparte.

## Capabilities and Constraints

- List and select invoice weeks; create the next week.
- Create, rename, delete, and ignore invoice folders.
- Edit OT codes as tags, paste tabular data, and use a spreadsheet-style batch editor.
- Upload, list, and open files inside an invoice folder.
- Synchronize one invoice folder or a full week to matching work folders.
- Show synchronization, missing-file, changed-file, and OT mismatch states.
- Track invoice receipt, payment-request email, and payment-proof states in hidden metadata; keep current and synchronized values separate so drift is detectable.
- Preserve the existing Flask plus single-template architecture and avoid introducing dependencies unless a future requirement proves the current stack insufficient.
- Preserve existing folder paths, file names, OT matching behavior, and operational flow unless a future change explicitly authorizes otherwise.
- The interface currently supports light/dark mode and Spanish operational copy.

## Brand Commitments

- Existing product name: `Gestor Obras` / `Sincronizador Obras`.
- Existing interface language: Spanish.
- Existing voice: direct, operational, and action-oriented.
- Existing type choice: Poppins loaded from Google Fonts; future visual work may refine the system without changing product terminology casually.
- No supplied logo, brand guide, or approved imagery was found. Future work must not fabricate brand assets or claims.
- The user explicitly requires preserving purpose, flow, and functionality while allowing a substantial visual and UX improvement.

## Evidence on Hand

- `servidor.py` — Flask application, filesystem operations, synchronization logic, API routes, and metadata handling.
- `templates/index.html` — the existing single-page interface, inline CSS, browser behavior, spreadsheet mode, dark mode, and status controls.
- `INICIAR_APP.bat` — local Windows launch command and runtime entry point.
- `odd/tasks/factura-estados.md` — prior implementation record for document-status controls and verification evidence.
- No visual regression fixtures, design system document, product brief, logo, or approved image assets were found.

## Product Principles

1. Keep the folder and OT workflow legible before adding visual expression.
2. Make synchronization risk and missing documentation visible at a glance.
3. Prefer direct actions, reversible edits, and clear feedback over hidden automation.
4. Treat shared-folder paths and existing metadata as operational contracts.
5. Improve visual quality without changing the user's mental model or data flow.

## Accessibility & Inclusion

No product-specific accessibility standard was confirmed during init. Preserve and improve keyboard access, visible focus, readable contrast, tooltip or accessible-label coverage for icon-only controls, responsive behavior, and non-color-only status communication in future UI work.

## Open Decisions

- Confirm whether administration, work supervision, or both are the primary audience.
- Confirm the required browser set and minimum supported viewport sizes.
- Confirm whether the application will remain restricted to the internal Windows network.
