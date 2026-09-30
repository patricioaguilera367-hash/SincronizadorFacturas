from pathlib import Path
import re
import unittest


HTML = Path(__file__).parents[1] / "templates" / "index.html"


class ColorSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")

    @classmethod
    def declarations(cls, selector):
        match = re.search(rf"(?m)^\s*{re.escape(selector)}\s*\{{([^}}]*)\}}", cls.source)
        if not match:
            raise AssertionError(f"Missing CSS rule: {selector}")
        return dict(re.findall(r"([\w-]+)\s*:\s*([^;]+)", match.group(1)))

    @classmethod
    def palette(cls, selector):
        return {
            name: value.strip()
            for name, value in cls.declarations(selector).items()
            if name.startswith("--")
        }

    @staticmethod
    def rgb(value):
        value = value.lstrip("#")
        return tuple(int(value[index : index + 2], 16) / 255 for index in (0, 2, 4))

    @staticmethod
    def linear(channel):
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    @classmethod
    def luminance(cls, color):
        red, green, blue = (cls.linear(channel) for channel in color)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    @classmethod
    def contrast(cls, foreground, background):
        high, low = sorted((cls.luminance(foreground), cls.luminance(background)), reverse=True)
        return (high + 0.05) / (low + 0.05)

    def assert_role_contrast(self, palettes, pairs, minimum):
        for theme, palette in palettes:
            for foreground, background in pairs:
                with self.subTest(theme=theme, foreground=foreground, background=background):
                    self.assertGreaterEqual(
                        self.contrast(self.rgb(palette[foreground]), self.rgb(palette[background])),
                        minimum,
                    )

    def test_palette_declares_semantic_roles_for_both_themes(self):
        light = self.palette(":root")
        dark = self.palette("body.dark-mode")
        required = {
            "--primary", "--primary-hover", "--primary-subtle", "--on-primary", "--focus-ring",
            "--selection-surface", "--text-main", "--text-muted", "--bg-body", "--bg-surface",
            "--border", "--success", "--warning", "--danger", "--status-success-text",
            "--status-success-bg", "--status-warning-text", "--status-warning-bg",
            "--status-danger-text", "--status-danger-bg", "--status-loading-text",
            "--status-loading-bg", "--status-ignored-text", "--status-ignored-bg",
            "--status-sent-text", "--status-sent-bg",
        }
        self.assertTrue(required.issubset(light))
        self.assertTrue(required.intersection(dark))
        self.assertNotIn("linear-gradient", self.source.lower())

    def test_desk_aliases_reuse_palette_swatches_with_aa_contrast(self):
        light = self.palette(":root")
        dark = {**light, **self.palette("body.dark-mode")}

        def resolve(palette, role):
            value = palette[role]
            while value.startswith("var("):
                value = palette[value[4:-1]]
            return value

        for theme, palette in (("light", light), ("dark", dark)):
            with self.subTest(theme=theme):
                for role in ("--desk-surface", "--desk-text", "--desk-muted"):
                    self.assertTrue(palette[role].startswith("var("))
                self.assertGreaterEqual(
                    self.contrast(self.rgb(resolve(palette, "--desk-text")), self.rgb(resolve(palette, "--desk-surface"))),
                    4.5,
                )
                self.assertGreaterEqual(
                    self.contrast(self.rgb(resolve(palette, "--desk-muted")), self.rgb(resolve(palette, "--desk-surface"))),
                    4.5,
                )

    def test_primary_action_is_solid_and_roles_match_the_state(self):
        master = self.declarations(".btn-master")
        self.assertEqual(master.get("background"), "var(--primary)")
        self.assertEqual(master.get("color"), "var(--on-primary)")
        self.assertEqual(self.declarations(".btn-add-week").get("background"), "var(--primary-subtle)")
        self.assertEqual(self.declarations(".btn-delete:hover").get("background"), "var(--status-danger-bg)")
        self.assertEqual(self.declarations(".status-pendiente").get("color"), "var(--status-warning-text)")
        self.assertEqual(self.declarations(".status-recibida, .status-recibido").get("color"), "var(--status-success-text)")
        self.assertEqual(self.declarations(".status-enviado").get("color"), "var(--status-sent-text)")
        self.assertEqual(self.declarations(".badge-warning").get("color"), "var(--status-warning-text)")

    def test_api_warnings_keep_warning_semantics_in_both_sync_flows(self):
        self.assertIn("setStatus(index, 'warning', '⚠ Requiere revisión'", self.source)
        self.assertIn("setStatus(resItem.index, 'warning', '⚠ Requiere revisión'", self.source)
        self.assertIn("hidden.textContent = `: ${statusLabel}`;", self.source)

    def test_text_and_status_pairs_meet_aa_in_light_and_dark_themes(self):
        light = self.palette(":root")
        dark = {**light, **self.palette("body.dark-mode")}
        pairs = [
            ("--text-main", "--bg-body"),
            ("--text-main", "--bg-surface"),
            ("--text-muted", "--bg-surface"),
            ("--on-primary", "--primary"),
            ("--status-success-text", "--status-success-bg"),
            ("--status-warning-text", "--status-warning-bg"),
            ("--status-danger-text", "--status-danger-bg"),
            ("--status-loading-text", "--status-loading-bg"),
            ("--status-ignored-text", "--status-ignored-bg"),
            ("--status-sent-text", "--status-sent-bg"),
        ]
        self.assert_role_contrast((("light", light), ("dark", dark)), pairs, 4.5)

    def test_controls_focus_selection_and_progress_meet_non_text_contrast(self):
        light = self.palette(":root")
        dark = {**light, **self.palette("body.dark-mode")}
        pairs = [
            ("--focus-ring", "--bg-body"),
            ("--focus-ring", "--bg-surface"),
            ("--status-success-text", "--status-success-bg"),
            ("--status-warning-text", "--status-warning-bg"),
            ("--status-danger-text", "--status-danger-bg"),
            ("--status-sent-text", "--status-sent-bg"),
            ("--success", "--border"),
        ]
        self.assert_role_contrast((("light", light), ("dark", dark)), pairs, 3)

    def test_week_state_indicators_have_non_color_labels(self):
        self.assertIn('success: "Sincronización registrada"', self.source)
        self.assertIn('warning: "Pendiente de sincronización"', self.source)
        self.assertIn('danger: "Faltan códigos OT"', self.source)
        self.assertIn('none: "Sin facturas"', self.source)
        self.assertIn("status-dot-${statusToken}", self.source)

    def test_status_dot_shadow_uses_a_semantic_token(self):
        self.assertEqual(self.declarations(".status-dot").get("box-shadow"), "var(--shadow-status-dot)")
        self.assertIn("--shadow-status-dot", self.palette(":root"))
        self.assertIn("--shadow-status-dot", self.palette("body.dark-mode"))

    def test_sidebar_shadows_use_theme_tokens(self):
        light = self.palette(":root")
        dark = self.palette("body.dark-mode")
        self.assertEqual(self.declarations(".sidebar").get("box-shadow"), "var(--shadow-sidebar)")
        self.assertIn("box-shadow: var(--shadow-sidebar-mobile)", self.source)
        for role in ("--shadow-sidebar", "--shadow-sidebar-mobile"):
            self.assertIn(role, light)
            self.assertIn(role, dark)

    def test_active_week_has_a_contrasting_selection_marker(self):
        light = self.palette(":root")
        dark = {**light, **self.palette("body.dark-mode")}
        active = self.declarations(".week-item.active")
        self.assertEqual(active.get("background-color"), "var(--primary)")
        self.assertEqual(active.get("color"), "var(--on-primary)")
        self.assertEqual(self.declarations(".week-item").get("border-inline-start"), "1px solid transparent")
        self.assertEqual(active.get("border-inline-start-color"), "var(--on-primary)")
        pairs = [("--on-primary", "--primary")]
        self.assert_role_contrast((("light", light), ("dark", dark)), pairs, 3)

    def test_week_selection_is_exposed_as_a_dynamic_pressed_button(self):
        self.assertIn("button.type = 'button';", self.source)
        self.assertIn("button.className = 'week-item';", self.source)
        self.assertIn("button.setAttribute('aria-pressed', 'false');", self.source)
        self.assertTrue('el.setAttribute("aria-pressed", "false")' in self.source)
        self.assertTrue('elementoLista.setAttribute("aria-pressed", "true")' in self.source)

    def test_paste_highlight_accompanies_visible_content_updates(self):
        normal_start = self.source.index("function pegarNormal(")
        tag_render = self.source.index("renderTags(targetIndex);", normal_start)
        tag_highlight = self.source.index("container.classList.add('paste-highlight')", tag_render)
        self.assertLess(tag_render, tag_highlight)
        row_render = self.source.index("renderTags(rowIndex);", tag_highlight)
        row_highlight = self.source.index("container.classList.add('paste-highlight')", row_render)
        self.assertLess(row_render, row_highlight)
        sheet_start = self.source.index("function handlePlanillaPaste(")
        self.assertLess(
            self.source.index("input.value = celdas[c].trim();", sheet_start),
            self.source.index("input.classList.add('paste-highlight')", sheet_start),
        )


if __name__ == "__main__":
    unittest.main()
