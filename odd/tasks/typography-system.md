# Typography System

## Objective
Establish a clear, consistent typography hierarchy across the existing Spanish operations interface without changing its product identity or workflows.

## Problem and Why
`templates/index.html` mixed many literal sizes, had no global line-height, and contained duplicate cascade overrides. The initial Impeccable type detector reported 12 font-size advisories and four skipped-heading warnings. The established product identity uses Poppins; the redesign preserves that single family.

## Scope
- `templates/index.html` — semantic type roles, scale, weights, leading, contrast, and responsive behavior across headings, navigation, tables, forms, metadata, states, and actions.
- `DESIGN.md` — document the resulting type roles and scale.
- `tests/test_typography.py` — focused standard-library regression checks for semantic roles, heading order, and status-text contrast.

## Constraints
- Preserve Poppins, existing workflow, Spanish UI copy, layout, and controls.
- No new dependencies or font families.
- Strict TDD is enabled; Python's standard-library `unittest` is the authorized runner.
- Engram mirror is pending because memory writes report multiple active runtime sessions; no session ID is available to use.
- Git metadata resolves to `C:\Users\Supervisor`, outside the writable project root. Do not stage or commit against that home-level repository.
- Do not fetch remote fonts or access UNC paths for preview.

## Authorized Scope
Implement the requested typography redesign in this project workspace only. Do not run the operational app against network shares.

## Acceptance Criteria
- One-family Poppins hierarchy distinguishes page/section headings, body/data, labels, navigation, metadata, status, and actions.
- Repeated roles use a small semantic scale with explicit weight and line-height; contrast and dense table/form reading remain usable.
- Heading levels are semantically ordered without changing visible copy or behavior.
- `DESIGN.md` records the implemented type system; final Impeccable type scan has no findings.
- Automated TDD/source checks pass.
- Rendered long-Spanish-text, narrow-width, and browser-zoom usability is not verified; a rendered preview was not performed because the font is externally hosted and no offline fixture exists.

## Checks
- Initial type assessment: Poppins is the established family; no semantic scale/global line-height; no test runner/config found.
- Initial Impeccable type detector: 12 font-size advisories and four skipped-heading warnings.
- Strict TDD runner: `python -m unittest discover -s tests -p "test_*.py"`; RED observed before implementation and before final correction; final suite passed (4 tests).
- Final Impeccable detector: `impeccable.cmd detect --json --scope type templates/index.html` returned `[]`.
- An independent confirmation found ignored-status contrast below 4.5:1 (3.822 light, 4.038 dark) and a stale muted-color token in DESIGN.md. The final correction added theme-aware status foreground, a contrast regression assertion, and synchronized the documented token. The final unit suite and detector then passed.
- Browser/runtime visual inspection: not performed; loading the remote Google Font was not authorized and no static offline fixture exists.
- Review mode reported off but failed unsafe home-level Git-authority validation; risk assessment was unavailable. No native review lifecycle started.
- Work-unit commit: unavailable because the Git metadata is outside the authorized writable root.

## Tasks
- [ ] TYP-001 — Implement and verify the application-wide typography system in `templates/index.html` and `DESIGN.md`.
  - Route: delegated direct. Trigger evidence: the typeset skill required assessment/detection; preparation for edits and two non-trivial files required a delegated writer.
  - TDD: enabled by session instructions; exact runner: `python -m unittest discover -s tests -p "test_*.py"`.
  - Forecast: approximately 210 authored changed lines, generated files excluded.
  - Delivery strategy: `ask-on-risk` (default); forecast below the approximately 400-line slice budget.
  - Progress: implementation and contrast correction are complete. Four unit tests pass and the final typography detector is clean. The browser-preview criterion remains unverified; the task remains open until rendered reflow/zoom is inspected in an authorized local environment.
  - Commit evidence: none; Git metadata is outside the writable root.

## Next Step
If rendered evidence is required, inspect the local page with a preview that does not fetch external resources, or obtain authorization for the Google Fonts fetch. No further code change is currently indicated.

## Relevant Files
- `templates/index.html` — single-page UI, inline styles, typography system, and browser behavior.
- `tests/test_typography.py` — focused typography regression checks.
- `DESIGN.md` — product design guidance and documented typography tokens.
