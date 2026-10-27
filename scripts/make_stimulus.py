#!/usr/bin/env python3
"""Panel TR — turn a deliverable into what a panel persona can actually SEE.

    video: frames every 0.5 s for the first 3 s, then 1/s (+ the last frame), a hook sheet
           (first 3 s) and numbered contact sheets with the time under each tile, optional
           whisper transcript, loudness; on-screen text and audio description come from files
           YOU write (personas never "hear" anything).
    site:  Playwright FIREFOX (default) or WEBKIT screenshots (desktop 1440x900 + mobile 390x844,
           above the fold and the full page cut into readable slices) + the visible page text.
    post:  images (carousel order) resized for reading + the caption text.

Writes OUT/stimulus.md (what the persona prompt embeds) and OUT/stimulus.json (frame list for the
evidence check in aggregate.py).

    python scripts/make_stimulus.py video IN.mp4 RUN/stimulus --onscreen onscreen.txt --audio audio.txt \
        [--caption caption.txt] [--transcript]
    python scripts/make_stimulus.py site https://example.com RUN/stimulus      # or a local .html
    python scripts/make_stimulus.py post a.jpg,b.jpg RUN/stimulus --caption caption.txt

Needs ffmpeg/ffprobe on PATH (video), Pillow, and for site mode `pip install playwright` +
`python -m playwright install firefox` (or webkit). Chrome / Chromium are never launched.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import expand, font, load_config  # noqa: E402


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def probe_duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).stdout
    return float(out.strip())


def frame_times(duration: float) -> list[float]:
    ts = [i * 0.5 for i in range(6) if i * 0.5 < duration]           # 0.0 .. 2.5
    t = 3.0
    while t < duration - 0.05:
        ts.append(t)
        t += 1.0
    last = round(max(0.0, duration - 0.2), 2)                          # end card / last thing seen
    if last - ts[-1] >= 0.5:
        ts.append(last)
    return ts


def tile_sheet(items: list[tuple[Path, str]], out: Path, cols: int, tile_w: int, title: str):
    f, ft = font(26), font(30)
    imgs = [Image.open(p).convert("RGB") for p, _ in items]
    ratio = imgs[0].height / imgs[0].width
    tile_h = int(tile_w * ratio)
    label_h, gap, head = 40, 8, 54
    rows = math.ceil(len(items) / cols)
    W = cols * tile_w + (cols + 1) * gap
    H = head + rows * (tile_h + label_h + gap) + gap
    sheet = Image.new("RGB", (W, H), (245, 245, 242))
    d = ImageDraw.Draw(sheet)
    d.text((gap, 12), title, font=ft, fill=(20, 20, 20))
    for i, (im, (_, lab)) in enumerate(zip(imgs, items)):
        r, c = divmod(i, cols)
        x = gap + c * (tile_w + gap)
        y = head + r * (tile_h + label_h + gap)
        sheet.paste(im.resize((tile_w, tile_h)), (x, y))
        d.rectangle([x, y + tile_h, x + tile_w, y + tile_h + label_h], fill=(20, 20, 20))
        d.text((x + 10, y + tile_h + 6), lab, font=f, fill=(255, 255, 255))
    sheet.save(out, quality=88)


def read_opt(path: str | None) -> str:
    return Path(path).read_text(encoding="utf-8").strip() if path else ""


def loudness(path: Path) -> str:
    try:
        err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128",
                              "-f", "null", "-"], capture_output=True, text=True).stderr
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
        return f"{m[-1]} LUFS (entegre)" if m else "ölçülemedi"
    except Exception:
        return "ölçülemedi"


def has_audio(path: Path) -> bool:
    out = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
               str(path)]).stdout
    return bool(out.strip())


def transcript(path: Path, lang: str) -> str:
    """Optional speech transcript. Uses faster-whisper or openai-whisper if installed; never invents text."""
    model = str(load_config().get("transcript_model") or "small")
    try:
        from faster_whisper import WhisperModel          # pip install faster-whisper
        segs, _ = WhisperModel(model, compute_type="int8").transcribe(str(path), language=lang)
        return " ".join(s.text.strip() for s in segs).strip()
    except ImportError:
        pass
    except Exception as e:
        return f"(transkript alınamadı: {e})"
    try:
        import whisper                                    # pip install openai-whisper
        return (whisper.load_model(model).transcribe(str(path), language=lang).get("text") or "").strip()
    except ImportError:
        return "(transkript yok: faster-whisper ya da openai-whisper kurulu değil)"
    except Exception as e:
        return f"(transkript alınamadı: {e})"


def do_video(a):
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sys.exit("video modu için ffmpeg ve ffprobe gerekli (macOS: brew install ffmpeg; Debian/Ubuntu: apt install ffmpeg)")
    src, out = Path(a.input), Path(a.out)
    fr = out / "frames"
    fr.mkdir(parents=True, exist_ok=True)
    dur = probe_duration(src)
    ts = frame_times(dur)
    frames = []
    for t in ts:
        name = f"t{t:06.2f}.jpg"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1",
             "-vf", "scale=540:-2", "-q:v", "3", str(fr / name)])
        frames.append({"t": round(t, 2), "file": f"frames/{name}", "hook": t < 3.0})
    hook = [(out / f["file"], f"t={f['t']:.1f} s") for f in frames if f["hook"]]
    tile_sheet(hook, out / "sheet_00_ilk3sn.jpg", cols=3, tile_w=300, title="İLK 3 SANİYE (0,5 sn arayla)")
    rest = [(out / f["file"], f"t={f['t']:.1f} s") for f in frames if not f["hook"]]
    sheets = ["sheet_00_ilk3sn.jpg"]
    per = math.ceil(len(rest) / max(1, math.ceil(len(rest) / 12)))   # even sheets, at most 12 tiles each
    for k in range(0, len(rest), per):
        name = f"sheet_{k // per + 1:02d}.jpg"
        chunk = rest[k:k + per]
        tile_sheet(chunk, out / name, cols=4, tile_w=260,
                   title=f"DEVAMI (saniyede 1 kare) {chunk[0][1]} → {chunk[-1][1]}")
        sheets.append(name)
    aud = has_audio(src)
    tr = transcript(src, a.lang) if (a.transcript and aud) else ""
    manifest = {"type": "video", "source": src.name, "duration_s": round(dur, 2), "frames": frames,
                "sheets": sheets, "has_audio": aud, "loudness": loudness(src) if aud else None}
    write_manifest(out, manifest, a, tr)


def launch_browser(p):
    """Playwright FIREFOX (default) or WEBKIT only — never Chrome / Chromium / Chrome for Testing."""
    cfg = load_config()
    kind = str(cfg.get("browser") or "firefox").lower()
    if kind not in ("firefox", "webkit"):
        sys.exit("browser must be firefox or webkit")
    bt = getattr(p, kind)
    exe = expand(cfg.get("browser_executable"))
    try:
        return bt.launch(headless=True, timeout=180000, **({"executable_path": str(exe)} if exe else {}))
    except Exception as e:
        sys.exit(f"{kind} açılamadı: {e}\nKurulum: python -m playwright install {kind}  (bkz. README)")


def do_site(a):
    cfg = load_config()
    if cfg.get("playwright_browsers_path"):
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(expand(cfg["playwright_browsers_path"])))
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("site modu için: pip install playwright && python -m playwright install firefox")
    out = Path(a.out)
    shots = out / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    url = a.input if re.match(r"^https?://|^file://", a.input) else Path(a.input).resolve().as_uri()
    frames, text = [], ""
    with sync_playwright() as p:
        br = launch_browser(p)
        try:
            for label, vp, ua in [("desktop", {"width": 1440, "height": 900}, None),
                                  ("mobile", {"width": 390, "height": 844},
                                   "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
                                   "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")]:
                ctx = br.new_context(viewport=vp, user_agent=ua) if ua else br.new_context(viewport=vp)
                pg = ctx.new_page()
                pg.goto(url, wait_until="networkidle", timeout=60000)
                pg.wait_for_timeout(1500)
                fold = shots / f"{label}_00_ilk_ekran.png"
                pg.screenshot(path=str(fold))
                frames.append({"t": f"{label}_ilk_ekran", "file": f"shots/{fold.name}", "hook": True})
                # scroll like a visitor so scroll-reveal sections and lazy media render before the full shot
                height = pg.evaluate("document.documentElement.scrollHeight")
                y = 0
                while y < height:
                    y += vp["height"] // 2
                    pg.mouse.wheel(0, vp["height"] // 2)
                    pg.wait_for_timeout(250)
                pg.wait_for_timeout(1200)
                pg.evaluate("document.documentElement.style.scrollBehavior='auto'; window.scrollTo(0, 0)")
                pg.wait_for_timeout(900)
                full = shots / f"{label}_full.png"
                pg.screenshot(path=str(full), full_page=True)
                if not text:
                    text = pg.inner_text("body")
                ctx.close()
                im = Image.open(full).convert("RGB")
                step = vp["height"] * 2                       # readable slices, two screens each
                for i, y in enumerate(range(0, im.height, step)):
                    sl = im.crop((0, y, im.width, min(im.height, y + step)))
                    if label == "desktop":
                        sl = sl.resize((960, int(sl.height * 960 / sl.width)))
                    name = f"{label}_{i + 1:02d}.jpg"
                    sl.save(shots / name, quality=85)
                    frames.append({"t": f"{label}_{i + 1:02d}", "file": f"shots/{name}", "hook": False})
                full.unlink()
        finally:
            br.close()
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    (out / "site_text.txt").write_text(text, encoding="utf-8")
    manifest = {"type": "site", "source": a.input, "frames": frames, "sheets": [f["file"] for f in frames],
                "visible_text_chars": len(text)}
    write_manifest(out, manifest, a, "", site_text=text[:6000])


def do_post(a):
    out = Path(a.out)
    (out / "post").mkdir(parents=True, exist_ok=True)
    frames = []
    for i, p in enumerate(a.input.split(",")):
        im = Image.open(p.strip()).convert("RGB")
        if im.width > 1080:
            im = im.resize((1080, int(im.height * 1080 / im.width)))
        name = f"post/slide_{i + 1:02d}.jpg"
        im.save(out / name, quality=90)
        frames.append({"t": f"slide_{i + 1:02d}", "file": name, "hook": i == 0})
    manifest = {"type": "post", "source": a.input, "frames": frames, "sheets": [f["file"] for f in frames]}
    write_manifest(out, manifest, a, "")


def write_manifest(out: Path, m: dict, a, tr: str, site_text: str = ""):
    m["onscreen_text"] = read_opt(a.onscreen)
    m["audio_description"] = read_opt(a.audio)
    m["caption"] = read_opt(a.caption)
    m["transcript"] = tr
    if m["type"] == "post":
        m["source"] = ",".join(Path(x.strip()).name for x in str(m["source"]).split(","))
    (out / "stimulus.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    L = [f"# Uyaran ({m['type']})", ""]
    if m["type"] == "video":
        L += [f"- Süre: {m['duration_s']} sn, dikey video. Aşağıdaki görseller videonun karelerinden alındı; "
              "videoyu sen OYNATMADIN, sadece bu kareleri görüyorsun.",
              "- Görseller (sırayla bak):"]
        L += [f"  - `{s}`" for s in m["sheets"]]
        L += ["- Tek tek kareler (yazı okunmuyorsa bunlara bak): `frames/tXXX.XX.jpg` — "
              + ", ".join(f"t={f['t']}" for f in m["frames"])]
    elif m["type"] == "site":
        L += ["- Web sitesinin ekran görüntüleri: önce masaüstü, sonra mobil. `*_ilk_ekran` = sayfa açılınca "
              "kaydırmadan görülen alan.", "- Görseller (sırayla bak):"]
        L += [f"  - `{f['file']}`" for f in m["frames"]]
    else:
        L += ["- Gönderi görselleri (kaydırmalıysa sırasıyla):"]
        L += [f"  - `{f['file']}`" for f in m["frames"]]
    L += ["", "## Ekrandaki yazılar (bizim çıkardığımız liste, karelerle birebir aynı olmalı)", "",
          m["onscreen_text"] or "(liste verilmedi: yazıları sadece karelerden oku)"]
    if m["type"] == "video":
        L += ["", "## Ses (BİZİM ANALİZİMİZ — sen duymadın; sesi duymuş gibi yorum yapma, sadece bu bilgiye dayan)", ""]
        if not m.get("has_audio"):
            L += ["Videoda ses yok."]
        else:
            L += [m["audio_description"] or "(ses açıklaması verilmedi: sesle ilgili yorum yapma)",
                  f"", f"- Ölçülen ses seviyesi: {m.get('loudness')}"]
        if tr:
            L += ["", "## Konuşma metni (otomatik transkript)", "", tr]
    if m["caption"]:
        L += ["", "## Gönderi açıklaması (caption)", "", m["caption"]]
    if site_text:
        L += ["", "## Sayfadaki görünür metin (ilk 6000 karakter)", "", site_text]
    (out / "stimulus.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out / 'stimulus.md'} ({len(m['frames'])} frames/shots)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["video", "site", "post"])
    ap.add_argument("input", help="video file | URL or local .html | comma-separated image paths")
    ap.add_argument("out", help="output dir (e.g. RUN/stimulus or RUN/stimulus_A)")
    ap.add_argument("--onscreen", help="text file: on-screen text with time ranges (we write it)")
    ap.add_argument("--audio", help="text file: neutral audio description from OUR analysis")
    ap.add_argument("--caption", help="text file: post caption as it will be published")
    ap.add_argument("--transcript", action="store_true", help="run whisper on speech (video)")
    ap.add_argument("--lang", default="tr")
    a = ap.parse_args()
    load_config()                                         # fail early on a bad config (e.g. browser: chrome)
    out = Path(a.out)
    ours = {"frames", "shots", "post", "stimulus.json", "stimulus.md", "site_text.txt"}
    if out.exists() and any(out.iterdir()):
        names = {x.name for x in out.iterdir()}
        if not ((out / "stimulus.json").exists() or names <= ours | {f"sheet_{i:02d}.jpg" for i in range(40)}):
            # only ever replace an earlier (or half-written) stimulus dir
            sys.exit(f"{out} is not empty and is not a stimulus dir; pick a new folder")
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    {"video": do_video, "site": do_site, "post": do_post}[a.kind](a)


if __name__ == "__main__":
    main()
