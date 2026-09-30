# Responsive Delight and Motion

## Objective
Make the operations desk fit small notebooks through large monitors, then use restrained, accessible motion and interaction feedback to make repeated work feel clear and carefully finished.

## Problem and Why
- The interface already uses responsive grid/table states, a sidebar, expandable invoice rows, modal and spreadsheet flows, status controls, and copy/upload/sync feedback. This pass must strengthen those existing paths rather than add a new product layer.
- The current design records 1080px and 720px breakpoints and a high-density desktop table, but the user requests a deliberate fit from compact notebook screens to wide monitors, including bars, tables, side panels, forms, and modals.
- Purposeful interaction feedback can improve confidence in a repetitive file workflow; generic celebration, hover-only functions, layout jank, and movement that ignores reduced-motion would make the tool slower or less trustworthy.

## Design Thesis
Keep the desk responsive and steady: when work changes, a brief ink-and-violet cue confirms exactly what moved or completed, while layout adapts without losing the dense document ledger.

## Scope
- `templates/index.html` — responsive layout and overflow, touch/focus/hover/selection/empty/loading/success states, existing panel/modal navigation, and purposeful CSS motion.
- Focused UI tests under `tests/` — protect viewport/breakpoint behavior, keyboard/touch affordances, state feedback, and reduced-motion behavior.
- `DESIGN.md` — update responsive and motion conventions only if the implementation changes the existing documented system.

## Direction
- Preserve the ink-and-violet operations-desk identity, Spanish copy, existing concepts, status semantics, data, and workflows.
- Adapt rather than scale: protect the dense multi-column table and sidebar on desktop; use existing labeled row/card behavior at narrow widths; make tablet/small-notebook layouts reflow intentionally; keep large screens efficient instead of stretching content edge to edge.
- Keep all core controls available at every width. Do not rely on hover, conceal actions, add gesture-only behavior, or change the data's information architecture.
- The existing upload must keep drag/drop and expose a native file-picker path for touch/keyboard users; the existing folder-details expander must be keyboard operable. These provide access to existing actions, not new workflow features.
- Add only micro-feedback tied to a real event: week/folder selection, expansion, focus, copy/paste, drag/drop, modal, and operation state. Empty states clarify the next current action. No celebratory animation for routine clicks, fake progress, audio, new assets, or features.
- Motion is quick and calm (roughly 100–180ms for immediate feedback; 150–250ms for routine state changes), uses meaningful state-tied properties, exits quickly, and avoids bounce/elastic curves, broad `all`/shadow transitions, and gratuitous layout animation. Brief sidebar-collapse and progress-fill transitions remain because they directly communicate an existing state change. Preserve semantic state when motion is removed.
- Support `prefers-reduced-motion`, keyboard focus, coarse-pointer touch targets, and non-hover feedback. No dependency or runtime animation framework.

## Constraints
- Do not alter business meaning, filesystem operations, synchronization behavior, status values, API shape, or Spanish UI language.
- Strict TDD enabled by the current project/session instruction. Exact runner: `python -m unittest discover -s tests -p "test_*.py"`.
- The workspace has no local CodeGraph index; CodeGraph exploration reported unindexed and the one `gentle-ai codegraph init --cwd <workspace>` attempt refused `unsafe CodeGraph root`. Use the delegated bounded filesystem map already completed; do not retry CodeGraph this task.
- Git metadata resolves to `C:\Users\Supervisor`, outside the writable workspace. Do not stage/commit or alter external Git metadata.
- Initial task document is mirrored under `odd/responsive-delight-motion/tasks` (observation `#179`, independent project manual-save). The post-implementation mirror write also failed because multiple active runtime sessions match this project and directory, so this local copy remains authoritative until the ambiguity is resolved. Never invent a session ID.
- No browser/app preview is available in the current session; do not claim visual screenshot/device verification.

## Authorized Scope
Implement the requested delight, responsive adaptation, and purposeful animation refinements. The user explicitly authorized implementation and supplied no-permission request. Infer the truncated end of the animation prompt conservatively as “no decorative, elastic/bouncy movement”; ask no permission question.

## Acceptance Criteria
- At narrow mobile/tablet, small notebook (around 1280×720), standard desktop, and widescreen widths, the shell, sidebar, toolbar, tables/row details, forms, and modals remain usable without unintended clipping/overflow or lost core actions.
- Desktop preserves high information density; wide monitors retain a readable working measure; responsive rows preserve existing data labels and operation semantics.
- Hover and touch/keyboard states provide immediate feedback without hover dependency; focus stays visible; existing folder expansion and upload are operable by keyboard/touch; empty/selected/loading/success/error moments accurately communicate the existing state and next available action.
- Any introduced or adjusted motion explains a real state/layout change, remains brief and interruptible, preserves state feedback with reduced motion, and has no elastic/bouncy effect or broad `all` transition.
- Existing copy, interactions, ARIA relationships, statuses, clipboard, upload, sync, and table behavior remain intact.
- TDD RED is observed before UI-source edits; full test suite passes; independent verification passes; run the Impeccable detector once after the final UI edit and report any remaining findings.

## Checks
- Delegated read-only map covered `templates/index.html`, `DESIGN.md`, and focused identity, interaction, copy, typography, and color tests. Implementation is centered on the inline app shell and CSS, status, expansion, copy/paste, modal, and file-feedback paths.
- Product context was loaded earlier this session from `PRODUCT.md` and `DESIGN.md`; this is an internal Spanish operations product with a high-density workflow and no approved assets.
- CodeGraph is unavailable for this workspace because its index is absent and initialization refused the unsafe root; use ordinary bounded delegated exploration as the established fallback.
- TDD: strict; exact runner `python -m unittest discover -s tests -p "test_*.py"`.
- Forecast: approximately 350 authored changed lines (additions plus deletions, generated files excluded); delivery strategy `ask-on-risk`, below the 400-line threshold; no chain decision required.
- RDD: clone-local OFF. Post-implementation native assessment was high/unassessable: the 8 MiB untracked-file enumeration cap was exceeded at 243050 entries. Independent verification was required and completed; do not start review while the user-owned switch is off.
- Verification history: with the new assertions in place and before UI-source edits, the exact suite returned RED (36 tests, 5 expected failures). The first post-implementation run exposed one existing responsive test hard-coded to 720px; it was updated to the new 900px card breakpoint. Final exact-suite run: 36 tests, OK.
- First independent verification: FAIL with two in-scope gaps — folder details used a pointer-only `div` expander, upload was drag/drop-only on touch, and `DESIGN.md:179` still described the sidebar menu as a non-semantic div. Responsive/motion checks otherwise passed; exact full suite passed 36 tests. A single bounded corrective batch is planned, followed by one final verifier; no iterative polish loop.
- Corrective-batch TDD: three focused accessibility assertions were added first; exact suite returned RED (39 tests, exactly 3 expected failures for the picker, folder expander, and stale design note). The bounded correction then added a native picker routed through the existing upload handler, converted the expander to a native button with synchronized `aria-expanded`, and corrected the sidebar documentation. Exact full suite returned GREEN: 39 tests, OK. Independent verification passed and the parent spot-check also passed (39 tests, OK).
- Final Impeccable detector: exit 0 with two layout-transition warnings (purposeful sidebar collapse/progress feedback retained) and four undocumented-radius advisories; no source changes followed. Browser/device runtime verification remains unavailable.
- Visual verification: no browser/device preview is available; no screenshot/device result is claimed.

## Tasks
- [x] RESPONSIVE-001 — Adapt the existing operations shell and work surfaces from compact viewports to wide monitors without losing data or actions.
  - Route: delegated direct. Mapping trigger evidence: responsive layout understanding crossed 4+ UI areas and 6 source/test/doc files; the read-only map is complete.
  - TDD/evidence: assertions added first; RED observed (36 tests, 5 expected failures) before template edits; final verification and parent spot-check passed at 39 tests. Cards and operation actions reflow through 900px, the 901–1080px table scroll is contained, the wide working measure is capped at 1840px, and independent verification passed.
- [x] ANIMATE-001 — Tune existing state/navigation/panel/modal motion for quick continuity with a reduced-motion alternative.
  - Route: delegated direct single writer; implementation overlaps the same app shell and motion tests.
  - TDD/evidence: motion assertions were included in the pre-edit RED suite; final verification and parent spot-check passed at 39 tests. Modal/detail/tag arrivals are short and non-elastic; reduced motion remains active; sidebar collapse behavior is preserved. Detector reports layout-transition warnings for purposeful state-tied sidebar/progress transitions; these were retained.
- [x] DELIGHT-001 — Add restrained, product-specific micro-feedback to meaningful selection, focus, copy/paste, drop, empty, and completion states.
  - Route: delegated direct single writer; keep routine operation neutral, truthful, and repeatable.
  - TDD/evidence: state assertions were included in the pre-edit RED suite; final verification and parent spot-check passed at 39 tests. Copy, successful upload, empty file lists, paste, focus, and coarse-pointer targets use truthful existing workflow states without changing APIs or status tokens. Native file picking and the keyboard-operable expander are covered by regression tests.
- Delivery forecast: ~350 authored changed lines across the three coordinated tasks; one coherent UI work unit. Commit is unavailable outside the writable Git root.

## Next Step
All three tasks are complete: bounded accessibility correction, independent verification PASS, and parent test spot-check PASS (39 tests). The final detector completed with two purposeful layout-transition warnings and four radius advisories; no UI changes followed. No browser/device preview was available. Engram mirror update remains pending because multiple active runtime sessions match the project/directory; this local document is authoritative. No commit/stage operation was attempted because Git metadata is outside the writable workspace.

## Relevant Files
- `templates/index.html` — responsive CSS, shell, tables, modal/planilla, interactions, and existing motion.
- `DESIGN.md` — current responsive, identity, and motion guidance.
- `tests/test_interaction_polish.py` — current hover, transitions, scroll and reduced-motion assertions.
- `tests/test_bolder_identity.py` — hierarchy, selected-week, and responsive table invariants.
- `tests/test_ui_copy.py` — current labels/accessibility names and UI text invariants.
- `tests/test_typography.py` — responsive text/layout and focus hierarchy assertions.
- `tests/test_color_system.py` — feedback/status contrast invariants.
- `odd/tasks/responsive-delight-motion.md` — feature task/proof record.
