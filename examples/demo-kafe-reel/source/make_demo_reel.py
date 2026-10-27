#!/usr/bin/env python3
"""Build the FICTIONAL demo reel used in examples/demo-kafe-reel (12 s, 1080x1920, no audio).

"Mavi Kozalak Kahve" is made up for this demo; it is not a real business. Everything is drawn with
Pillow (no stock footage, no photos), then encoded with ffmpeg.

    python examples/demo-kafe-reel/source/make_demo_reel.py OUT.mp4
"""
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from common import font  # noqa: E402

W, H, FPS, DUR = 1080, 1920, 30, 12.0
CREAM, ESP, BLUE, ORANGE = (246, 238, 225), (52, 33, 24), (38, 84, 124), (214, 120, 52)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def text_c(d, y, s, size, fill, t_in, t, dy=60):
    a = ease((t - t_in) / 0.45)
    if a <= 0:
        return
    f = font(size)
    w = d.textlength(s, font=f)
    col = tuple(int(c * a + bg * (1 - a)) for c, bg in zip(fill, CREAM))
    d.text(((W - w) / 2, y + (1 - a) * dy), s, font=f, fill=col)


def cup(d, cx, cy, s, t):
    d.rounded_rectangle([cx - 150 * s, cy - 120 * s, cx + 150 * s, cy + 140 * s], int(40 * s), fill=BLUE)
    d.ellipse([cx + 120 * s, cy - 60 * s, cx + 230 * s, cy + 70 * s], outline=BLUE, width=int(26 * s))
    d.ellipse([cx - 230 * s, cy + 120 * s, cx + 230 * s, cy + 200 * s], fill=(222, 210, 192))
    for i in range(3):                       # steam
        x0 = cx - 70 * s + i * 70 * s
        pts = [(x0 + 18 * s * math.sin(t * 3 + i + k / 5), cy - 150 * s - k * 12 * s) for k in range(14)]
        d.line(pts, fill=(170, 150, 130), width=int(10 * s))


def frame(t):
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    if t < 3.0:                                   # hook
        cup(d, W / 2, 1150, 1.0 + 0.05 * t, t)
        text_c(d, 360, "Odunpazarı'nda", 92, ESP, 0.1, t)
        text_c(d, 480, "yeni kahve durağı", 92, ESP, 0.4, t)
        text_c(d, 1560, "açıldı", 70, ORANGE, 1.2, t)
    elif t < 6.0:
        tt = t - 3.0
        cup(d, W / 2, 1300, 0.7, t)
        text_c(d, 380, "Taze kavrum", 96, ESP, 0.0, tt)
        text_c(d, 500, "filtre kahve", 96, ESP, 0.15, tt)
        text_c(d, 700, "Her sabah 08:00'de", 60, BLUE, 0.9, tt)
        text_c(d, 780, "fırından sıcak poğaça", 60, BLUE, 1.1, tt)
    elif t < 9.0:
        tt = t - 6.0
        d.rounded_rectangle([90, 520, W - 90, 1240], 48, fill=ORANGE)
        f1, f2 = font(84), font(54)
        for y, s, f in [(600, "AÇILIŞ HAFTASI", f1), (760, "2. filtre kahve", f1), (880, "bizden", f1),
                        (1080, "20-26 Ekim", f2)]:
            a = ease((tt - (y - 600) / 900) / 0.4)
            if a > 0:
                w = d.textlength(s, font=f)
                d.text(((W - w) / 2, y + (1 - a) * 40), s, font=f, fill=(255, 250, 240))
    else:                                          # end card
        tt = t - 9.0
        cup(d, W / 2, 640, 0.55, t)
        text_c(d, 960, "Mavi Kozalak Kahve", 88, ESP, 0.0, tt)
        text_c(d, 1090, "Odunpazarı, Eskişehir", 52, BLUE, 0.3, tt)
        text_c(d, 1160, "Her gün 08:00-22:00", 52, BLUE, 0.5, tt)
        text_c(d, 1650, "@mavikozalak.kahve", 34, (120, 110, 100), 0.8, tt)
    return im


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "demo_reel.mp4")
    with tempfile.TemporaryDirectory() as td:
        for i in range(int(DUR * FPS)):
            frame(i / FPS).save(f"{td}/f{i:04d}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{td}/f%04d.png",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-movflags", "+faststart",
                        str(out)], check=True)
    print(out)


if __name__ == "__main__":
    main()
