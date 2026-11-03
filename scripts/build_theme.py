#!/usr/bin/env python3
"""Build the "nova" Ventoy/GRUB theme: background, 9-slice pixmaps, fonts.

Usage:
  python3 -I scripts/build_theme.py            # images + fonts
  python3 -I scripts/build_theme.py --preview  # also write docs/preview.png

Needs Pillow + numpy. Fonts need grub-mkfont (Linux: grub-mkfont,
macOS: `brew install x86_64-elf-grub` -> x86_64-elf-grub-mkfont) and the
JetBrains Mono TTFs (set JETBRAINS_MONO_DIR if they are not in a default
font folder). All sizes assume the 1920x1080 gfxmode set in ventoy.json.
"""
import glob
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "theme", "nova")
W, H = 1920, 1080
SS = 4  # supersampling for anti-aliased shapes

# Palette
BG = (10, 12, 18)
VIOLET = (124, 92, 255)
CYAN = (34, 211, 238)
TEXT = (232, 236, 244)
MUTED = (110, 118, 138)

# Layout (must match theme.txt)
CARD = dict(left=0.30, top=0.27, width=0.40, height=0.44)


def font_path(style):
    dirs = [os.environ.get("JETBRAINS_MONO_DIR", ""),
            os.path.expanduser("~/Library/Fonts"), "/Library/Fonts",
            "/usr/share/fonts", os.path.expanduser("~/.local/share/fonts")]
    for d in dirs:
        if not d:
            continue
        hits = glob.glob(os.path.join(d, "**", f"JetBrainsMono-{style}.ttf"), recursive=True)
        if hits:
            return hits[0]
    sys.exit(f"JetBrainsMono-{style}.ttf not found; set JETBRAINS_MONO_DIR")


def rounded(w, h, r, fill, outline=None, width=1):
    """Anti-aliased rounded rectangle as an RGBA image of size w x h."""
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=r * SS, fill=fill,
                        outline=outline, width=width * SS if outline else 0)
    return img.resize((w, h), Image.Resampling.LANCZOS)


def nine_slice(name, img, b, only=None):
    """Cut img into GRUB 9-slice pieces with border b and save name_<dir>.png."""
    w, h = img.size
    boxes = {
        "nw": (0, 0, b, b), "n": (b, 0, w - b, b), "ne": (w - b, 0, w, b),
        "w": (0, b, b, h - b), "c": (b, b, w - b, h - b), "e": (w - b, b, w, h - b),
        "sw": (0, h - b, b, h), "s": (b, h - b, w - b, h), "se": (w - b, h - b, w, h),
    }
    for k, box in boxes.items():
        if only and k not in only:
            continue
        img.crop(box).save(os.path.join(OUT, f"{name}_{k}.png"))


def three_slice(name, img, b):
    """Horizontal w/c/e slices at full height (selection pill, bars)."""
    w, h = img.size
    img.crop((0, 0, b, h)).save(os.path.join(OUT, f"{name}_w.png"))
    img.crop((b, 0, w - b, h)).save(os.path.join(OUT, f"{name}_c.png"))
    img.crop((w - b, 0, w, h)).save(os.path.join(OUT, f"{name}_e.png"))


def glow(canvas, cx, cy, rx, ry, color, alpha):
    layer = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([(cx - rx) / 4, (cy - ry) / 4, (cx + rx) / 4, (cy + ry) / 4],
              fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(60)).resize((W, H), Image.Resampling.BICUBIC)
    canvas.alpha_composite(layer)


def background():
    img = Image.new("RGBA", (W, H), BG + (255,))
    glow(img, 520, 160, 620, 380, VIOLET, 120)
    glow(img, 1500, 980, 640, 360, CYAN, 70)
    glow(img, 1650, 120, 300, 200, VIOLET, 40)

    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = np.clip((dist - 0.6) * 0.55, 0, 0.45)
    arr = np.asarray(img).astype(np.float32)
    arr[..., :3] *= (1 - vig)[..., None]

    # fine grain to stop gradient banding on 24-bit framebuffers
    rng = np.random.default_rng(7)
    arr[..., :3] += rng.normal(0, 2.2, (H, W, 1))
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")

    # wordmark above the card
    d = ImageDraw.Draw(img)
    title = ImageFont.truetype(font_path("Light"), 44)
    sub = ImageFont.truetype(font_path("Regular"), 18)
    word = "v e n t o y"
    tw = d.textlength(word, font=title)
    ty = int(H * CARD["top"]) - 120
    d.text(((W - tw) / 2, ty), word, font=title, fill=TEXT + (255,))
    tag = "select an image to boot"
    sw = d.textlength(tag, font=sub)
    d.text(((W - sw) / 2, ty + 62), tag, font=sub, fill=MUTED + (255,))
    # accent dot
    cx = (W + tw) / 2 + 18
    d.ellipse([cx - 5, ty + 28, cx + 5, ty + 38], fill=VIOLET + (255,))

    img.convert("RGB").save(os.path.join(OUT, "background.png"), optimize=True)
    return img


def pixmaps():
    # menu card: translucent, hairline border, 20px radius; 24px slices = padding
    card = rounded(49, 49, 20, fill=(20, 24, 34, 200), outline=(255, 255, 255, 26))
    nine_slice("card", card, 24)

    # selection pill: soft violet fill + brighter border
    pill = rounded(41, 48, 12, fill=VIOLET + (60,), outline=VIOLET + (150,))
    three_slice("select", pill, 20)

    # timeout bar: 6px rounded track + accent fill
    three_slice("progress_bar", rounded(13, 6, 3, fill=(255, 255, 255, 30)), 6)
    three_slice("progress_highlight", rounded(13, 6, 3, fill=VIOLET + (255,)), 6)

    # scrollbar thumb (vertical 3-slice: n/c/s)
    thumb = rounded(6, 13, 3, fill=(255, 255, 255, 70))
    thumb.crop((0, 0, 6, 6)).save(os.path.join(OUT, "slider_n.png"))
    thumb.crop((0, 6, 6, 7)).save(os.path.join(OUT, "slider_c.png"))
    thumb.crop((0, 7, 6, 13)).save(os.path.join(OUT, "slider_s.png"))

    # terminal box (F-key consoles, grub shell)
    term = rounded(33, 33, 12, fill=(12, 14, 20, 245), outline=(255, 255, 255, 30))
    nine_slice("terminal_box", term, 16)


FONTS = [  # (ttf style, size) -> grub name "JetBrains Mono <Style> <size>"
    ("Regular", 16), ("Regular", 18), ("Regular", 22), ("Bold", 22),
]


def fonts():
    mk = shutil.which("grub-mkfont") or shutil.which("x86_64-elf-grub-mkfont") \
        or shutil.which("grub2-mkfont")
    if not mk:
        print("WARN: grub-mkfont not found, fonts not rebuilt")
        return
    for style, size in FONTS:
        out = os.path.join(OUT, f"JetBrainsMono_{style}_{size}.pf2")
        # ASCII + Latin-1 + box drawing + arrows keeps the files small
        subprocess.run([mk, "-s", str(size), "-r", "0x20-0x7E,0xA0-0xFF,0x2190-0x21FF,0x2500-0x257F",
                        "-o", out, font_path(style)], check=True)


def preview(bg):
    """Approximate render of the menu for docs/README (not pixel-exact GRUB)."""
    img = bg.copy()
    L, T = int(W * CARD["left"]), int(H * CARD["top"])
    CW, CH = int(W * CARD["width"]), int(H * CARD["height"])
    img.alpha_composite(rounded(CW, CH, 20, fill=(20, 24, 34, 200), outline=(255, 255, 255, 26)), (L, T))
    d = ImageDraw.Draw(img)
    item = ImageFont.truetype(font_path("Regular"), 22)
    bold = ImageFont.truetype(font_path("Bold"), 22)
    small = ImageFont.truetype(font_path("Regular"), 16)
    icons = os.path.join(OUT, "icons")
    rows = [("archlinux", "archlinux-2026.11.01-x86_64.iso"),
            ("cachyos", "cachyos-desktop-linux-260809.iso"),
            ("garuda", "garuda-gnome-linux-garuda-260819.iso"),
            ("SystemRescueCD", "systemrescue-13.02-amd64.iso"),
            ("ubuntu", "ubuntu-26.10-desktop-amd64.iso"),
            ("windows", "Win11-Jul-2025-x64.iso")]
    y = T + 24
    for i, (cls, name) in enumerate(rows):
        x = L + 24
        if i == 0:
            img.alpha_composite(rounded(CW - 48 - 16, 48, 12, fill=VIOLET + (60,), outline=VIOLET + (150,)), (x, y))
        ic = os.path.join(icons, f"{cls}.png")
        if os.path.exists(ic):
            img.alpha_composite(Image.open(ic).convert("RGBA").resize((32, 32)), (x + 14, y + 8))
        d.text((x + 60, y + 12), name, font=bold if i == 0 else item,
               fill=(255, 255, 255) if i == 0 else (150, 158, 178))
        y += 48 + 8
    by = int(H * 0.75)
    img.alpha_composite(rounded(CW, 6, 3, fill=(255, 255, 255, 30)), (L, by))
    img.alpha_composite(rounded(int(CW * 0.6), 6, 3, fill=VIOLET + (255,)), (L, by))
    t = "booting in 6s"
    d.text((L + CW - d.textlength(t, font=small), by + 16), t, font=small, fill=MUTED)
    tip = "F1:Help  F2:Browse  F3:ListView  F4:Localboot  F5:Tools  F6:ExMenu"
    d.text(((W - d.textlength(tip, font=small)) / 2, int(H * 0.93)), tip, font=small, fill=MUTED)
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    img.convert("RGB").save(os.path.join(ROOT, "docs", "preview.png"), optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    bg = background()
    pixmaps()
    fonts()
    if "--preview" in sys.argv:
        preview(bg)
    print(f"theme written to {OUT}")


if __name__ == "__main__":
    main()
