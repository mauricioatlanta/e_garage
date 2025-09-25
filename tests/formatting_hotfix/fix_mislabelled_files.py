#!/usr/bin/env python3
"""
Fix non-Python files that have .py extension and break black/isort:
- *.html.py -> *.html (if looks like HTML/Django template)
- *.txt.py  -> *.txt  (if looks like plain text)
- PowerShell-in-Python -> .ps1 (detects 'New-Item -ItemType' or 'Write-Host')
Skips git-ignored or disabled folders if you pass --skip-dirs.
Dry-run by default; use --apply to actually rename/move.
"""

import argparse
from pathlib import Path

HTML_HINTS = (
    b"<html",
    b"<!doctype",
    b"{% extends",
    b"{% block",
    b"{{",
    b"{% load",
    b"<head",
    b"<body",
)
PS1_HINTS = (
    b"New-Item -ItemType",
    b"Write-Host",
    b"Get-ChildItem",
    b"Remove-Item",
    b"Out-Null",
    b"Set-Content",
)

DEFAULT_SKIP = [
    "_disabled_templates",
    "templates_final",
    "templates_new",
    "deploy_pythonanywhere",
    "actualizacion_pythonanywhere",
    "frontend/public",
    "reports",
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    "node_modules",
]


def looks_html(buf: bytes) -> bool:
    b = buf.lower()
    return any(h in b for h in HTML_HINTS)


def looks_powershell(buf: bytes) -> bool:
    return any(h in buf for h in PS1_HINTS)


def looks_plaintext(buf: bytes) -> bool:
    b = buf
    if (
        b.strip().startswith(b"#!")
        or b.strip().startswith(b"import ")
        or b"def " in b
        or b"class " in b
    ):
        return False
    if b.count(b"<") > 5 and b.count(b">") > 5:
        return False
    return True


def should_skip(path: Path, skip_dirs):
    p = str(path).replace("\\", "/")
    return any(f"/{sd}/" in p or p.endswith(f"/{sd}") for sd in skip_dirs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root")
    ap.add_argument("--apply", action="store_true", help="Actually rename/move files")
    ap.add_argument(
        "--skip-dirs", nargs="*", default=DEFAULT_SKIP, help="Directories to skip"
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    changed = []
    kept = []
    for p in root.rglob("*.py"):
        if should_skip(p, args.skip_dirs):
            continue
        try:
            buf = p.read_bytes()[:4096]
        except Exception:
            kept.append(("unreadable", str(p)))
            continue

        new_path = None
        if p.name.endswith(".html.py") and looks_html(buf):
            new_path = p.with_suffix("")
        elif p.name.endswith(".txt.py") and looks_plaintext(buf):
            new_path = p.with_suffix("")
        elif looks_powershell(buf) and b"import " not in buf and b"def " not in buf:
            new_path = p.with_suffix(".ps1")

        if new_path and new_path != p:
            if args.apply:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                p.replace(new_path)
                changed.append((str(p), str(new_path)))
            else:
                changed.append((f"(dry-run) {p}", f"-> {new_path}"))
        else:
            kept.append(("kept", str(p)))

    import json

    print(
        json.dumps(
            {
                "root": str(root),
                "apply": args.apply,
                "renamed_count": len(changed),
                "kept_count": len(kept),
                "examples": changed[:10],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
