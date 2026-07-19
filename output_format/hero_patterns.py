"""Random, self-contained hero visuals for image reports."""

import base64
import random
from pathlib import Path


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
HEROES_DIR = ASSETS_DIR / "heroes"
LEGACY_HERO_PATH = ASSETS_DIR / "report_hero.png"


BUILTIN_HEROES = (
    """<div class="hero-pattern hero-pattern-bot" aria-hidden="true">
  <span class="spark one"></span><span class="spark two"></span>
  <div class="mascot-panel">
    <span class="antenna"></span>
    <span class="bot-ear left"></span><span class="bot-ear right"></span>
    <span class="bot-face"></span><span class="bot-smile"></span>
  </div>
</div>""",
    """<div class="hero-pattern hero-pattern-library" aria-hidden="true">
  <span class="library-spark library-spark-one"></span>
  <span class="library-spark library-spark-two"></span>
  <div class="library-book library-book-back"></div>
  <div class="library-book library-book-front"><span></span><span></span><span></span></div>
  <div class="library-lens"><i></i></div>
</div>""",
    """<div class="hero-pattern hero-pattern-signal" aria-hidden="true">
  <div class="signal-frame"><span class="signal-line line-one"></span><span class="signal-line line-two"></span><span class="signal-line line-three"></span></div>
  <div class="signal-core"><span></span></div>
  <div class="signal-card card-one"></div><div class="signal-card card-two"></div>
</div>""",
    """<div class="hero-pattern hero-pattern-notes" aria-hidden="true">
  <div class="note-sheet"><span class="note-tab"></span><i></i><i></i><i></i><i></i></div>
  <div class="note-pencil"></div>
  <div class="note-check check-one"></div><div class="note-check check-two"></div>
</div>""",
)


def _custom_hero_markup() -> list[str]:
    paths = []
    if LEGACY_HERO_PATH.is_file():
        paths.append(LEGACY_HERO_PATH)
    if HEROES_DIR.is_dir():
        paths.extend(sorted(path for path in HEROES_DIR.glob("*.png") if path.is_file()))

    markup = []
    for path in paths:
        try:
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            markup.append(
                '<img src="data:image/png;base64,'
                + encoded
                + '" alt="Deep Research hero illustration">'
            )
        except OSError:
            continue
    return markup


def render_random_hero() -> str:
    """Choose a custom PNG when available, otherwise choose a built-in visual."""
    choices = _custom_hero_markup() or list(BUILTIN_HEROES)
    return random.choice(choices)
