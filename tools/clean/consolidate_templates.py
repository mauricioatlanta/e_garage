#!/usr/bin/env python3
"""
Consolidate templates into a canonical tree:
- Copies chosen "winner" for each duplicate name into templates_canonical/{common|cl/es|us/en}
- Writes a remap CSV with old_path -> new_path for grepping & updating loaders.
WARNING: This does not modify your code; it only builds a clean tree to review.
"""

import argparse
import csv
import shutil
from pathlib import Path


def decide_bucket(path: Path) -> str:
    p = str(path).replace("\\", "/").lower()
    if "/cl/" in p:
        return "cl/es"
    if "/us/" in p:
        return "us/en"
    return "common"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="project root containing templates/")
    ap.add_argument(
        "--dest", default="templates_canonical", help="output canonical tree"
    )
    ap.add_argument(
        "--prefer",
        nargs="*",
        default=[],
        help="substrings to prefer when duplicates exist (e.g. us/en cl/es common)",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    src = root / "templates"
    dst = root / args.dest
    dst.mkdir(parents=True, exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    remap_csv = root / "reports" / "templates_remap.csv"

    # collect by filename
    by_name = {}
    for p in src.rglob("*.html"):
        by_name.setdefault(p.name, []).append(p)

    with remap_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["old_path", "new_path"])
        for name, paths in sorted(by_name.items()):
            # pick winner
            winner = None
            if len(paths) == 1:
                winner = paths[0]
            else:
                # prefer args.prefer order
                for pref in args.prefer:
                    for p in paths:
                        if pref.lower() in str(p).lower():
                            winner = p
                            break
                    if winner:
                        break
                if not winner:
                    winner = paths[0]

            bucket = decide_bucket(winner)
            out = dst / bucket / name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(winner, out)

            for p in paths:
                w.writerow(
                    [p.relative_to(root).as_posix(), out.relative_to(root).as_posix()]
                )

    print(f"✔ Canonical tree at: {dst}")
    print(f"✔ Remap written to: {remap_csv}")


if __name__ == "__main__":
    main()
