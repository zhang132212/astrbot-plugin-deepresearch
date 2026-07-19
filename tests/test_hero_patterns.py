import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "output_format" / "hero_patterns.py"
SPEC = importlib.util.spec_from_file_location("deepresearch_hero_patterns", MODULE_PATH)
hero_patterns = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = hero_patterns
SPEC.loader.exec_module(hero_patterns)


class HeroPatternTests(unittest.TestCase):
    def test_uses_a_builtin_visual_without_custom_assets(self):
        original_dir = hero_patterns.HEROES_DIR
        original_legacy = hero_patterns.LEGACY_HERO_PATH
        try:
            with tempfile.TemporaryDirectory() as directory:
                hero_patterns.HEROES_DIR = Path(directory) / "heroes"
                hero_patterns.LEGACY_HERO_PATH = Path(directory) / "report_hero.png"
                self.assertIn(hero_patterns.render_random_hero(), hero_patterns.BUILTIN_HEROES)
        finally:
            hero_patterns.HEROES_DIR = original_dir
            hero_patterns.LEGACY_HERO_PATH = original_legacy

    def test_custom_pngs_take_precedence(self):
        original_dir = hero_patterns.HEROES_DIR
        original_legacy = hero_patterns.LEGACY_HERO_PATH
        try:
            with tempfile.TemporaryDirectory() as directory:
                custom_dir = Path(directory) / "heroes"
                custom_dir.mkdir()
                (custom_dir / "sample.png").write_bytes(b"png-data")
                hero_patterns.HEROES_DIR = custom_dir
                hero_patterns.LEGACY_HERO_PATH = Path(directory) / "report_hero.png"
                self.assertIn("data:image/png;base64,cG5nLWRhdGE=", hero_patterns.render_random_hero())
        finally:
            hero_patterns.HEROES_DIR = original_dir
            hero_patterns.LEGACY_HERO_PATH = original_legacy
