"""Shared helpers for Panel TR: config, edition, persona and source loading, fonts.

No absolute paths are hard-coded. Everything is resolved from:
  1. environment variables (PANEL_TR_CONFIG, PANEL_TR_EDITION, PANEL_TR_RUNS_DIR),
  2. config.yaml next to SKILL.md (copy config.example.yaml),
  3. built-in defaults below.
"""
from __future__ import annotations

import os
import platform
import re
from pathlib import Path

import yaml

SKILL = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"

DEFAULTS = {
    "runs_dir": "~/panel-tr-runs",
    "browser": "firefox",                 # firefox | webkit   (Chrome/Chromium are refused)
    "playwright_browsers_path": None,     # optional: custom Playwright browser cache
    "browser_executable": None,           # optional: explicit Firefox/WebKit binary
    "font_path": None,                    # optional: a .ttf with Turkish glyphs for contact sheets/charts
    "transcript_model": "small",          # used only if faster-whisper or openai-whisper is installed
    "viewer_age_weights": {               # Instagram Türkiye yaş dağılımı, NapoleonCat Eylül 2026 [NC:F02-F06]
        "18-24": 0.216, "25-34": 0.328, "35-44": 0.197, "45-54": 0.137, "55+": 0.122},
    "calibration": {
        "viewer": ("Türkiye'de 10-50 bin takipçili Instagram hesaplarında medyan etkileşim oranı yaklaşık %0,44 "
                   "(Click Analytic, Eylül 2026); markaların reels'lerinde gönderi başına ortalama etkileşim %0,50 "
                   "(Socialinsider 2025). Yani 1.000 takipçili bir hesabın ortalama reels'ine 4-6 beğeni, yorum, "
                   "paylaşım ya da kaydetme gelir; izleyenlerin büyük çoğunluğu hiçbir şey yapmadan geçer."),
        "buyer": ("Soğuk B2B tekliflerine ortalama yanıt oranı %4,1 (Hunter, 2024'te gönderilen 11 milyon e-posta); "
                  "50 kişiden küçük kampanyalarda %5,8, 1.000+ kişilik kampanyalarda %2,1. Yani teklifi gören "
                  "100 işletmeden kabaca 2-6'sı cevap verir."),
    },
}


def _deep_merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = _deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def config_path() -> Path | None:
    env = os.environ.get("PANEL_TR_CONFIG")
    if env:
        return Path(env).expanduser()
    p = SKILL / "config.yaml"
    return p if p.exists() else None


def load_config() -> dict:
    cfg = DEFAULTS
    p = config_path()
    if p and p.exists():
        cfg = _deep_merge(DEFAULTS, yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    if os.environ.get("PANEL_TR_RUNS_DIR"):
        cfg = {**cfg, "runs_dir": os.environ["PANEL_TR_RUNS_DIR"]}
    if str(cfg.get("browser", "firefox")).lower() not in ("firefox", "webkit"):
        raise SystemExit("config: browser must be 'firefox' or 'webkit' (Chrome/Chromium are not supported)")
    return cfg


def expand(p: str | None) -> Path | None:
    """~ and $VARS expanded; relative paths are relative to the current directory."""
    if not p:
        return None
    return Path(os.path.expandvars(os.path.expanduser(str(p))))


def runs_dir() -> Path:
    return expand(load_config()["runs_dir"])


# ---------------------------------------------------------------- edition
def edition() -> str:
    env = os.environ.get("PANEL_TR_EDITION")
    if env:
        return env.strip().lower()
    f = SKILL / "EDITION"
    if f.exists():
        return f.read_text(encoding="utf-8").strip().lower()
    return "pro"          # source checkout (development): everything available


def is_pro() -> bool:
    return edition() == "pro"


def require_pro(feature: str):
    if not is_pro():
        raise SystemExit(f"'{feature}' Panel TR Pro özelliğidir (bu kurulum: Lite). "
                         "Lite: 10 izleyici, tek seçenek, hızlı rapor. Bkz. README.")


def persona_dir() -> Path:
    flat = SKILL / "personas"
    if (flat / "viewers.yaml").exists():          # release layout: personas/{viewers,buyers}.yaml
        return flat
    return flat / edition()                       # source layout: personas/lite|pro/


def persona_files() -> dict[str, Path]:
    d = persona_dir()
    return {k: d / f"{k}s.yaml" for k in ("viewer", "buyer") if (d / f"{k}s.yaml").exists()}


def load_personas(panel: str | None = None) -> list[dict]:
    out = []
    for p, f in persona_files().items():
        if panel and p != panel:
            continue
        out += yaml.safe_load(f.read_text(encoding="utf-8")) or []
    return out


# ---------------------------------------------------------------- sources
# A trait ends with [varsayım] or [KEY:F07] / [KEY:12] / [KEY:12-14] (fact id or line numbers in that file).
TAG = re.compile(r"\[(varsayım|([A-Z]{2}):(F\d{2,3}|\d+)(?:-(F\d{2,3}|\d+))?)\]\s*$")


def load_sources() -> dict[str, Path]:
    idx = SKILL / "sources" / "index.yaml"
    raw = yaml.safe_load(idx.read_text(encoding="utf-8")) or {}
    return {k: (SKILL / "sources" / v) for k, v in raw.items()}


def source_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split("\n")


def resolve_cite(lines: list[str], a: str, b: str | None) -> list[int] | None:
    """Return 1-based line numbers for a citation, or None if it does not exist."""
    def one(x: str) -> int | None:
        if x.startswith("F"):
            for i, ln in enumerate(lines, 1):
                if ln.startswith(x + " "):
                    return i
            return None
        n = int(x)
        return n if 1 <= n <= len(lines) else None
    ia, ib = one(a), one(b or a)
    if ia is None or ib is None or ib < ia:
        return None
    return list(range(ia, ib + 1))


def age_band(age: int) -> str:
    for lo, hi, b in [(18, 24, "18-24"), (25, 34, "25-34"), (35, 44, "35-44"), (45, 54, "45-54")]:
        if lo <= age <= hi:
            return b
    return "55+"


# ---------------------------------------------------------------- fonts
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",            # macOS
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",          # Debian/Ubuntu
    "/usr/share/fonts/TTF/DejaVuSans.ttf",                      # Arch
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",        # Fedora
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/noto/NotoSans-Regular.ttf",
]


def font(size: int):
    from PIL import ImageFont
    custom = expand(load_config().get("font_path"))
    for p in ([str(custom)] if custom else []) + FONT_CANDIDATES:
        if p and Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)     # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def system_summary() -> str:
    return f"{platform.system()} {platform.release()} / Python {platform.python_version()}"
