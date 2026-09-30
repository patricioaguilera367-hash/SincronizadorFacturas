# Color System

## Objective
Establish a cohesive, role-based palette for the existing operations UI that improves action, selection, status, and wayfinding without replacing its product identity.

## Problem and Why
The single-page UI mixes one violet accent across primary actions, links, selections, tags, metrics, hover and focus states. A pale gradient stop fails text contrast, several state-control colors fail non-text contrast, and a few colors bypass theme tokens. Light and dark themes do not yet compose all status/control roles consistently.

## Scope
- `templates/index.html` — semantic color tokens, light/dark mappings, interactive and state colors, focus/selection, and current warning/error class mapping.
- `DESIGN.md` — document palette roles and usage.
- `tests/test_color_system.py` — focused standard-library checks for semantic tokens and key light/dark contrast pairs.

## Design Direction
- Operate-mode productivity UI: cool, restrained, neutral layered surfaces; violet remains a rare incumbent signal for primary action, selection, focus, and links.
- Keep existing product semantics: success green, warning/attention amber, error/destructive red, ignored/neutral slate. Avoid new decorative colors and the primary-button gradient.
- Compose dark mode by role rather than mechanically inverting light values; preserve visible text/icon/focus contrast and non-color state cues.
- Violet is an inferred incumbent convention from the UI, not a formally approved brand color; the user's request explicitly asks to derive from the existing interface.

## Constraints
- Preserve existing workflows, Spanish UI copy, and light/dark behavior.
- No new dependencies, font families, image assets, or remote fetches.
- Strict TDD is enabled by session instructions; exact runner authorized earlier for this CSS/markup-only work: `python -m unittest discover -s tests -p "test_*.py"`.
- Engram mirror is pending: the memory write failed because multiple active runtime sessions match this project/directory.
- Git metadata resolves to `C:\Users\Supervisor`, outside the writable workspace; do not stage or commit against that home-level repository.
- CodeGraph initialization was previously rejected because Git resolves to the home directory; do not use the home index for this workspace.
- No project skill registry was found; follow the installed Impeccable, Ponytail, and documentation skills passed to the writer.

## Authorized Scope
Implement the requested interface palette and its focused documentation/tests in this workspace. Do not change operational behavior or touch network-share paths.

## Acceptance Criteria
- Every color has a stable semantic role or a clear status/wayfinding purpose; arbitrary one-off values are consolidated.
- Primary action and selection are immediately legible; secondary controls remain quiet; success/warning/error/neutral meanings stay consistent.
- Light and dark variants meet WCAG AA text contrast (4.5:1) and non-text contrast (3:1) for interactive icons/controls/focus.
- Selection and status are not conveyed by color alone; active selection has a programmatic state and a visible indicator with at least 3:1 contrast against adjacent surfaces.
- The palette retains the existing product feel and does not resemble a marketing landing page.
- `DESIGN.md` and regression tests match the implementation.

## Checks
- Read-only map: `PRODUCT.md`, `DESIGN.md`, `templates/index.html`, backend status mapping, existing tests and assets reviewed by delegated explorer.
- No formal brand guide/assets exist; incumbent violet is #4318FF; no separate stylesheet or theme asset tree exists.
- The current primary button's pale gradient stop yields 2.91:1 with white text; solid incumbent violet yields 7.46:1.
- State-control icon contrasts include 1.96:1 for light amber, 2.37:1 for light green, and 1.90:1 for dark violet sent state.
- Review mode/risk remain unknown: prior status reported off but failed home-level Git authority validation; assessment was unavailable. No native lifecycle started.
- Visual browser evidence is not yet available; avoid fetching external resources.
- Impeccable does not support a `color` detector scope. The full scan returned 5 findings; after tokenizing the status-dot shadow, the final full scan returned 4 unrelated transition/radius advisories.
- Independent verification found the active-week selection surface too subtle (1.25:1 light, 1.12:1 dark; active marker 1.96:1 dark), no programmatic selected-state cue, two remaining raw shadows, and stale selection guidance in DESIGN.md. The source was corrected in one bounded TDD pass; a final read-only review confirmed selection contrast/state and paste feedback, and the parent reconciled the design text. The unrelated responsive-breakpoint note in DESIGN.md remains pre-existing.
- Final rendered/browser preview was not performed; no browser or remote resources were used.

## Tasks
- [ ] COL-001 — Implement and verify the semantic color system across template, tests, and design documentation.
  - Route: delegated direct. Trigger evidence: understanding required mapping 4+ files; writing CSS/markup, docs, and tests is multi-file non-trivial.
  - TDD: enabled; exact runner: `python -m unittest discover -s tests -p "test_*.py"`; writer must report RED before source edits, then GREEN and REFACTOR.
  - Forecast: approximately 230 authored changed lines, generated files excluded.
  - Delivery strategy: `ask-on-risk` (default); forecast below the approximately 400-line slice budget.
  - Progress: implementation and focused verification are complete. The active-week marker now has theme-aware contrast and dynamic `aria-pressed`; semantic shadow tokens cover the UI; DESIGN.md was reconciled with the final state. The task stays open only because the required work-unit commit cannot be made from the authorized writable root.
  - Verification evidence: strict TDD RED/GREEN observed for both source batches; final `python -m unittest discover -s tests -p "test_*.py"` — `Ran 15 tests`, `OK` (parent spot-check). Final `impeccable.cmd detect --json templates/index.html` — exit 0, no color findings; one layout-transition and three radius advisories remain. Independent review verified token coverage, contrast, warning/error semantics, active state, and paste feedback; it found a documentation mismatch, which was corrected and read back.
  - Commit evidence: unavailable; Git metadata resolves to `C:\Users\Supervisor`, outside the writable workspace. Independent verification is complete; this documentation-only reconciliation was read back.

## Next Step
No source changes remain. The work-unit commit is unavailable because Git metadata resolves outside the authorized writable root; the Engram mirror is pending because multiple runtime sessions match. Do not stage/commit to the home-level Git metadata or expand scope for the pre-existing responsive-doc and detector advisories.

## Relevant Files
- `templates/index.html` — single-page UI, inline theme tokens and rendering logic.
- `DESIGN.md` — existing “Document Operations Desk” design description and color guidance.
- `tests/test_color_system.py` — semantic role, contrast, and theme-token regression checks.
- `odd/tasks/color-system.md` — ODD task and recovery record.
