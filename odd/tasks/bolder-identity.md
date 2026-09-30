# Bolder Application Identity

## Objective
Give the existing operations app a more distinctive, mature visual identity while preserving its established color, typography, workflow, and accessibility systems.

## Problem and Why
The product is an operational document desk, but repeated rounded white cards and quiet table structure understate its document-ledger character. The user asked for a stronger personality across navigation, headings, surfaces, controls, tables, and states while explicitly preserving the system already built.

## Scope
- `templates/index.html` — stronger visual amplification across navigation, masthead, metrics, table, controls, and states.
- `tests/test_bolder_identity.py` and/or the existing color-system tests — focused regression checks for the full hierarchy, theme contrast, and unchanged control/state semantics.
- `DESIGN.md` — record the reinforced visual motif without altering unrelated guidance.

## Design Direction
- The first attempt used only two 3 px rails and a heavier table-header weight; the user reported that it felt like only a 3% change. Reopen this task and make the hierarchy unmistakable without replacing the application’s identity.
- Direction: “ink-and-violet document desk.” Use a small set of broad, deliberate ink surfaces to frame weekly navigation, masthead, and the full table header; let existing violet carry selected week and primary action. The table should read as an operational ledger, not a collection of repeated cards.
- Add theme-aware semantic aliases `--desk-surface`, `--desk-text`, and `--desk-muted` that reuse current theme swatches; do not introduce new raw hues. Use them for dark ink surfaces and legible foregrounds.
- Make the selected week an unmistakable solid primary selection with on-primary text; preserve native button, `aria-pressed`, and current focus semantics.
- Quiet the repeated metrics-card treatment into a restrained secondary instrument strip. Keep ordinary data surfaces calm; strengthen the full table header and give rows a deliberate ledger rhythm.
- Reinforce existing textual status cues using only their existing semantic colors; do not make state meaning depend on color alone. Preserve action hierarchy and row-control affordances.
- No new fonts, radii, shadows, dependencies, copy, or behavior. Add only the justified semantic color aliases; reuse existing typography, palette, and interaction system.

## Constraints
- Preserve Operate-mode usability, Spanish UI copy, layout behavior, workflows, and all control semantics.
- No new dependencies, external imagery, network access, or remote font fetch.
- Strict TDD is enabled; exact runner: `python -m unittest discover -s tests -p "test_*.py"`.
- Impeccable setup already ran this session. Do not rerun context; read `craft-floor.md` immediately before UI edits.
- CodeGraph cannot safely index this workspace: Git root resolves to the user's home directory; use bounded local inspection, not the home-level index.
- Engram mirror saved as observation `#159` and read back.
- Git metadata is outside the writable root; do not stage or commit to the home-level repository.

## Authorized Scope
Implement the requested bolder pass across the named whole-app UI while preserving the shipped design system. Do not make a new visual-world proposal or change behavior/copy.

## Acceptance Criteria
- The first viewport visibly reads as a distinctive document-operations desk through broad ink/violet hierarchy, solid active navigation, and a complete ledger-style table header—not just thin accent rails.
- Navigation, masthead, metrics, table, controls, and states have purposeful visual roles without making every element loud.
- Existing light/dark contrast, active selection accessibility, status cues, and responsive behavior remain intact.
- New semantic aliases reuse the palette’s existing swatches; no new raw hue, font, radius, shadow, dependency, copy, or behavior is introduced.
- `DESIGN.md` and focused regression tests describe and protect the implemented treatment.

## Checks
- Read-only map: PRODUCT.md, DESIGN.md, template, color tests, and repository visuals reviewed by delegated explorer.
- Existing palette/type tokens and 3 px active-week selection rail provide the available motif; no formal logo or external brand assets exist.
- Corrective TDD: new assertions observed RED (3 failures and 2 missing-alias errors), then `python -m unittest discover -s tests -p "test_*.py"` passed with 21 tests. The suite passed again after the documentation correction.
- No committed screenshot, golden, or visual-regression fixture exists; no browser preview is available. Impeccable detector reported one unrelated layout-transition warning and three radius advisories.
- RDD is clone-local OFF; native assessment was high/unassessable because the external home-level Git enumerated 242,054 untracked entries above its deterministic limit. No review was attempted; delivery remains disabled/unmanaged.

## Tasks
- [ ] BOLD-001 — Amplify the existing ledger motif across the application's major headings and data table while preserving current controls and status roles.
  - Route: delegated direct. Trigger evidence: understanding touches 4+ files and the non-trivial UI, tests, and design-document changes require one writer.
  - TDD: enabled; exact runner: `python -m unittest discover -s tests -p "test_*.py"`; previous minimal pass was RED then GREEN (17 tests). Corrective pass must establish new RED before UI-source edits, then GREEN and REFACTOR.
  - Forecast: approximately 260 authored changed lines including tests/docs, generated files excluded.
  - Delivery strategy: `ask-on-risk` (default); forecast is below the approximately 400-line slice budget.
  - Progress: stronger ink-and-violet hierarchy and documentation correction complete; implementation and acceptance checks pass. Task closure remains pending only because workspace-scoped Git metadata is unavailable.
  - Verification evidence: new assertions observed RED; the full runner passed with 21 tests before and after the documentation correction. Independent verification confirmed light/dark contrast (desk text 11.15:1/17.06:1; muted 9.94:1/12.02:1), active selection/ARIA/focus/status semantics, table/metrics roles, mobile data-label orientation, and valid UTF-8 in `DESIGN.md` with no corrupted accents. Impeccable detector reported one unrelated layout-transition warning and three radius advisories. No browser render or committed visual fixture is available.
  - Commit evidence: not produced; Git metadata resolves outside the writable root to an external home-level repository. Do not stage or commit there.

## Next Step
No further UI changes remain. Close BOLD-001 with a work-unit commit only when Git metadata is workspace-scoped; do not alter the external home-level Git authority or repair the separate stale Impeccable sidecar as part of this task.

## Relevant Files
- `templates/index.html` — single-page UI and inline visual system.
- `tests/test_color_system.py` — light/dark palette and contrast regression tests.
- `DESIGN.md` — current Document Operations Desk visual guidance.
- `odd/tasks/bolder-identity.md` — ODD task and recovery record.
