# Clarify UI Copy

## Objective
Make the application's visible Spanish copy concise, consistent, and immediately understandable without changing domain concepts, data meaning, or behavior.

## Problem and Why
- The single-page UI mixes terse abbreviations, inconsistent capitalization, vague feedback, and labels that do not always describe the actual action (for example, copying tabular data to the clipboard is labeled as Excel export).
- User-visible language is split between `templates/index.html` and backend response/status text in `servidor.py`; frontend status text is also used by a few exact-string conditionals, so inconsistent edits can change behavior.
- Clearer labels and outcome messages should reduce operational ambiguity while preserving the current invoice-folder, OT, exception/ignore, payment-document, and synchronization concepts.

## Scope
- `templates/index.html` — visible labels, placeholders, helper text, dialog and feedback copy, dynamic statuses, responsive `data-label` values, and accessible names/semantics for existing icon controls.
- `servidor.py` — user-facing badge/status and API error messages only, preserving response structure, behavior, and domain terms.
- `tests/test_ui_copy.py` or existing focused tests — protect key copy choices, copy/data-label consistency, accessible names, and status-logic semantics without overfitting every literal.

## Design Direction
- Keep existing Spanish product voice, terminology (`OT`, `factura`, `sincronizar`, `ignorado/excepción` where current behavior requires it), and current user mental model.
- Prefer a specific verb plus object, sentence-case labels, and short messages that say what happened and the next useful action when needed.
- Describe actual behavior: clipboard copy is not a file export; folder creation, deletion, ignored/excluded behavior, and synchronization must retain their current consequences.
- Avoid raw exception details as primary user copy when they expose internal paths; keep useful known recovery guidance, without promising unknown causes.
- Keep the change to copy and existing accessible names; do not add features, change API schemas, alter filesystem/synchronization behavior, or introduce a translation framework.

## Constraints
- Preserve all domain concepts, data semantics, paths, operations, API structure, Spanish language, and existing workflow.
- Strict TDD enabled (project/session instruction); exact runner: `python -m unittest discover -s tests -p "test_*.py"`.
- The repo does not have a workspace-local CodeGraph index. `codegraph_explore` reported unindexed and `gentle-ai codegraph init --cwd <workspace>` refused with `unsafe CodeGraph root`; use ordinary bounded source inspection as fallback, with no further CodeGraph attempts this task.
- Git root resolves to `C:\Users\Supervisor`, outside the writable workspace. Do not stage/commit or alter that metadata.
- Engram task mirror is pending: project/session lookup has multiple active runtime matches; preserve this local document and do not invent a session ID.

## Authorized Scope
Clarify all visible application labels, placeholders, buttons, states, and messages as requested. User explicitly authorizes meaningful implementation and says not to ask for approval. No business/product decision is delegated; preserve uncertain domain vocabulary instead of redefining it.

## Acceptance Criteria
- Visible copy across the frontend and backend is consistent, concise, grammatical, and accurate about the current action/result.
- Every reworded action describes its actual outcome; ambiguous or high-consequence messages identify the affected object and consequence.
- Existing business terms, behavior, API response shape, status transitions, exact-string-dependent flow, and data semantics remain unchanged.
- Screen-reader names and mobile `data-label` values remain aligned with visible controls/headings; icon-only existing controls have clear names.
- Existing icon-only sidebar/theme controls expose native or equivalent keyboard-operable semantics without adding a new user action.
- Focused regression assertions and the exact full test suite pass; the Impeccable detector is run once after the final UI edit.

## Checks
- Read-only map by `/root/clarify_copy_map` reviewed the single-page UI and backend response/status paths; exact copy sources are `templates/index.html` and `servidor.py`; copy-bearing user-visible messages are tested by the full Python unittest suite.
- CodeGraph query was unavailable because this workspace is not indexed; initialization refused an unsafe root. Exploration therefore used the delegated bounded filesystem fallback.
- TDD: enabled by current project instructions; assertions-first RED observed before source edits (30 tests/4 expected failures for first pass; 31 tests/1 expected failure for the icon-control correction), then GREEN.
- Independent verification first identified an accessibility gap: the sidebar toggle was a clickable `div` without keyboard/button semantics or a name, and the theme icon button lacked an accessible label. The correction is now covered and independent verification passes.
- Runner: `python -m unittest discover -s tests -p "test_*.py"`.
- Final GREEN and parent spot-check: 31 tests passed (independent verifier: 0.027s; parent: 0.032s). No browser preview was available.
- Final Impeccable detector: exit 0. It reported one `layout-transition` warning for `transition: max-height, margin` and four advisory radius-token findings (`3px`, `6px`, `999px`, `4px`); these are outside the copy/accessible-name scope and no detector-driven edits were made.
- Delivery forecast: approximately 250 authored changed lines including tests, generated files excluded; strategy `ask-on-risk` (no chain decision required at this forecast).
- RDD: off (`clone_local`). Candidate assessment was high/unassessable because `C:\Users\Supervisor\.git` failed safe ownership validation and untracked-file enumeration exceeded the 8 MiB limit (243001 entries); independent verification was therefore required. No review lifecycle is being attempted.

## Tasks
- [ ] COPY-001 — Clarify frontend and backend UI copy as one coherent work unit, with regression coverage.
  - Route: delegated direct. Trigger evidence: broad map required 4+ source/interaction areas and the implementation spans non-trivial frontend, backend, and test changes.
  - TDD: strict; add/adjust regression assertions first and observe RED before changing source copy.
  - Scope fence: no feature/flow/API-schema/domain changes; preserve exact-string behavior checks or update their coupled assertions when copy-only semantics remain equivalent.
  - Progress: frontend/backend copy, status/accessibility assertions, native menu-button semantics, and theme-control accessible names are implemented. Independent verification and the parent test spot-check pass. The source outcome is complete; task remains unchecked only because the required work-unit commit cannot be made outside the writable Git root.
  - Commit evidence: unavailable while Git metadata remains outside the writable workspace.

## Next Step
Implementation, regression tests, independent verification, parent spot-check, and the final detector run are complete. Remaining process items: mirror this document if a unique Engram session becomes available; create the work-unit commit only when the Git metadata is inside an authorized writable workspace. Do not bypass either boundary.

## Relevant Files
- `templates/index.html` — UI labels, dialogs, dynamic statuses, accessibility names, and browser behavior.
- `servidor.py` — backend badge/status and API message strings.
- `tests/test_ui_copy.py` — copy and accessible-control regression coverage.
- `tests/test_color_system.py` — updated copy-sensitive assertions.
- `odd/tasks/clarify-ui-copy.md` — task/proof record.
