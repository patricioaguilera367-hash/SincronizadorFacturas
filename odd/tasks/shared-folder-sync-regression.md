# Shared-Folder Sync Regression

## Objective
Restore responsive folder discovery and reliable synchronization against the configured Obras share without weakening filesystem boundaries.

## Problem and Why
- Startup scans every invoice to determine week badges and repeatedly resolves paths on a network share; one inaccessible child aborts the entire response.
- Synchronization rescans Obras per invoice, may hide OT write failures, and may return a server error after copying when state persistence fails.
- These are code-level findings. SMB latency, permissions, and the Python process identity have not been measured on the actual share.

## Scope and Constraints
- `servidor.py`, `templates/index.html`, and focused tests in `tests/`; preserve route payloads, Spanish UI copy, path containment, and symlink rejection.
- No new dependency, global stale cache, credential change, or direct access to `\\192.168.99.61\Obras` without explicit authorization for the credential/session.
- Strict TDD enabled by project instructions. Runner: `python -m unittest discover -s tests -p "test_*.py"`.
- Git resolves to `C:\Users\Supervisor`, outside the writable workspace. Do not stage or commit to that home-level Git metadata.
- CodeGraph is unavailable for this nested workspace because its Git root is the home directory; delegated filesystem mapping supplied the code evidence.

## Delivery
- Forecast: about 340 authored changed lines, excluding this task document.
- Strategy: `ask-on-risk`; no PR or remote delivery authorized.
- Work-unit commits are pending because repository metadata is outside the writable workspace.

## Tasks
- [x] SFS-001 ? Reduce and isolate folder-discovery work.
  - Route: delegated direct. Trigger: startup path handling and regression tests require two non-trivial files; mapping covered four or more files.
  - Acceptance: startup lists available weeks without repeatedly scanning every invoice for badges; unavailable/inaccessible children do not hide otherwise available weeks; untrusted names and links cannot escape the approved root.
  - Checks: RED observed (`python -m unittest tests.test_async_recovery.AsyncRecoveryTests.test_initial_week_render_executes_without_undefined_bindings` failed: week button was not rendered); runnable Node DOM-stub renderer regression passed with four related focused checks (5 tests total). Full `python -m unittest discover -s tests -p "test_*.py"` passed (75 tests, 1 skipped).
- [x] SFS-002 ? Make synchronization consistent and avoid repeated Obras scans.
  - Route: delegated direct. Trigger: shared sync behavior and tests require two non-trivial files.
  - Acceptance: a batch lists Obras at most once; failed OT or state writes never report success; single and batch routes use the same durable OT content before state records it; copy failures remain visible; boundary protections remain intact.
  - Checks: RED observed (`python -m unittest tests.test_filesystem_boundaries.FilesystemBoundaryTests.test_sync_uses_direct_ot_folder_when_obras_listing_is_denied` returned Obras access error); focused GREEN passed (5 SFS sync tests); full `python -m unittest discover -s tests -p "test_*.py"` passed (80 tests, 1 skipped).
- [x] SFS-003 ? Distinguish inaccessible OT folders from missing ones and refresh week badges without clearing the list.
  - Route: delegated direct. Trigger: backend and UI behavior plus regression tests span three non-trivial files.
  - Acceptance: an OT folder that exists but denies metadata access is not reported as nonexistent; single and weekly sync share the same diagnosis; finishing a sync refreshes existing week badges in place instead of clearing/rebuilding the sidebar.
  - Checks: strict TDD RED observed (2 new regressions failed before implementation); focused sync tests passed (28, 1 skipped); full `python -m unittest discover -s tests -p "test_*.py"` passed (82, 1 skipped); independent `python -m unittest tests.test_filesystem_boundaries` passed (28, 1 skipped).

## Progress
- Read-only flow mapped in `servidor.py` and `tests/test_filesystem_boundaries.py`; no UNC access.
- SFS-001 complete: initial and detailed rendering both use the shared status updater after status child nodes exist; the Node DOM-stub regression executes this path.
- SFS-002 complete: direct approved OT folders synchronize without root listing; batch shares one lazy fallback list only when a direct path is absent.
- SFS-003 complete: direct and listed OT candidates now distinguish `PermissionError` from absence; single and batch responses share that diagnosis. Sync completion refreshes existing week badges in place with `initSemanas(true)`, avoiding sidebar clear/rebuild. No UNC/live-share access performed.
- Engram mirror pending because multiple active runtime sessions match this workspace and no authoritative session ID is available.

## Next Step
SFS-001, SFS-002, and SFS-003 are complete. Request separate authorization before any live-share test. Work-unit commit remains unavailable because the Git root is outside the writable workspace.

## Relevant Files
- `templates/index.html` - weekly sidebar refresh and synchronization handlers.
- `servidor.py` — filesystem guards, listing endpoints, synchronization.
- `tests/test_filesystem_boundaries.py` — local temporary-root regression tests.
