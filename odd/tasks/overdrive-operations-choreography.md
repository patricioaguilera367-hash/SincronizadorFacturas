# Overdrive Operations Choreography

## Objective
Make week selection and invoice-folder disclosure feel unusually fluid through focused, native View Transitions and coordinated navigation motion, without changing the operational workflow or relying on the effect for state comprehension.

## Problem and Why
- The operations desk already has a dense week sidebar, active-week state, invoice rows, an accessible folder disclosure, and file details. The user's selected overdrive directions are (1) morphing folder/queue states and (3) coordinated navigation choreography.
- The existing system is an ink-and-violet operational desk, not a marketing surface. Extraordinary motion should communicate which week/folder became active and where its files appeared, while keeping the table readable and fast.
- Network loads are asynchronous. View Transition callbacks must only wrap synchronous DOM updates; they must never delay file/week fetches or make the transition API a dependency for state changes.

## Design Thesis
Let the navigation marker travel to the selected week, then let the selected invoice row resolve into its file detail. Keep shell and detail movement in one calm visual language; never animate the whole ledger at once.

## Scope
- `templates/index.html` — progressive-enhancement helper, selected-week transition, invoice-row/detail morph, coordinated motion and reduced-motion fallback.
- `tests/test_interaction_polish.py` — focused regression coverage for feature detection, state update fallback, reduced motion and transition naming/cleanup.
- `DESIGN.md` — document the deliberate motion pattern if it changes the current system guidance.
- `odd/tasks/overdrive-operations-choreography.md` — task/proof record.

## Direction
- Use the browser's same-document View Transition capability only when it exists and reduced motion is not requested; otherwise run the exact existing state update synchronously.
- Morph only the outgoing/incoming active week marker and the opened invoice folder into its file details. Keep sidebar collapse on its existing behavior; coordinate navigation and detail motions so they do not compete.
- Keep all network work outside the transition callback. Preserve one active transition name per state, clear dynamic names after completion, and retain current fetch/API behavior, focus, button semantics, `aria-pressed`, `aria-expanded`, and `aria-controls`.
- Don't add a dependency, new workflow, new backend behavior, loading delay, modal, or full-page transition. No spring/bounce, sound, decorative particles, or whole-table choreography.
- User owns all visual validation; after implementation, provide an enumerated interaction checklist with expected results. Do not open a browser or run visual review.

## Constraints
- Preserve Spanish copy, business/data semantics, filesystem behavior, API shape, and the app's responsive table/card behavior.
- Strict TDD is enabled. Exact test runner: `python -m unittest discover -s tests -p "test_*.py"`.
- The same-document View Transition API is an optional visual layer, not a state-management mechanism; follow the W3C specification's old/new capture model and fail open to the direct DOM update.
- CodeGraph initialization previously failed with `unsafe CodeGraph root`; use the completed delegated map and do not retry CodeGraph.
- Git metadata resolves outside the writable workspace. Do not stage/commit or mutate external Git metadata.
- Engram mirror writes have previously failed due to multiple active runtime sessions. Do not invent a session ID; preserve the local task file and report mirror pending if that recurs.
- User explicitly requests that they perform all visual validation; no browser/device claim may be made.

## Authorized Scope
Implement the user's selected direction 1 + 3 from Impeccable overdrive: morphing folder/queue states and coordinated navigation choreography. Add only necessary safeguards for correct transition lifecycle; no product redesign or unrelated fixes.

## Acceptance Criteria
- Selecting a different week gives an immediate, legible active-marker transition; the selected week and data update are correct even if the API or View Transition API is unavailable.
- Opening and closing an invoice's file details visually connects the row to its detail without moving or animating the entire ledger; focus and disclosure ARIA remain correct.
- Existing sidebar collapse remains usable and its motion does not compete with row-detail morphing.
- Async fetches are never awaited inside the transition callback; dynamic names are unique and cleaned up; rapid interactions still leave canonical DOM/ARIA state intact.
- `prefers-reduced-motion` and unsupported browsers use the direct, non-animated existing state updates.
- Exact unit suite passes and JavaScript syntax/build check (if the existing environment provides one) reports no error. No visual review is run; user performs the manual checks listed in the final response.

## Checks
- Impeccable `overdrive` playbook requires proposing directions before code; user selected directions 1 and 3. The other directions were not accepted and are out of scope.
- Context loaded directly from `PRODUCT.md` and `DESIGN.md`: Spanish Windows-network operations desk, invoice folders, OTs, files, and synchronization; retain existing function, high-density layout, and no dependencies.
- Delegated map covered the week selection, sidebar, folder disclosure and details flow in `templates/index.html`, plus relevant motion/ARIA tests and design notes. It identified async response races; avoid adding transition-induced race risk and keep network work outside synchronous callbacks.
- Primary technical reference: W3C CSS View Transitions Module Level 1, https://www.w3.org/TR/css-view-transitions-1/.
- TDD: strict; exact runner `python -m unittest discover -s tests -p "test_*.py"`. JavaScript syntax command to be resolved by the writer from installed tooling.
- Forecast: approximately 180 authored changed lines, below the 400-line budget; default delivery strategy `ask-on-risk`.
- The user explicitly owns all review/visual validation; no RDD status/risk assessment or review workflow was run. No RDD review was started.
- Verification evidence: strict TDD RED observed before editing `templates/index.html` (43 tests, 4 new focused failures). Two interim post-source runs exposed test-only matcher/expected-direction mismatches (3 failures, then 1); the assertions were corrected to the intended source semantics. Final exact suite is GREEN (43 tests, OK). Node v24 syntax check of the extracted inline script passed. No browser, screenshots, visual review, detector, or separate verifier was run per user instruction; task boxes remain open pending user visual validation.

## Tasks
- [ ] NAV-MORPH-001 — Morph active-week selection and coordinate existing sidebar navigation motion with View Transitions, with direct fallback.
  - Route: delegated direct; writer trigger evidence: analysis-driven change touches the inline template, motion regression tests and design guidance (3 non-trivial files); reading that prepares the write stays with the writer.
  - TDD/evidence: active-week marker assertion included in RED (43 tests, 4 failures) before template edits; final exact suite 43 tests, OK. `selected-week` morphs only the active button; root crossfade is disabled, sidebar collapse keeps its existing CSS transition, and a revision/skip guard keeps rapid selections canonical. Week fetch remains outside the synchronous update callback.
- [ ] DETAIL-MORPH-001 — Transition an invoice-folder disclosure into its file details without delaying fetches or compromising keyboard/reduced-motion behavior.
  - Route: delegated direct single writer; related flow and motion share the same template/state lifecycle.
  - TDD/evidence: fallback, reduced-motion, interruptibility, unique-name transfer, synchronous disclosure, and documentation assertions included in RED before template edits; final exact suite 43 tests, OK. `folder-detail` transfers from disclosure to detail (and back), names/classes clean on completion or fallback, existing detail entry animation is suppressed only during the shared transition path, and file fetching remains outside the callback.
- Delivery forecast: ~180 authored changed lines across two coordinated tasks; no PR-chain decision expected.

## Next Step
Automated suite and inline JavaScript syntax check passed. User-owned visual validation remains pending; the final response provides numbered interactions and expected results. Do not run a browser preview, visual QA, detector, or independent reviewer. Close task checkboxes only after the user reports their visual acceptance. Engram save was attempted after creation and implementation but refused because multiple active runtime sessions match; mirror remains pending and this local task file is authoritative.

## Relevant Files
- `templates/index.html` — single-template application, week navigation, table, invoice-folder disclosure, file detail, inline CSS and browser behavior.
- `tests/test_interaction_polish.py` — motion, focus, responsive, and disclosure assertions.
- `tests/test_bolder_identity.py` — active-week visual/semantic invariants.
- `DESIGN.md` — current ink-and-violet operations-desk and motion guidance.
- `odd/tasks/overdrive-operations-choreography.md` — feature task and proof record.
