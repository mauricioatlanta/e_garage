#!/usr/bin/env python3
"""
Audit static assets:
- Finds assets (css/js/img/svg) outside the /static/ folder.
- Scans templates for <link>/<script>/<img> that point to non-static paths.
- Emits JSON with suggestions.
"""

import argparse
import json
import os
import re
from pathlib import Path

ASSET_EXT = {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"}
LINK_RE = re.compile(
    r"""<(?:link|script|img)[^>]+(?:href|src)\s*=\s*["']([^"']+)["']""", re.IGNORECASE
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="project root")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    static_root = root / "static"
    templates_root = root / "templates"

    outside = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in ASSET_EXT:
            try:
                p.relative_to(static_root)
                # it's inside static
            except ValueError:
                # exclude virtualenvs and hidden dirs
                if any(
                    seg in p.parts
                    for seg in (".venv", "venv", ".git", "__pycache__", "node_modules")
                ):
                    continue
                outside.append(p.relative_to(root).as_posix())

    bad_refs = []
    if templates_root.exists():
        for t in templates_root.rglob("*.html"):
            txt = t.read_text(encoding="utf-8", errors="ignore")
            for url in LINK_RE.findall(txt):
                if url.startswith(("http://", "https://", "{% static", "{{")):
                    continue
                if url.startswith("/") and not url.startswith("/static/"):
                    bad_refs.append(
                        {"template": t.relative_to(root).as_posix(), "url": url}
                    )

    report = {
        "outside_static": sorted(outside),
        "bad_template_refs": bad_refs,
        "summary": {
            "outside_count": len(outside),
            "bad_refs_count": len(bad_refs),
        },
    }
    json.dump(report, fp=os.sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
