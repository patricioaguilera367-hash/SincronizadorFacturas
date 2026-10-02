from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
SERVER = (ROOT / "servidor.py").read_text(encoding="utf-8")


class UiCopyTests(unittest.TestCase):
    def test_actions_describe_their_real_outcome(self):
        self.assertIn('placeholder="🔍 Buscar semanas"', HTML)
        self.assertIn('Crear próxima semana', HTML)
        self.assertIn('➕ Nueva carpeta', HTML)
        self.assertIn('Editar en planilla', HTML)
        self.assertIn('📋 Copiar', HTML)
        self.assertIn('Copia la tabla actual al portapapeles', HTML)
        self.assertIn('🚀 Sincronizar', HTML)
        self.assertNotIn('Exportar a Excel', HTML)

    def test_folder_and_ignored_copy_preserve_the_operational_concepts(self):
        self.assertIn("folderCell.dataset.label = 'Carpeta';", HTML)
        self.assertIn('Añadir código OT', HTML)
        self.assertIn('Las carpetas ignoradas no aparecen aquí', HTML)
        self.assertIn('Marcar como ignorada', HTML)
        self.assertIn('Quitar estado ignorado', HTML)
        self.assertIn("ignoreChip.textContent = '🚫 Ignorada';", HTML)
        self.assertIn('Eliminar la carpeta "${fact.nombre}" y todo su contenido? Esta acción no se puede deshacer.', HTML)

    def test_existing_icon_controls_have_clear_native_accessibility_names(self):
        self.assertIn('<button type="button" class="menu-icon" onclick="toggleSidebar()" aria-label="Mostrar u ocultar menú lateral" title="Mostrar u ocultar menú lateral">', HTML)
        self.assertIn('id="darkModeBtn" onclick="toggleDarkMode()" aria-label="Activar modo oscuro" title="Activar modo oscuro"', HTML)
        self.assertIn("const themeAction = isDark ? 'Activar modo claro' : 'Activar modo oscuro';", HTML)
        self.assertIn("setAttribute('aria-label', themeAction)", HTML)
        self.assertIn("setAttribute('title', themeAction)", HTML)
        self.assertIn('.menu-icon { cursor: pointer; display: flex; flex-direction: column; gap: 6px; padding: 10px; border: none; background: transparent; font: inherit;', HTML)

    def test_sync_labels_stay_coupled_to_existing_status_logic(self):
        self.assertIn('badge.textContent.includes("✓ Sincronizado")', HTML)
        self.assertIn("badge.textContent.includes('✓ Sincronizado')", HTML)
        self.assertIn('return "badge-success", "✓ Sincronizado"', SERVER)
        self.assertIn('Esta carpeta está ignorada para sincronización.', SERVER)
        self.assertIn("ignoreChip.textContent = '🚫 Ignorada';", HTML)
        self.assertIn('"⏳ Pendiente de sincronización"', SERVER)

    def test_sync_feedback_has_progress_timeout_and_backend_error_details(self):
        self.assertIn('AbortController', HTML)
        self.assertIn('fetchConTimeout', HTML)
        self.assertIn('90000', HTML)
        self.assertIn('Sincronizando ${exitos}/${ots.length} OT', HTML)
        self.assertIn('Sincronizado en ${duracionSegundos}s', HTML)
        self.assertIn("data.mensaje || (data.errores || []).join(' | ')", HTML)
        self.assertIn("setEstadoSyncOT(index, ot, 'error', detalle)", HTML)
        self.assertIn("errores.join(' | ')", HTML)

    def test_backend_errors_are_actionable_without_raw_exception_details(self):
        self.assertNotIn('str(e)', SERVER)
        self.assertIn('No se pudo completar la sincronización.', SERVER)
        self.assertIn('No se pudo copiar la carpeta de factura en la OT {ot}.', SERVER)


if __name__ == '__main__':
    unittest.main()
