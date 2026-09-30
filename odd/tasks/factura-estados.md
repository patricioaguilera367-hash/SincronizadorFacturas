# Feature: factura-estados

## Objective
Add three compact circular status controls to each invoice folder and persist their current/last-synchronized values in the hidden metadata state.

## Problem
The table only exposes folder synchronization status; operators cannot see whether the invoice, payment-request email, or payment proof are pending/received/sent.

## Why
Make missing payment documentation visible at a glance without adding text to the row, while preserving synchronization drift detection.

## Scope
- Extend the existing `.sync_state.json` schema with current and synchronized document statuses.
- Add a minimal endpoint to cycle/persist one status and make folder sync compare status drift.
- Render three icon-only circular controls immediately left of the existing sync badge, with accessible tooltips/labels and color states.
- Refresh status controls after save/sync/upload actions where needed.

## Constraints
- Reuse the current Flask endpoint and single-page template; no new dependency.
- Status labels live in metadata/tooltips, not visible row text.
- Keep existing sync behavior and ignored folders intact.
- TDD mode: unknown; use focused functional checks after implementation.
- Delivery strategy: ask-on-risk; forecast under 400 authored lines.

## Acceptance Criteria
- Every non-ignored invoice row shows invoice, payment-request, and payment-proof circular controls immediately left of the sync badge.
- Clicking a control cycles only through its valid states and persists the current value.
- Reloading the week restores the selected values.
- A manual status change makes the folder visibly out of sync until the next successful synchronization snapshots it.
- Existing OT/file synchronization and ignored-folder behavior remain unchanged.
- Focused syntax/behavior checks pass.

## Tasks
- [x] T1 (delegated direct): Extend backend metadata, status API, sync comparison, and snapshot behavior in `servidor.py`.
- [x] T2 (delegated direct): Add compact accessible status controls and client-side refresh/cycling behavior in `templates/index.html`.
- [x] T3 (inline verification): Run syntax/static checks and inspect the diff; record any unavailable checks honestly.

## Progress
- Delegated writer completed T1/T2; parent reviewed the resulting backend and template changes.
- Trigger evidence: writer trigger fired (backend + template); CodeGraph unavailable for this nested workspace, so filesystem inspection was used.
- All implementation tasks are complete.

## Verification Evidence
- `python -m py_compile servidor.py` passed.
- Browser JavaScript extracted from `templates/index.html` passed `node --check`.
- Flask template render test passed and included the new controls/endpoints.
- Temporary Flask test verified persistence, drift detection after a manual status change, and clean status after synchronization snapshot.
- Impeccable detector ran once; it reported pre-existing low-contrast and heading-hierarchy warnings in the template.

## Next Step
Feature implementation is complete. A work-unit commit was not created because the repository root is `C:\Users\Supervisor` while the workspace is nested and the sandbox denied writes to the external `.git` ref store.

## Relevant Files
- servidor.py — Flask API and `.sync_state.json` synchronization logic.
- templates/index.html — invoice table markup, styles, and browser behavior.
