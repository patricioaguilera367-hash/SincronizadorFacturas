# Feature: layout-redesign

## Objective
Redesign the full existing application layout to improve hierarchy, desktop space usage, alignment, spacing rhythm, density, semantic grouping, and responsive behavior without changing product behavior or architecture.

## Problem
The current single-template dashboard uses a fixed 300px week rail, separate scrolling regions, generous repeated panel spacing, a dense invoice row, and no breakpoint-based layout. The desktop viewport is underused and smaller screens rely on incidental scrolling.

## Why
The user explicitly requested a complete layout redesign while preserving functionality, data, and the current HTML/Flask architecture, with no unnecessary dependencies.

## Scope
- Edit only `templates/index.html` for layout and responsive structure; preserve existing JS behavior, selectors, IDs, API calls, data, and Spanish UI copy.
- Keep the existing design identity and palette; the layout may change hierarchy and grouping as explicitly requested.
- Spatial thesis: week orientation → selected-week anchor → compact attention summary → invoice workbench → expanded files → synchronization. Each invoice reads left-to-right as identity → OT → document states → actions. Reflow records at narrow widths; retain deliberate horizontal scrolling only for the spreadsheet grid.
- Do not access UNC shares, run Flask/API calls, add dependencies, update DESIGN.md, or redesign visual identity in this task.

## Constraints
- User selected option B: an explicit TDD exception for this layout-only task. Do not create test infrastructure or dependencies. Verify with one post-edit Impeccable layout detector run, code/source review, and preservation checks.
- Strict TDD remains enabled outside this feature. The workspace has no configured runner, tests, visual fixtures, or browser surface; do not invent a test command or claim rendered verification.
- TDD mode for this feature: waived by explicit user choice `B)` after disclosure. Runner: none. Verification command: `C:/Users/Supervisor/.agents/skills/impeccable/scripts/impeccable.cmd detect --json --scope layout templates/index.html` (run once after the edit); plus parent static readback.
- Receipt-driven development status output reported `off`, but the command also failed on unsafe external `.git` ownership validation; keep the failure visible and do not start a review while disabled.
- Git root resolves to `C:\Users\Supervisor` outside the writable workspace; the target is currently untracked. Do not write to external `.git`; commit/branch may remain pending.
- Delivery strategy: `ask-on-risk`; initial changed-line forecast: 300 authored lines (one template file, generated files excluded).

## Acceptance Criteria
- The week → invoice → OT → files → sync workflow, all existing controls, callbacks, selectors, and data remain functional and unchanged.
- Desktop layout uses available width deliberately and makes the selected week and invoice workbench the visual anchors.
- At narrow and intermediate widths, content reflows intentionally without obscuring actions or requiring accidental page-level overflow.
- No new dependency or backend/API change.
- One final Impeccable layout detector scan is recorded; findings are addressed or explained. Browser/rendered verification is explicitly unavailable.
- Worktree changes are read back; external `.git` is not modified.

## Tasks
- [x] T1 (delegated direct): Refactor the layout in `templates/index.html` using the spatial thesis, retaining every existing functional hook and visual identity. **Verified:** one-file CSS/layout edit (~105 authored lines); added 1080px/720px reflow and mobile stacked records. Parent review found and the writer corrected two desktop regressions before detector: constrained grid/main scroll and collapsed sidebar track.
- [x] T2 (delegated verification): Ran the Impeccable layout detector once after T1 and inspected the output; no findings.
- [x] T3 (inline integration): Reconciled source and verification evidence; recorded that repository metadata is outside the writable workspace, so no commit was attempted and no external `.git` was modified.

## Progress
- Route: delegated direct for T1; delegated mechanical verification for T2; inline for T3.
- Trigger evidence: source reading prepares an authorized nontrivial layout write; a read-only layout mapping was delegated before implementation.
- Read-only assessment found the current path at `templates/index.html:128-203`, row structure at `:476-524`, fixed 300px rail and separate scroll regions at `:21-37`, `:111-123`, and no media queries.
- Browser surfaces unavailable; no server, app API, or UNC share accessed.
- Engram task mirror pending: `mem_save` failed because multiple active runtime sessions match this project and directory; no session ID was available to select safely.

## Verification Evidence
- T1: writer reported preservation of IDs/handlers/API routes and static syntax check; parent re-ran `node --check` against the extracted inline script: PASS.
- Parent source readback confirmed 1080px/720px breakpoints, labeled narrow-screen cells, `min-height: 0` scroll containment, desktop rail track collapse, and unchanged mobile collapse behavior.
- Parent spot checks confirmed the selected responsive layout hooks and `toggleSidebar()`/invoice-rendering behavior remain present; the target was untracked at baseline, so a Git diff against a tracked pre-edit version is unavailable.
- T2: `C:/Users/Supervisor/.agents/skills/impeccable/scripts/impeccable.cmd detect --json --scope layout templates/index.html` — exit 0; stdout `[]` (no findings).
- Browser render, app/API, and UNC checks were not run; no browser surface is available and network-share reads are outside scope.
- Commit remains pending because the Git metadata root resolves outside the writable workspace; no external `.git` access or mutation was performed.

## Next Step
Implementation and local verification are complete. Remaining limits: no browser/rendered check, no commit because the Git root is outside the writable workspace, and Engram mirror pending because runtime-session selection is ambiguous.

## Relevant Files
- `templates/index.html` — single-page UI, inline CSS/JS, layout target.
- `DESIGN.md` — incumbent visual-system baseline; preserve its palette and components but honor the user's explicit authorization to change layout hierarchy.
- `odd/tasks/layout-redesign.md` — task record and verification evidence.
