#!/usr/bin/env python3
"""
prefer_country_layout.py

Objective
---------
Keep only country-specific templates:
  - templates/taller/us/en/** and templates/taller/cl/es/**
Remove "common" variants:
  - templates/taller/common/**
Also remove short copies under:
  - templates/common/**

Behavior
--------
- Reads reports/finalize_templates_report.json (from finalize_templates_layout.py).
- For every kept_for_review entry that includes a deep "common" candidate and
  at least one country-specific candidate with the SAME filename, we remove/move
  the deep "common" file.
- Then, we remove/move the entire "templates/common" short tree.
- Finally, if "templates/taller/common" becomes empty, we remove/move that folder too.

By default: DRY RUN. Use --apply to perform changes.
Use --delete to delete instead of moving to backup.

Usage
-----
# Preview actions
python prefer_country_layout.py --root . --report reports/finalize_templates_report.json

# Apply: move to backup
python prefer_country_layout.py --root . --report reports/finalize_templates_report.json --apply

# Apply + delete (no backup; be sure!)
python prefer_country_layout.py --root . --report reports/finalize_templates_report.json --apply --delete
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


def move_or_delete(
    path: Path, backup_root: Path, do_delete: bool, apply: bool, actions: list
):
    if not path.exists():
        actions.append(("missing", str(path)))
        return
    if apply:
        if do_delete:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            actions.append(("deleted", str(path)))
        else:
            # move preserving relative structure under backup root
            rel = path
            # make rel relative to project root by walking up until we find marker dirs
            # assume backup_root is under project root; compute a relative path safely
            try:
                # If path is inside the project root (parent of backup_root), get relative
                project_root = backup_root.parent
                rel = path.relative_to(project_root)
            except Exception:
                rel = path.name
            dst = backup_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dst))
            actions.append(("moved_to_backup", f"{path} -> {dst}"))
    else:
        actions.append(
            ("would_delete" if do_delete else "would_move_to_backup", str(path))
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root")
    ap.add_argument(
        "--report",
        default="reports/finalize_templates_report.json",
        help="Path to finalize report JSON",
    )
    ap.add_argument("--apply", action="store_true", help="Apply changes")
    ap.add_argument(
        "--delete", action="store_true", help="Delete instead of moving to backup"
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    report_path = (root / args.report).resolve()
    if not report_path.exists():
        raise SystemExit(f"Report not found: {report_path}")

    with report_path.open("r", encoding="utf-8") as f:
        rep = json.load(f)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / f"templates_country_pref_backup_{ts}"

    actions = []
    removed_common_deep = 0

    # 1) Remove deep 'templates/taller/common/**' when there is a country-specific twin
    for entry in rep.get("kept_for_review", []):
        short = entry.get("short", "")
        candidates = entry.get("candidates", [])
        # consider only filename, we only remove deep common copies
        deep_common = [
            c for c in candidates if "templates/taller/common/" in c.replace("\\", "/")
        ]
        deep_us = [
            c for c in candidates if "templates/taller/us/en/" in c.replace("\\", "/")
        ]
        deep_cl = [
            c for c in candidates if "templates/taller/cl/es/" in c.replace("\\", "/")
        ]
        if deep_common and (deep_us or deep_cl):
            for c in deep_common:
                p = (root / c).resolve()
                move_or_delete(p, backup_root, args.delete, args.apply, actions)
                removed_common_deep += 1

    # 2) Remove short 'templates/common/**' entirely
    short_common_dir = root / "templates/common"
    if short_common_dir.exists():
        move_or_delete(short_common_dir, backup_root, args.delete, args.apply, actions)

    # 3) If 'templates/taller/common' is empty after removals, delete it too
    deep_common_dir = root / "templates/taller/common"
    if deep_common_dir.exists():
        is_empty = True
        for _ in deep_common_dir.rglob("*"):
            is_empty = False
            break
        if is_empty:
            move_or_delete(
                deep_common_dir, backup_root, args.delete, args.apply, actions
            )

    summary = {
        "root": str(root),
        "apply": args.apply,
        "delete": args.delete,
        "backup_root": str(backup_root),
        "removed_deep_common_files": removed_common_deep,
        "actions_count": len(actions),
    }
    print(json.dumps(summary, indent=2))
    for a in actions[:100]:
        print(f"{a[0]}: {a[1]}")
    if len(actions) > 100:
        print(f"... and {len(actions)-100} more actions")


if __name__ == "__main__":
    main()
