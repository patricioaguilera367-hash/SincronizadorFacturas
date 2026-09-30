# UI Interaction Polish

## Objective
Correct the week-navigation hover layers, give the existing scroll areas a restrained theme-aware scrollbar treatment, and make light/dark changes feel smooth without transition jank.

## Problem and Why
- The week list creates a `<li class="week-item">` around a `<button class="week-item">`. Both receive the same hover rule, so the outer row animates a pale surface while the selected button keeps a light label; overlapping states make the text hard to read.
- The desktop/modal scroll owners (`.week-list`, `.main-content`, `.modal-body`) use browser-default scrollbars; at mobile widths `body` becomes the page scroll owner too. The design has no authored thumb/track feedback for those owners.
- Theme toggling only changes `body.dark-mode` and localStorage, but many surfaces and controls use duration-only `transition` shorthands at 300–400 ms. Those shorthands mean `all`; color/background/border and large shadow changes animate broadly and plausibly cause the perceived lag. Geometry should remain separate for sidebar collapse.

## Scope
- `templates/index.html` — correct the single week hover target, theme-aware scrollbars, and bounded theme transitions/reduced-motion behavior.
- `tests/test_interaction_polish.py` or existing focused UI/color tests — protect hover ownership, scrollbar roles, theme transition scope, reduced-motion, and accessibility semantics.
- `DESIGN.md` — describe the scrollbar and motion conventions in the existing visual system.

## Design Direction
- Keep `.week-item` exclusively on the inner native button; the list wrapper remains structurally neutral, removing the duplicate hover surface rather than adding more rules.
- Use native CSS scrollbars on all owners, including mobile `body`: thin, visible, transparent track, theme-token thumb, a quiet hover state; include WebKit fallback, forced-colors fallback, and do not hide scrollbars or rely on hover for discoverability. Desktop `body` is overflow-hidden, so styling it is inactive there. Add no scrollbar library.
- Limit theme transitions to explicit color/background/border properties with a short, calm duration (~160–180 ms); do not animate large shadows or unrelated properties. Preserve separate sidebar collapse/reflow transitions.
- Add a `prefers-reduced-motion` path that shortens or removes nonessential movement while keeping state changes and focus feedback visible.
- Reuse existing theme tokens, status semantics, controls, and Spanish UI copy; add no new hues, dependencies, or unnecessary primitives.

## Constraints
- Preserve the document operations workflow, Spanish UI copy, keyboard/focus behavior, button semantics, and `aria-pressed` updates.
- No remote access, external assets, package installation, or added scrollbar/animation dependency.
- Strict TDD is enabled; exact runner: `python -m unittest discover -s tests -p "test_*.py"`.
- CodeGraph cannot query this workspace because no `.codegraph/` index exists and Git root resolves to an external home directory; do not call CodeGraph again or inspect/change home Git metadata.
- Git metadata is outside the writable root; do not stage or commit there.
- Engram mirror is pending: save was rejected because multiple active runtime sessions matched this project; keep the local tracker and do not invent/borrow a session ID.

## Authorized Scope
Fix the described week hover contrast defect, style the existing scrollbars, and make theme switching smooth and accessible. User explicitly delegated the visual decisions; do not ask a follow-up.

## Acceptance Criteria
- Exactly one element per week receives `.week-item` hover and active styles; hover never washes out the selected label.
- Every actual scroll owner uses a slim, quiet, theme-aware scrollbar in current browsers, including `body` at the mobile breakpoint, with a visible fallback and no lost forced-colors/touch discoverability.
- Theme changes use short explicit color transitions, avoid broad `all`/shadow work, preserve collapse behavior, and respect `prefers-reduced-motion`.
- Existing active selection, text/status semantics, controls, focus indicators, dark/light contrast, and mobile behavior remain intact.
- Regression tests prove the three requirements; `DESIGN.md` matches implementation.

## Checks
- Read-only map reviewed `templates/index.html`, `tests/test_color_system.py`, and `tests/test_bolder_identity.py`.
- Evidence: duplicate wrapper/button class at `templates/index.html:447–457`; desktop/modal scroll owners `.week-list`, `.main-content`, `.modal-body`; mobile `body` becomes the scroll owner at `max-width:720px`; theme click toggles a body class and stores preference, while CSS uses 300–400 ms duration-only shorthands; no reduced-motion rule exists.
- Previous project suite passed 21 tests before this task; new tests must observe RED before UI-source edits, then GREEN and REFACTOR.
- Implementation evidence: the week wrapper no longer duplicates `.week-item`; tokenized thin scrollbars cover all four owners including mobile `body`, with WebKit and forced-colors fallbacks; theme colors use short explicit transitions and reduced-motion support while collapse geometry remains separate.
- TDD evidence: assertions-first run observed RED; after implementation and the mobile-owner correction, independent full suite `python -m unittest discover -s tests -p "test_*.py"` passed: 26 tests, OK. A bounded independent source/doc/test readback passed. Browser preview was unavailable and not run.
- RDD is clone-local OFF; recent native assessment was high/unassessable due the external home-level Git's excessive untracked files. No review lifecycle is authorized/needed.

## Tasks
- [ ] INT-001 — Fix duplicate week hover ownership and add the restrained custom scrollbar treatment. Implementation and tests complete; required work-unit commit unavailable because Git metadata is outside the writable workspace.
  - Route: delegated direct. Trigger evidence: exact cause traced in DOM/CSS/JS and implementation spans template, tests, and design guidance.
  - TDD: enabled; run the full test runner after assertions-first and observe RED before UI edits.
  - Forecast: approximately 180 authored changed lines across both tasks, generated files excluded.
  - Progress: duplicate hover fixed and themed scrollbars cover desktop, modal, and mobile page scroll owners; regression coverage and independent verification pass.
  - Commit evidence: unavailable until Git metadata is workspace-scoped; do not write to the external home-level repository.
- [ ] INT-002 — Smooth theme transitions without animating broad/shadow properties; support reduced motion. Implementation and tests complete; required work-unit commit unavailable because Git metadata is outside the writable workspace.
  - Route: delegated direct; same writer owns the single-page CSS and regression updates.
  - TDD: enabled; include tests for explicit transition properties, reduced-motion, and preserved collapse transitions.
  - Progress: implementation and independent verification passed for explicit color-only transitions, sidebar collapse, and reduced motion.
  - Commit evidence: unavailable until Git metadata is workspace-scoped; do not write to the external home-level repository.

## Next Step
Implementation, docs, regression checks, and independent verification are complete. The remaining process items are the work-unit commit and Engram mirror; neither can be completed safely while Git metadata is outside the writable workspace and Engram cannot resolve a unique active runtime session.

## Relevant Files
- `templates/index.html` — week list DOM, inline CSS, and theme toggle.
- `tests/test_color_system.py` — color semantics and theme contrasts.
- `tests/test_bolder_identity.py` — selection and accessibility regression assertions.
- `DESIGN.md` — visual-system guidance.
- `odd/tasks/ui-interaction-polish.md` — task/proof record.
