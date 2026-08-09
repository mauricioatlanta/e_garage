#!/usr/bin/env python3
"""
Sprint B visual asset pipeline for eGarage.

Flow:
  marketing/Assets/Master/01_taller.{png,jpg,…}
       ↓  crop to 16:9, full resolution
  marketing/Assets/Scenes/01_taller.webp          (scene master — 16:9)
       ↓  resize to each format
  marketing/Assets/Exports/Hero/01_taller_2560x1440.webp
  marketing/Assets/Exports/OG/01_taller_1200x630.webp
  marketing/Assets/Exports/Social/01_taller_1080x1350.webp
  marketing/Assets/Exports/Story/01_taller_1080x1920.webp
  marketing/Assets/Exports/Thumbnail/01_taller_1280x720.webp
       ↓  web-optimised copy
  static/img/welcome/scenes/taller.webp

Usage:
  python marketing/scripts/export_assets.py          # process all masters
  python marketing/scripts/export_assets.py --check  # only report what's missing
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

# ── project root (two levels above this file) ────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]

MASTER_DIR   = ROOT / "marketing" / "Assets" / "Master"
SCENES_DIR   = ROOT / "marketing" / "Assets" / "Scenes"
EXPORTS_DIR  = ROOT / "marketing" / "Assets" / "Exports"
WEB_DIR      = ROOT / "static" / "img" / "welcome" / "scenes"

# Numbered master prefix → scene name (web slug)
SCENE_MAP = {
    "01_taller":         "taller",
    "02_repuestos":      "repuestos",
    "03_desarme":        "desarme",
    "04_carwash":        "carwash",
    "05_control_center": "control_center",
}

# Export format name → (width, height)
EXPORT_FORMATS = {
    "Hero":      (2560, 1440),
    "OG":        (1200,  630),
    "Social":    (1080, 1350),
    "Story":     (1080, 1920),
    "Thumbnail": (1280,  720),
}

WEB_SIZE    = (1920, 1080)   # optimized for browser hero (smaller than master)
WEB_QUALITY = 85
EXPORT_QUALITY = 88

SOURCE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}

ANSI_OK    = "\033[32m✓\033[0m"
ANSI_WARN  = "\033[33m⚠\033[0m"
ANSI_ERR   = "\033[31m✗\033[0m"
ANSI_INFO  = "\033[36m·\033[0m"


def find_master(prefix: str) -> Path | None:
    for ext in SOURCE_EXTS:
        candidate = MASTER_DIR / f"{prefix}{ext}"
        if candidate.exists():
            return candidate
    return None


def fit_crop(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize+center-crop to exact (width, height) preserving quality."""
    return ImageOps.fit(img, size, method=Image.LANCZOS)


def export_one(prefix: str, scene: str, dry_run: bool = False) -> dict:
    master_path = find_master(prefix)
    result = {"prefix": prefix, "scene": scene, "found": master_path is not None, "exports": []}

    if master_path is None:
        return result

    if dry_run:
        result["exports"] = list(EXPORT_FORMATS.keys()) + ["web"]
        return result

    img = Image.open(master_path).convert("RGB")

    # Scene master (16:9, lossless quality reference)
    scene_out = SCENES_DIR / f"{prefix}.webp"
    fit_crop(img, (2560, 1440)).save(scene_out, "WEBP", quality=92)
    result["exports"].append(f"Scenes/{prefix}.webp")

    # Per-format exports
    for fmt_name, size in EXPORT_FORMATS.items():
        fmt_dir = EXPORTS_DIR / fmt_name
        fmt_dir.mkdir(parents=True, exist_ok=True)
        w, h = size
        out = fmt_dir / f"{prefix}_{w}x{h}.webp"
        fit_crop(img, size).save(out, "WEBP", quality=EXPORT_QUALITY)
        result["exports"].append(f"Exports/{fmt_name}/{out.name}")

    # Web-ready copy
    web_out = WEB_DIR / f"{scene}.webp"
    fit_crop(img, WEB_SIZE).save(web_out, "WEBP", quality=WEB_QUALITY)
    result["exports"].append(f"static/.../scenes/{scene}.webp")

    return result


def check_status() -> None:
    print("\neGarage Sprint B — asset status\n" + "─" * 40)
    all_ok = True
    for prefix, scene in SCENE_MAP.items():
        master = find_master(prefix)
        web = WEB_DIR / f"{scene}.webp"
        web_is_placeholder = web.exists() and web.stat().st_size < 500

        if master:
            status = ANSI_OK
            note = f"master found → {master.name}"
        else:
            status = ANSI_WARN
            note = "master missing — add to marketing/Assets/Master/"
            all_ok = False

        web_note = ""
        if web_is_placeholder:
            web_note = f" {ANSI_WARN} web placeholder (will be replaced on export)"
        elif web.exists():
            web_note = f" {ANSI_OK} web ok"
        else:
            web_note = f" {ANSI_ERR} web missing"

        print(f"  {status}  {prefix:22s}  {note}{web_note}")

    print()
    if all_ok:
        print(f"{ANSI_OK}  All masters present. Run without --check to export.\n")
    else:
        print(f"{ANSI_WARN}  Some masters are missing. Add them to marketing/Assets/Master/ and re-run.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="eGarage visual asset export pipeline")
    parser.add_argument("--check",   action="store_true", help="report status without exporting")
    parser.add_argument("--dry-run", action="store_true", help="show what would be exported without writing files")
    parser.add_argument("scene",     nargs="*",           help="limit to specific scene names (e.g. taller repuestos)")
    args = parser.parse_args()

    if args.check:
        check_status()
        return

    target_scenes = set(args.scene) if args.scene else set(SCENE_MAP.values())
    processed = 0

    print("\neGarage Sprint B — export pipeline\n" + "─" * 40)
    for prefix, scene in SCENE_MAP.items():
        if scene not in target_scenes:
            continue

        result = export_one(prefix, scene, dry_run=args.dry_run)
        if not result["found"]:
            print(f"  {ANSI_WARN}  {prefix:22s}  no master — skipping")
            continue

        label = "(dry-run) " if args.dry_run else ""
        print(f"  {ANSI_OK}  {prefix:22s}  {label}→ {len(result['exports'])} files")
        for exp in result["exports"]:
            print(f"       {ANSI_INFO}  {exp}")
        processed += 1

    print()
    if processed == 0:
        print(f"{ANSI_WARN}  No masters found. Add images to marketing/Assets/Master/ and re-run.\n")
    else:
        verb = "Would export" if args.dry_run else "Exported"
        print(f"{ANSI_OK}  {verb} {processed}/{len(SCENE_MAP)} scenes.\n")


if __name__ == "__main__":
    main()
