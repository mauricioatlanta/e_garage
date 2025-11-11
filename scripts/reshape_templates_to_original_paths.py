#!/usr/bin/env python3
import argparse
import csv
import json
import shutil
from pathlib import Path


def rewrite_promoted_path(root: Path, new_rel: str, assume_promoted: bool) -> str:
    """If templates_canonical/ was promoted (moved to templates/), rewrite new_path accordingly."""
    if new_rel.startswith("templates_canonical/"):
        canonical_dir = root / "templates_canonical"
        if assume_promoted or not canonical_dir.exists():
            return "templates/" + new_rel.split("templates_canonical/", 1)[1]
    return new_rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root with ./templates")
    ap.add_argument("--remap", required=True, help="Path to reports/templates_remap.csv")
    ap.add_argument("--apply", action="store_true", help="Actually perform file operations")
    ap.add_argument(
        "--mode",
        choices=["copy", "move"],
        default="copy",
        help="copy (default) or move winners into old_path",
    )
    ap.add_argument(
        "--assume-promoted",
        action="store_true",
        help="Assume templates_canonical was promoted to templates and rewrite paths accordingly",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    templates = root / "templates"
    remap_csv = (root / args.remap).resolve()
    if not templates.exists():
        raise SystemExit(f"Missing templates dir: {templates}")
    if not remap_csv.exists():
        raise SystemExit(f"CSV not found: {remap_csv}")

    actions = []
    with remap_csv.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            old_rel = row.get("old_path", "").strip()
            new_rel_raw = row.get("new_path", "").strip()
            if not old_rel or not new_rel_raw or old_rel == new_rel_raw:
                continue
            new_rel = rewrite_promoted_path(root, new_rel_raw, args.assume_promoted)

            src = (root / new_rel).resolve()
            dst = (root / old_rel).resolve()

            if not src.exists():
                actions.append(("missing_src", str(src), str(dst)))
                continue

            dst_parent = dst.parent
            dst_parent.mkdir(parents=True, exist_ok=True)

            if args.apply:
                if args.mode == "move":
                    shutil.move(str(src), str(dst))
                    actions.append(("moved", str(src), str(dst)))
                else:
                    shutil.copy2(str(src), str(dst))
                    actions.append(("copied", str(src), str(dst)))
            else:
                actions.append(
                    (
                        "would_" + ("move" if args.mode == "move" else "copy"),
                        str(src),
                        str(dst),
                    )
                )

    print(
        json.dumps(
            {
                "root": str(root),
                "apply": args.apply,
                "mode": args.mode,
                "count": len(actions),
            },
            indent=2,
        )
    )
    for kind, src, dst in actions[:80]:
        print(f"{kind}: {src} -> {dst}")
    if len(actions) > 80:
        print(f"... and {len(actions)-80} more")


if __name__ == "__main__":
    main()
