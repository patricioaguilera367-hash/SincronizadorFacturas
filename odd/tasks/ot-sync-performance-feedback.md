# OT Sync Normalized Lookup and Feedback

## Objective
Make OT synchronization find normalized folders promptly, report useful progress and failures, and retain safe support for nested folders and multiple OTs per invoice.

## Problem and Why
The provided OT `206/NT-591` remains slash-delimited after parsing. The direct path-component guard rejects it, so lookup falls through to a recursive Obras walk; the UI waits on a single fetch with no timeout or useful in-flight status. Automated diagnosis also found a red baseline that must be reconciled without weakening assertions.

## Scope and Constraints
- Authorized files: `servidor.py`, `templates/index.html`, focused tests under `tests/`, and this task document.
- Keep path containment and symlink protections; preserve nested-directory matches, single/batch payload shapes, and multiple OTs per invoice.
- No new dependency, server permission changes, UNC/live-share access, credential/session use, destructive production tests, file deletion/overwrite, directory restructuring, or unrelated cleanup.
- Actual effective SMB permissions remain unverified unless separately authorized with a named credential/session. Test expected permission failures only on local temporary paths/mocks.
- CodeGraph is unavailable for this nested workspace; focused delegated mapping was used.

## TDD and Delivery
- TDD: enabled by project instructions (`AGENTS.md`).
- Runner: `python -m unittest discover -s tests -p "test_*.py"` (from existing shared-folder sync task).
- Route: delegated direct. Trigger: mapping required four or more files; implementation spans non-trivial backend, frontend, and regression-test changes.
- Forecast: approximately 300 authored changed lines, excluding generated files and this task document.
- Delivery strategy: `ask-on-risk`; no remote delivery is authorized. Git resolves to `C:\Users\Supervisor`, outside the writable workspace, so work-unit commits cannot be created here.

## Tasks
- [ ] OTSYNC-001 — Reproduce, correct, and verify OT lookup and user feedback.
  - Acceptance: a local temporary `206_NT_591` directory is found from `206/NT-591` without walking the whole tree first; recursive fallback remains for nested legacy folders and stops once unresolved requested OTs are found; multiple OTs stay supported; lookup/copy/directory errors are visible and timed; the UI shows an in-progress state, useful error/success details, and does not wait indefinitely for a request; path boundaries remain enforced.
  - Checks: strict-TDD RED for the normalized direct-path regression and applicable UI/error cases; focused tests GREEN; full runner GREEN or exact remaining baseline failures explained. Never exercise the production share.
  - Route evidence: delegated mapping confirmed slash validation, direct-path rejection, recursive fallback, broad exception handling, and unbounded frontend fetch. Writer must load the matching skills before reading/editing.

## Baseline Evidence
- Read-only flow map: button handlers in `templates/index.html` call `/api/sincronizar` or `/api/sincronizar_todo`; backend route and lookup/copy helpers are in `servidor.py`.
- Baseline runner: 82 tests, 75 passed, 6 failed, 1 skipped. Failures: `test_sync_all_keeps_the_existing_in_root_result_shape`, `test_sync_all_lists_obras_once_for_multiple_invoices`, `test_sync_defers_obras_metadata_and_skips_unsafe_match`, `test_sync_reports_a_matching_ot_folder_when_its_metadata_is_denied`, `test_sync_reports_ot_write_and_state_write_failures`, and `test_sync_single_persists_ot_before_matching_state`.
- No UNC share, credentials, ACLs, or server data were accessed.

## Progress
- [x] Mapped frontend-to-backend flow and verified preliminary direct-lookup/recursive-scan hypotheses against source.
- [x] Reproduced the current local automated-test baseline; no source changes made yet.
- [ ] Implement OTSYNC-001, then record focused and full verification evidence.

## Next Step
Delegate one bounded writer to add red regressions first, implement the minimal backend/frontend correction, and run the listed test runner. Reconcile any baseline failures without weakening contract assertions.

## Relevant Files
- `servidor.py` — OT validation, directory discovery, copy, state persistence, and backend response.
- `templates/index.html` — individual and batch sync requests and user-facing status.
- `tests/` — local filesystem and frontend regression coverage.
