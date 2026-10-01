# Install montos-facturas

## Objective
Install the supplied invoice-amount feature package from `patch/` into the existing application on `feature/montos-facturas`.

## Problem and why
The repository has a prepared package and installation guide, but the feature is not integrated into the current app. The user requested installation and explicitly asked that verification be left to them.

## Scope
- Back up the current weekly template before replacing it.
- Copy the two Python package files, replacement template, and focused test file from `patch/`.
- Add only the backup ignore patterns required by the guide.
- Run the package installer once to modify the existing `servidor.py` in place.
- Preserve the untracked `SincronizadorWeb_Montos.zip` and `patch/` inputs.

## Constraints
- Do not run tests, compilation, diff inspection, or manual/UI verification; the user will verify.
- The README says not to commit before user verification; the user subsequently confirmed “Está correcto” and explicitly requested a V1.1 commit.
- Do not install PyMuPDF from a package index without explicit remote-transfer authorization. The guide says the feature retains manual amount entry if PyMuPDF is unavailable.
- Strict TDD is enabled in the session instructions, but the user explicitly prohibited automated verification for the installation; record checks as skipped and do not claim test-first evidence.
- Keep scope limited to the package instructions; do not replace the user's backend wholesale.

## Authorized scope
`patch/factura_montos.py`, `patch/instalar_montos.py`, `patch/templates/index.html`, `patch/tests/test_factura_montos.py`, plus root `factura_montos.py`, `instalar_montos.py`, `templates/index.html`, `tests/test_factura_montos.py`, `servidor.py`, `.gitignore`, and the HTML backup named in the README.

## Acceptance criteria
- The installer reports successful integration without replacing the backend.
- The four supplied files are installed at their documented destinations; the prior template and backend installer backup are preserved.
- The README's two backup ignore patterns are present exactly once.
- User-provided ZIP and `patch/` directory remain untouched.
- A Conventional Commit records the installation, with a `v1.1` release tag.
- Automated checks remain skipped per user instruction.

## Checks and mode
- TDD mode: enabled by session instruction; the user explicitly requested no verification for this installation.
- Test runner documented by README: `python -m unittest discover -s tests -p "test_factura_montos.py"` (not run).
- Compile command documented by README: `python -m py_compile .\servidor.py .\factura_montos.py` (not run).
- Functional/UI verification: not run; user will perform it.

## Delivery
- Route: delegated direct.
- Trigger evidence: installation reads span 4+ files and modifies several non-trivial files; exploration and implementation must be delegated.
- Forecast: over 400 authored changed lines, principally from the new module, test, template replacement, and server integration.
- Release strategy: keep a linear version history with annotated tags (`v1.0`, `v1.1`, …) so rollback can target the previous release tag.
- PR chaining: not applicable to the requested local commit/tag; no PR is being created.

## Tasks
- [x] T1 (delegated): Installed the prepared feature package, preserved backups and input artifacts, and ran the installer once without separate checks.
- [x] T2 (inline): Created work-unit commit `7ffaa5d960908886b9240b79c9a4988033a6e9dd` and annotated release tag `v1.1`.

## Progress and next step
T1 completed per the delegated install report: four package files copied; `.gitignore` patterns added; `python .\instalar_montos.py` exited 0 and created `servidor.antes_montos.20260930_171849.bak`; the weekly template backup is `templates/index.html.antes_montos.bak`. PyMuPDF was not installed; its package-index transfer was not authorized, and the guide says manual amount entry remains available. The user confirmed “Está correcto” and clarified that the priority is simple rollback to the prior version and sequential version tags. Commit `7ffaa5d960908886b9240b79c9a4988033a6e9dd` (`feat(montos): add invoice amount summary`) is tagged `v1.1`; `v1.0` remains on prior release commit `14c80c5f5a5ea96a32b697f5625fe0c3c5ba5a86` as rollback point. No tests or compilation were run, per the user's instruction. No PR was created. If a regression appears, the previous release point is `v1.0`.
