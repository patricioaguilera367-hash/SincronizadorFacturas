from pathlib import Path
import re
import unittest


HTML = Path(__file__).parents[1] / "templates" / "index.html"
DESIGN = Path(__file__).parents[1] / "DESIGN.md"


class BolderIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")

    @classmethod
    def declarations(cls, selector):
        match = re.search(rf"(?m)^\s*{re.escape(selector)}\s*\{{([^}}]*)\}}", cls.source)
        if not match:
            raise AssertionError(f"Missing CSS rule: {selector}")
        return dict((name, value.strip()) for name, value in re.findall(r"([\w-]+)\s*:\s*([^;]+)", match.group(1)))

    def test_ledger_header_replaces_the_old_accent_rail(self):
        self.assertEqual(self.declarations(".week-item").get("border-inline-start"), "1px solid transparent")
        self.assertNotIn(".table-container thead th:first-child", self.source)
        self.assertEqual(self.declarations(".table-container th").get("font-weight"), "700")
        self.assertIn("ink-and-violet", DESIGN.read_text(encoding="utf-8").lower())

    def test_ink_and_violet_hierarchy_frames_the_whole_desk(self):
        light = self.declarations(":root")
        dark = self.declarations("body.dark-mode")
        for palette in (light, dark):
            self.assertEqual(palette.get("--desk-surface"), "var(--text-main)" if palette is light else "var(--bg-body)")
            self.assertIn(palette.get("--desk-text"), {"var(--bg-surface)", "var(--text-main)"})
            self.assertIn(palette.get("--desk-muted"), {"var(--secondary)", "var(--text-muted)"})

        self.assertEqual(self.declarations(".sidebar").get("background"), "var(--desk-surface)")
        self.assertEqual(self.declarations(".header-card").get("background"), "var(--desk-surface)")
        self.assertEqual(self.declarations(".table-container thead").get("background"), "var(--desk-surface)")
        self.assertEqual(self.declarations("th").get("color"), "var(--desk-text)")
        self.assertEqual(self.declarations(".stats-container").get("background"), "var(--secondary)")
        self.assertEqual(self.declarations(".stats-container").get("box-shadow"), "none")
        self.assertIn("ink-and-violet", DESIGN.read_text(encoding="utf-8").lower())

    def test_active_week_is_a_solid_primary_selection(self):
        active = self.declarations(".week-item.active")
        self.assertEqual(active.get("background-color"), "var(--primary)")
        self.assertEqual(active.get("color"), "var(--on-primary)")
        self.assertEqual(active.get("border-inline-start-color"), "var(--on-primary)")
        self.assertEqual(active.get("font-weight"), "600")

    def test_ledger_rows_and_mobile_labels_keep_operational_orientation(self):
        self.assertEqual(
            self.declarations(".table-container tbody > tr:not(.archivos-row):nth-child(even) td").get("background"),
            "var(--secondary)",
        )
        self.assertIn(".table-container tbody > tr:not(.archivos-row):hover td", self.source)
        mobile_start = self.source.index("@media (max-width: 900px)")
        mobile = self.source[mobile_start:]
        self.assertIn(".table-container thead", mobile)
        self.assertIn("content: attr(data-label)", mobile)
        self.assertIn("color: var(--action-text)", mobile)

    def test_controls_and_status_semantics_remain_unchanged(self):
        self.assertEqual(self.declarations(".btn-master").get("background"), "var(--primary)")
        self.assertEqual(self.declarations(".status-pendiente").get("color"), "var(--status-warning-text)")
        self.assertEqual(self.declarations(".status-recibida, .status-recibido").get("color"), "var(--status-success-text)")
        self.assertEqual(self.declarations(".status-enviado").get("color"), "var(--status-sent-text)")
        self.assertIn('elementoLista.setAttribute("aria-pressed", "true")', self.source)


if __name__ == "__main__":
    unittest.main()
