#!/usr/bin/env python3
"""Validate ventoy.json against the theme on disk.

Checks:
  1. ventoy.json is well-formed JSON.
  2. Every menu_class `class` has a matching icons/<class>.png (case-sensitive).
  3. Every icon is a real PNG sized to the theme's icon_width/icon_height.
  4. The generic "/iso/linux" catch-all is the last linux rule (first match wins,
     so a catch-all placed above a more specific path would shadow it).
  5. Theme and font files referenced by ventoy.json exist on disk.

Exit code is non-zero if any check fails, so CI goes red.
"""
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME_DIR = ICON_DIR = None  # set in main() from ventoy.json theme.file

errors = []
warnings = []


def png_size(path):
    """Return (width, height) for a PNG, or None if it is not a valid PNG."""
    with open(path, "rb") as fh:
        header = fh.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def theme_icon_size():
    """Read icon_width/icon_height from theme.txt (defaults to 32x32)."""
    w = h = 32
    theme_txt = os.path.join(THEME_DIR, "theme.txt")
    try:
        text = open(theme_txt).read()
    except OSError:
        return w, h
    mw = re.search(r"icon_width\s*=\s*(\d+)", text)
    mh = re.search(r"icon_height\s*=\s*(\d+)", text)
    if mw:
        w = int(mw.group(1))
    if mh:
        h = int(mh.group(1))
    return w, h


def repo_rel(path):
    """Resolve a ventoy.json path to a repo-root path.

    Theme/font paths in ventoy.json are relative to the USB drive root, where
    this repo lives in the "ventoy/" folder. So "/ventoy/theme/x" and
    "ventoy/theme/x" both map to "theme/x" inside this repo.
    """
    rel = path.lstrip("/")
    if rel.startswith("ventoy/"):
        rel = rel[len("ventoy/"):]
    return os.path.join(ROOT, rel)


def main():
    cfg_path = os.path.join(ROOT, "ventoy.json")
    try:
        cfg = json.load(open(cfg_path))
    except (OSError, ValueError) as exc:
        print(f"FATAL: cannot parse ventoy.json: {exc}")
        return 1

    global THEME_DIR, ICON_DIR
    theme_file = cfg.get("theme", {}).get("file", "/ventoy/theme/nova/theme.txt")
    THEME_DIR = os.path.dirname(repo_rel(theme_file))
    ICON_DIR = os.path.join(THEME_DIR, "icons")

    icon_w, icon_h = theme_icon_size()
    entries = cfg.get("menu_class", [])

    # 2 + 3: every class has a correctly-sized icon
    for entry in entries:
        cls = entry.get("class")
        if not cls:
            errors.append(f"menu_class entry missing 'class': {entry}")
            continue
        icon = os.path.join(ICON_DIR, f"{cls}.png")
        if not os.path.isfile(icon):
            errors.append(f"class '{cls}' has no icon at {os.path.relpath(ICON_DIR, ROOT)}/{cls}.png")
            continue
        size = png_size(icon)
        if size is None:
            errors.append(f"icons/{cls}.png is not a valid PNG")
        elif size != (icon_w, icon_h):
            warnings.append(
                f"icons/{cls}.png is {size[0]}x{size[1]}, theme renders at {icon_w}x{icon_h}"
            )

    # 4: catch-all ordering — first match wins, so "/iso/linux" must come after
    #    every "/iso/linux/<distro>" entry.
    linux_parents = [
        (i, e.get("parent", "")) for i, e in enumerate(entries)
        if e.get("parent", "").startswith("/iso/linux")
    ]
    catch_all = [i for i, p in linux_parents if p.rstrip("/") == "/iso/linux"]
    for ci in catch_all:
        shadowed = [p for i, p in linux_parents if i > ci and p.rstrip("/") != "/iso/linux"]
        if shadowed:
            errors.append(
                "'/iso/linux' catch-all appears before more specific entries that it "
                f"will shadow: {shadowed}"
            )

    # 5: referenced theme + font files exist
    theme = cfg.get("theme", {})
    if theme.get("file") and not os.path.isfile(repo_rel(theme["file"])):
        errors.append(f"theme.file not found on disk: {theme['file']}")
    for font in theme.get("fonts", []):
        if not os.path.isfile(repo_rel(font)):
            errors.append(f"font not found on disk: {font}")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"FAIL: {e}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK: {len(entries)} menu_class entries validated, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
