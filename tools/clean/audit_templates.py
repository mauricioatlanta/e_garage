#!/usr/bin/env python3
"""
Audit templates for duplicates & layout issues.
- Detects same filenames in multiple paths (potential duplicates).
- Flags templates extending unexpected bases (e.g. common/base.html vs country base).
- Finds templates under _duplicates/ and _unsorted/.
Outputs JSON to stdout.
"""

import argparse
import json
import os
import re
from collections import defaultdict
from pathlib import Path

EXTENDS_RE = re.compile(r"{%\s*extends\s+['\"]([^'\"]+)['\"]\s*%}")


def scan_templates(root: Path):
    tmpl_root = root / "templates"
    results = {
        "by_name": defaultdict(list),
        "extends_map": {},
        "duplicates_dirs": [],
        "stats": {"total": 0},
        "problems": {"duplicates": [], "weird_extends": [], "unsorted": []},
    }
    if not tmpl_root.exists():
        return results

    for p in tmpl_root.rglob("*.html"):
        rel = p.relative_to(root).as_posix()
        results["stats"]["total"] += 1
        results["by_name"][p.name].append(rel)

        txt = p.read_text(encoding="utf-8", errors="ignore")
        m = EXTENDS_RE.search(txt)
        if m:
            results["extends_map"][rel] = m.group(1)

        if any(seg in rel for seg in ["_duplicates/", "_unsorted/"]):
            results["duplicates_dirs"].append(rel)

    # duplicates by name
    for name, paths in results["by_name"].items():
        if len(paths) > 1:
            results["problems"]["duplicates"].append({"file": name, "paths": paths})

    # weird extends: country templates extending "common/base.html" is OK,
    # but country template extending another country's base is weird.
    for rel, ext in results["extends_map"].items():
        rel_l = rel.lower()
        ext_l = ext.lower()
        if "/cl/" in rel_l and "/us/" in ext_l:
            results["problems"]["weird_extends"].append(
                {
                    "template": rel,
                    "extends": ext,
                    "reason": "CL template extends US base",
                }
            )
        if "/us/" in rel_l and "/cl/" in ext_l:
            results["problems"]["weird_extends"].append(
                {
                    "template": rel,
                    "extends": ext,
                    "reason": "US template extends CL base",
                }
            )

    # unsorted
    for rel in results["duplicates_dirs"]:
        results["problems"]["unsorted"].append(rel)

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="project root containing templates/")
    args = ap.parse_args()

    data = scan_templates(Path(args.root).resolve())
    json.dump(data, fp=os.sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
