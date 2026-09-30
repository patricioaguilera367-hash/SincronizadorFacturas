from pathlib import Path
import re
import unittest


HTML = Path(__file__).parents[1] / "templates" / "index.html"
DESIGN = Path(__file__).parents[1] / "DESIGN.md"


class TypographySystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")

    @classmethod
    def declarations(cls, selector):
        match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>[^}}]*)\}}", cls.source)
        if not match:
            raise AssertionError(f"Missing CSS rule: {selector}")
        return dict(re.findall(r"([\w-]+)\s*:\s*([^;]+)", match.group("body")))

    @classmethod
    def variables(cls, selector):
        return {
            name: value.strip()
            for name, value in cls.declarations(selector).items()
            if name.startswith("--")
        }

    @staticmethod
    def hex_color(value):
        value = value.lstrip("#")
        return tuple(int(value[index : index + 2], 16) / 255 for index in range(0, 6, 2))

    @staticmethod
    def linear(channel):
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    @classmethod
    def contrast(cls, foreground, background):
        def luminance(color):
            red, green, blue = (cls.linear(channel) for channel in color)
            return 0.2126 * red + 0.7152 * green + 0.0722 * blue

        first, second = sorted((luminance(foreground), luminance(background)), reverse=True)
        return (first + 0.05) / (second + 0.05)

    @staticmethod
    def composite(rgba, background):
        red, green, blue, alpha = (float(value) for value in re.findall(r"[\d.]+", rgba))
        foreground = (red / 255, green / 255, blue / 255)
        return tuple(
            (channel * alpha) + (base * (1 - alpha))
            for channel, base in zip(foreground, background)
        )

    @classmethod
    def background_color(cls, value, palette):
        token = re.fullmatch(r"var\((--[\w-]+)\)", value)
        if token:
            return cls.hex_color(palette[token.group(1)])
        return cls.composite(value, cls.hex_color(palette["--bg-surface"]))

    def test_semantic_roles_declare_size_weight_and_leading(self):
        expected = {
            "body": {
                "font-size": "var(--type-body)",
                "font-weight": "400",
                "line-height": "var(--leading-body)",
            },
            ".header-titles h1": {
                "font-size": "var(--type-page-title)",
                "font-weight": "700",
                "line-height": "var(--leading-tight)",
            },
            "td, .tag-input, .spreadsheet-input": {
                "font-size": "var(--type-data)",
                "font-weight": "400",
                "line-height": "var(--leading-dense)",
            },
            ".status-badge": {
                "font-size": "var(--type-meta)",
                "font-weight": "600",
                "line-height": "var(--leading-dense)",
            },
        }
        for selector, properties in expected.items():
            declarations = self.declarations(selector)
            for property_name, value in properties.items():
                self.assertEqual(declarations.get(property_name), value, selector)

    def test_heading_sequence_starts_with_page_heading(self):
        levels = [int(level) for level in re.findall(r"<h([1-6])(?:\s|>)", self.source)]
        self.assertEqual(levels[0], 1)
        self.assertTrue(all(current <= previous + 1 for previous, current in zip(levels, levels[1:])))

    def test_design_muted_token_matches_the_light_theme(self):
        design = DESIGN.read_text(encoding="utf-8")
        light = self.variables(":root")
        documented = re.search(r'^  text-muted: "(#[0-9A-Fa-f]{6})"$', design, re.MULTILINE)
        self.assertIsNotNone(documented)
        self.assertEqual(documented.group(1), light["--text-muted"])

    def test_status_text_meets_contrast_target_in_both_themes(self):
        light = self.variables(":root")
        dark = {**light, **self.variables("body.dark-mode")}
        for selector, text_token in (
            (".badge-success", "--status-success-text"),
            (".badge-danger", "--status-danger-text"),
            (".badge-loading", "--status-loading-text"),
            (".badge-ignored", "--status-ignored-text"),
        ):
            declarations = self.declarations(selector)
            self.assertEqual(declarations.get("color"), f"var({text_token})")
            for theme, palette in (("light", light), ("dark", dark)):
                with self.subTest(selector=selector, theme=theme):
                    foreground = self.hex_color(palette[text_token])
                    background = self.background_color(declarations["background"], palette)
                    self.assertGreaterEqual(self.contrast(foreground, background), 4.5)


if __name__ == "__main__":
    unittest.main()
