from pathlib import Path
import re
import unittest


HTML = Path(__file__).parents[1] / "templates" / "index.html"
DESIGN = Path(__file__).parents[1] / "DESIGN.md"


class InteractionPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")

    @classmethod
    def declarations(cls, selector):
        match = re.search(rf"(?m)^\s*{re.escape(selector)}\s*\{{([^}}]*)\}}", cls.source)
        if not match:
            raise AssertionError(f"Missing CSS rule: {selector}")
        return dict((name, value.strip()) for name, value in re.findall(r"([\w-]+)\s*:\s*([^;]+)", match.group(1)))

    def assert_source_contains(self, text):
        self.assertTrue(text in self.source, f"Missing source marker: {text}")

    def assert_source_not_contains(self, text):
        self.assertTrue(text not in self.source, f"Unexpected source marker: {text}")

    def test_week_hover_belongs_only_to_the_native_button(self):
        self.assertNotIn('li.className = "week-item"', self.source)
        self.assertIn("button.type = 'button';", self.source)
        self.assertIn("button.className = 'week-item';", self.source)
        self.assertIn("button.setAttribute('aria-pressed', 'false');", self.source)
        self.assertIn('.week-item:hover', self.source)
        self.assertIn('elementoLista.setAttribute("aria-pressed", "true")', self.source)

    def test_scroll_owners_share_a_tokenized_native_scrollbar(self):
        owners = self.declarations('body, .week-list, .main-content, .modal-body')
        self.assertEqual(owners.get('scrollbar-width'), 'thin')
        self.assertEqual(owners.get('scrollbar-color'), 'var(--border) transparent')
        for selector in (
            'body::-webkit-scrollbar, .week-list::-webkit-scrollbar, .main-content::-webkit-scrollbar, .modal-body::-webkit-scrollbar',
            'body::-webkit-scrollbar-thumb, .week-list::-webkit-scrollbar-thumb, .main-content::-webkit-scrollbar-thumb, .modal-body::-webkit-scrollbar-thumb',
            'body::-webkit-scrollbar-thumb:hover, .week-list::-webkit-scrollbar-thumb:hover, .main-content::-webkit-scrollbar-thumb:hover, .modal-body::-webkit-scrollbar-thumb:hover',
        ):
            self.assertIn(selector, self.source)
        self.assertIn('background: var(--text-muted)', self.source)
        self.assertIn('@media (forced-colors: active)', self.source)
        self.assertIn('scrollbar-color: auto', self.source)

    def test_theme_transitions_are_explicit_fast_and_keep_collapse_motion(self):
        for selector in ('body', '.search-box', '.week-item', '.header-card', '.table-container'):
            transition = self.declarations(selector).get('transition', '')
            self.assertIn('background-color', transition, selector)
            self.assertNotIn('all', transition, selector)
            self.assertNotIn('box-shadow', transition, selector)
            self.assertRegex(transition, r'0\.1[678]s')
        sidebar = self.declarations('.sidebar').get('transition', '')
        self.assertIn('width 0.35s ease', sidebar)
        self.assertIn('background-color', sidebar)
        self.assertIn('transition: max-height 0.35s ease, margin 0.35s ease', self.source)

    def test_reduced_motion_removes_nonessential_animation_without_hiding_state(self):
        reduced_motion = re.search(r'@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\n\s*\}', self.source, re.S)
        self.assertIsNotNone(reduced_motion)
        self.assertIn('animation-duration: 0.01ms', reduced_motion.group(1))
        self.assertIn('transition-duration: 0.01ms', reduced_motion.group(1))
        self.assertIn(':focus-visible', self.source)

    def test_design_documents_scrollbar_and_motion_conventions(self):
        design = DESIGN.read_text(encoding="utf-8").lower()
        self.assertIn('scrollbar', design)
        self.assertIn('prefers-reduced-motion', design)

    def test_tablet_layout_uses_labeled_rows_and_keeps_actions_in_flow(self):
        self.assert_source_contains('@media (max-width: 900px)')
        compact = self.source.split('@media (max-width: 900px)', 1)[1].split('\n        }', 1)[0]
        self.assertIn('body { display: block;', compact)
        self.assertIn('.table-container tbody > tr:not(.archivos-row) > td::before', compact)
        self.assertIn('content: attr(data-label)', compact)
        self.assertEqual(self.source.count("matchMedia('(max-width: 900px)')"), 2, 'Both responsive display switches must match the card breakpoint')

    def test_notebook_table_scroll_is_contained_and_wide_working_measure_is_capped(self):
        self.assert_source_contains('@media (min-width: 901px) and (max-width: 1080px)')
        compact_table = self.source.split('@media (min-width: 901px) and (max-width: 1080px)', 1)[1].split('\n        }', 1)[0]
        self.assertIn('overflow-x: auto', compact_table)
        self.assertIn('min-width: 760px', compact_table)
        self.assertIn('overscroll-behavior-inline: contain', compact_table)
        self.assert_source_contains('max-width: 1840px')
        self.assert_source_contains('margin-inline: auto')
        self.assert_source_contains('min-width: 0')

    def test_coarse_pointer_targets_and_press_feedback_are_not_hover_only(self):
        self.assert_source_contains('@media (pointer: coarse)')
        coarse = self.source.split('@media (pointer: coarse)', 1)[1].split('\n        }', 1)[0]
        self.assertIn('min-height: 44px', coarse)
        self.assertIn('min-width: 44px', coarse)
        self.assert_source_contains('button:active:not(:disabled)')
        self.assert_source_contains('.week-item:active')
        self.assert_source_not_contains('transform: scale(')

    def test_motion_is_state_specific_brief_and_keeps_sidebar_collapse(self):
        arrival = re.search(r'@keyframes surface-arrive\s*\{(.*?)\n\s*\}', self.source, re.S)
        self.assertIsNotNone(arrival)
        self.assertNotIn('scale(', arrival.group(1))
        self.assertIn('translateY(', arrival.group(1))
        self.assert_source_contains('animation: surface-arrive 0.2s')
        self.assert_source_contains('animation: scrim-enter 0.16s')
        self.assert_source_not_contains('transition: 0.5s')
        sidebar = self.declarations('.sidebar').get('transition', '')
        self.assertIn('width 0.35s ease', sidebar)
        self.assertIn('transition: max-height 0.35s ease, margin 0.35s ease', self.source)

    def test_copy_drop_empty_and_paste_feedback_reflect_real_states(self):
        for marker in (
            '.btn-outline.copy-confirmed',
            "btn.classList.add('copy-confirmed')",
            "btn.classList.remove('copy-confirmed')",
            '.drop-zone.uploaded',
            "classList.add('uploaded')",
            "classList.remove('uploaded')",
            '.file-list.empty',
            "fileList.classList.add('empty')",
            'fileList.classList.remove("empty")',
            '.tags-container.paste-highlight',
            '.spreadsheet-input.paste-highlight',
        ):
            self.assert_source_contains(marker)

    def test_existing_upload_has_a_native_picker_using_the_same_handler(self):
        self.assert_source_contains("picker.type = 'file';")
        self.assert_source_contains("picker.className = 'file-picker';")
        self.assert_source_contains("picker.id = `file_picker_${index}`;")
        self.assert_source_contains("picker.setAttribute('aria-label', 'Seleccionar archivo para subir');")
        self.assert_source_contains("picker.addEventListener('change', event => handleDrop(event, index, fact.ruta));")
        self.assert_source_contains('const files = e.dataTransfer ? e.dataTransfer.files : e.target.files;')
        self.assert_source_contains('if (e.target.type === "file") e.target.value = "";')

    def test_folder_expander_is_a_button_with_synchronized_aria_state(self):
        self.assert_source_contains("expander.type = 'button';")
        self.assert_source_contains("expander.className = 'folder-name';")
        self.assert_source_contains("expander.id = `folder_expander_${index}`;")
        self.assert_source_contains("expander.setAttribute('aria-controls', `archivos_row_${index}`);")
        self.assert_source_contains('expander.setAttribute("aria-expanded", "false")')
        self.assert_source_contains('expander.setAttribute("aria-expanded", "true")')
        self.assert_source_contains("document.querySelectorAll('.folder-name[aria-expanded=\"true\"]')")

    def test_design_documents_the_semantic_sidebar_button(self):
        design = DESIGN.read_text(encoding="utf-8")
        self.assertIn('`button.menu-icon`', design)
        self.assertNotIn('no es un botón semántico', design)


    def test_week_selection_uses_a_unique_shared_marker(self):
        self.assert_source_contains('.week-item.active { view-transition-name: selected-week; }')
        self.assert_source_contains('updateWithViewTransition(() => {')
        self.assert_source_contains("elementoLista.classList.add('active')")

    def test_view_transition_is_optional_reduced_and_interruptible(self):
        self.assert_source_contains('typeof document.startViewTransition === "function"')
        self.assert_source_contains('window.matchMedia("(prefers-reduced-motion: reduce)").matches')
        self.assert_source_contains('pendingTransition.skipTransition()')
        self.assert_source_contains('revision !== viewTransitionRevision')
        self.assert_source_contains('transition.finished.then(finish, finish)')
        self.assert_source_contains('source.style.viewTransitionName = ""')
        self.assert_source_contains('target.style.viewTransitionName = options.name')

    def test_folder_detail_name_moves_with_sync_dom_only_disclosure(self):
        self.assert_source_contains('name: "folder-detail"')
        self.assert_source_contains('source: opening ? expander : row')
        self.assert_source_contains('target: opening ? row : expander')
        self.assert_source_contains('suppressEntry: opening ? row : null')
        toggle = self.source.split('function toggleArchivos(index, ruta) {', 1)[1].split('async function cargarListaArchivos', 1)[0]
        self.assertNotIn('await ', toggle)
        self.assertLess(toggle.index('updateWithViewTransition'), toggle.index('cargarListaArchivos(index, ruta)'))
        self.assert_source_contains('.archivos-row.view-transition-active .archivos-container { animation: none; }')
        self.assert_source_contains('suppressEntry.classList.add("view-transition-active")')

    def test_view_transition_limits_choreography_to_named_elements_and_documents_it(self):
        self.assert_source_contains('::view-transition-old(root), ::view-transition-new(root) { animation: none; }')
        self.assert_source_contains('::view-transition-group(selected-week), ::view-transition-group(folder-detail)')
        design = DESIGN.read_text(encoding="utf-8")
        self.assertIn('`selected-week`', design)
        self.assertIn('`folder-detail`', design)
        self.assertIn('barra lateral conserva su transici\u00f3n independiente', design)

    def test_desktop_sidebar_collapse_transitions_its_grid_track(self):
        self.assertIn('grid-template-columns 0.35s ease', self.declarations('body').get('transition', ''))
        collapsed = self.declarations('body:has(.sidebar.collapsed)')
        self.assertEqual(collapsed.get('grid-template-columns'), '0 minmax(0, 1fr)')
        self.assert_source_contains('transition: max-height 0.35s ease, margin 0.35s ease')


if __name__ == '__main__':
    unittest.main()
