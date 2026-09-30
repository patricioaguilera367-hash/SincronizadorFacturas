# Interface Hardening

## Objective
Harden the existing Gestor Obras interface and the filesystem/API boundaries it drives against untrusted or missing data, network failures, large content, unusual viewport/zoom conditions, and keyboard-only use without changing the established visual system or business semantics.

## Problem and Why
- The requested production hardening covers long text, missing data, empty/loading/error states, overflow, inputs, long tables, unusual resolutions, zoom, keyboard navigation, and edge cases.
- A read-only map confirmed that multiple filesystem routes trust caller-provided paths, dynamic shared-folder content is interpolated into HTML/inline handlers, async requests can race or leave loading UI stuck, modal/tag keyboard affordances are incomplete, and some long content can overflow.
- The prior responsive/delight/motion work is complete and must remain intact; this is a separate hardening pass, not a redesign.

## Scope
- `servidor.py` — constrain filesystem operations to their approved invoice/work roots and reject invalid path components.
- `templates/index.html` — safely render dynamic data; make asynchronous states recoverable and resilient to stale responses; harden keyboard semantics and long-content layout.
- Focused automated tests under `tests/`.
- Preserve Spanish UI copy, existing API/domain semantics, folder/work-order behavior, responsive layout, visual tokens, and existing action flow. Do not add arbitrary data/upload limits or alter network binding/debug deployment settings without a product decision.

## Constraints
- No new dependencies.
- Strict TDD: enabled by the current session/project instructions. Exact suite runner: `python -m unittest discover -s tests -p "test_*.py"`.
- No browser or visual QA by the agent; the user will validate the UI manually. Run code tests and the Impeccable static detector once after all UI edits.
- Preserve the existing responsive/delight/motion task and its completed tests.
- CodeGraph is unavailable for this workspace; the delegated read-only map used targeted filesystem exploration instead.
- Do not stage/commit or modify Git metadata outside the writable workspace. Git common root resolves outside the authorized write root; delivery remains uncommitted unless repository metadata becomes writable.

## Delivery
- Forecast: approximately 600 authored changed lines across implementation and tests (generated files excluded).
- Strategy: `ask-on-risk` (default). If commits become available, resolve the required PR-chain strategy before the first commit because the forecast exceeds 400 lines. No PR or remote operation is authorized.

## Tasks
- [x] IH-001 — Constrain filesystem/API paths to approved roots.
  - Route: delegated direct. Trigger evidence: route ownership spans `servidor.py` path resolution plus new regression tests; writer trigger applies to source and test files.
  - Acceptance: all invoice-folder routes (read/write/list/upload/rename/delete/serve/state/ignore/sync) require exactly `BASE_FACTURAS/<week>/<invoice>` depth; week-level routes accept only a validated single week component. Invalid, missing, absolute-outside, traversal, root/week deletion/rename, or escaping symlink paths fail safely; complete write/batch payloads are validated before mutation; tests prove no outside file is created, served, modified, renamed, or deleted; legitimate in-root operations preserve behavior.
  - Progress: completed shared realpath/commonpath containment, exact invoice-folder depth enforcement across all invoice routes, validated week components, root/week destructive-operation rejection, and validate-before-write guards.
  - Verification: RED observed for outside paths, malformed payloads, root/week delete/rename, and five invoice routes accepting week-level paths. Writer and parent full-suite runs GREEN: `python -m unittest discover -s tests -p "test_*.py"` — 64 tests, 1 skipped because Windows denied temporary symlink creation. Independent verification PASS; all tests use temporary roots. Native risk assessment remained high/unassessable because Git enumeration timed out after 2 minutes on 243,000+ untracked entries; RDD status also exited 1 due to the shared Git authority path's ownership. No Git operations were performed.
- [x] IH-002 — Safely render and scale dynamic folder/file data.
  - Route: delegated direct. Trigger evidence: dynamic data is constructed in multiple template render paths and tests; security and long-list rendering require a coordinated source/test edit.
  - Acceptance: untrusted names, paths, and OT text render as text rather than executable markup/handlers; quotes, entities, emoji, and long strings preserve readability; large row lists avoid repeated per-row whole-container rebuilds; existing actions still target the correct row.
  - Progress: completed safe DOM/text/value rendering with listener-bound actions and batched fragment replacement for data lists; Spanish copy, existing actions, API shape, and layout remain unchanged.
  - Verification: RED observed with 3 focused dynamic-rendering failures before implementation. Writer and parent full-suite runs GREEN: `python -m unittest discover -s tests -p "test_*.py"` — 67 tests, 1 skipped because Windows denied temporary symlink creation. Independent verification PASS; no browser/visual QA was run. The intermediate Impeccable detector reported existing layout-transition/radius advisories; final detector remains pending until the remaining UI tasks are complete. Native risk assessment was high/unassessable because Git enumeration timed out after 2 minutes on 243,000+ untracked entries.
- [x] IH-003 — Recover cleanly from API failures, empty data, and out-of-order responses.
  - Route: delegated direct. Trigger evidence: multiple asynchronous load/save/sync handlers and UI states share lifecycle concerns across the template and tests.
  - Acceptance: rejected/slow requests do not leave permanent loading/disabled states; users get concise actionable error/retry or explicit empty/missing states; stale responses cannot overwrite a newly selected week/folder; repeated submission cannot trigger concurrent duplicate destructive actions; API payloads and business meanings remain unchanged.
  - Progress: completed shared HTTP/JSON failure handling, explicit empty/error/retry states, request identity guards for week/folder responses, and per-operation duplicate submission locks with `finally` cleanup. API routes/payload keys unchanged.
  - Verification: RED observed in 2 focused async recovery tests before implementation. Writer and parent full-suite runs GREEN: `python -m unittest discover -s tests -p "test_*.py"` — 69 tests, 1 skipped because Windows denied temporary symlink creation. Extracted-script `node --check` passed; independent verification PASS. Native risk assessment was high/unassessable because Git enumeration timed out after 2 minutes on 243,000+ untracked entries. No browser/visual QA was run.
- [ ] IH-004 — Harden keyboard access and long-content layout.
  - Route: delegated direct. Trigger evidence: modal/tag interaction semantics and responsive text/table containers are in the same large template and require matching regression assertions.
  - Acceptance: modal open/close, Escape, focus entry/return, and tag removal are keyboard-operable and labelled; 100+ character names and large numeric/content values wrap or truncate without hiding access to actions; tables remain contained at narrow widths and 200% zoom; the existing visual design and breakpoints remain otherwise unchanged.
  - Progress: implementation and focused regression coverage are complete; leave unchecked pending parent verification.
  - Verification: RED observed with 3 focused accessibility-hardening failures before implementation. GREEN: `python -m unittest discover -s tests -p "test_*.py"` passed 72 tests with 1 platform skip. Inline JavaScript syntax check and bounded source audit passed; no browser/visual QA was run.

## Checks
- TDD per task: add the narrow regression assertions first and observe RED, implement, observe GREEN.
- Run focused tests while iterating and `python -m unittest discover -s tests -p "test_*.py"` at task closure.
- Run `C:\Users\Supervisor\.agents\skills\impeccable\scripts\impeccable.cmd detect --json templates/index.html` once after all UI edits; treat output as a mechanical check, not visual QA.
- Parent performs the required test spot-check. User performs all visual validation using numbered interactions provided at delivery.

## Progress
- Exploration complete: delegated hardening map and independent path-containment assumption challenge both confirmed concrete findings.
- IH-001, IH-002, and IH-003 are complete; IH-004 is the next implementation task.
- Engram task mirror is pending: `mem_save` could not select a unique active runtime session; local task file is authoritative until Engram is available.

## Next Step
Implement IH-004 in strict TDD; update this document and the Engram mirror after each completed task.

## Relevant Files
- `servidor.py` — Flask routes and filesystem operations.
- `templates/index.html` — main responsive UI, dynamic rendering, and browser interactions.
- `tests/` — current focused UI tests; add boundary-focused route/UI regression coverage.
- `odd/tasks/responsive-delight-motion.md` — completed prior responsive/motion pass; preserve its outcomes.
