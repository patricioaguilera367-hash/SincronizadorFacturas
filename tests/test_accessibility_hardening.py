from pathlib import Path
import unittest


HTML = Path(__file__).parents[1] / "templates" / "index.html"


class AccessibilityHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")

    def body(self, start, end):
        return self.source.split(start, 1)[1].split(end, 1)[0]

    def test_planilla_dialog_has_keyboard_lifecycle_and_focus_return(self):
        modal = self.source.split('id="modalPlanilla"', 1)[1].split('<script>', 1)[0]
        open_dialog = self.body('function abrirModoPlanilla()', 'function crearCeldaPlanilla')
        close_dialog = self.body('function cerrarModalPlanilla()', 'function guardarPlanilla')

        self.assertIn('role="dialog"', modal)
        self.assertIn('aria-modal="true"', modal)
        self.assertIn('aria-labelledby="tituloPlanilla"', modal)
        self.assertIn('let ultimoFocoPlanilla = null;', self.source)
        self.assertIn('ultimoFocoPlanilla = document.activeElement;', open_dialog)
        self.assertIn("document.getElementById('cerrarPlanilla').focus();", open_dialog)
        self.assertIn("event.key === 'Escape'", self.source)
        self.assertIn('ultimoFocoPlanilla.focus();', close_dialog)
        self.assertIn("event.key === 'Tab'", self.source)

    def test_tag_removal_is_a_labeled_native_button(self):
        tags = self.body('function renderTags(index)', 'function removeTag')
        self.assertIn("document.createElement('button')", tags)
        self.assertIn("tagClose.type = 'button';", tags)
        self.assertIn("tagClose.setAttribute('aria-label'", tags)
        self.assertIn("tagClose.addEventListener('click'", tags)
        self.assertIn('.tag-close {', self.source)
        self.assertIn('font: inherit', self.source)

    def test_long_content_wraps_without_hiding_actions_or_table_access(self):
        for marker in (
            'min-width: 0; overflow-x: auto; overscroll-behavior-inline: contain;',
            '.folder-name, .status-badge, .modal-header h2, .modal-footer > span { overflow-wrap: anywhere; }',
            '.folder-wrapper, .folder-name, .sync-cell, .acciones-flex { min-width: 0; }',
            '.acciones-flex { display: flex; gap: 8px; flex-wrap: wrap; }',
            '.tag-input, .spreadsheet-input { min-width: 0; max-width: 100%; }',
        ):
            self.assertIn(marker, self.source)


if __name__ == "__main__":
    unittest.main()
