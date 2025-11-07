#!/usr/bin/env python3
"""
cleanup_templates_from_remap.py

Automate template cleanup using a remap CSV (old_path -> new_path) produced by consolidate_templates.py.

Features
- Dry-run by default (prints actions).
- --delete-duplicates: removes OLD files listed in CSV (when old_path != new_path).
- --promote-canonical: backs up ./templates to ./templates_backup_YYYYmmdd_HHMMSS and replaces with ./templates_canonical.
- Safety checks: refuses to run with --apply if missing CSV or required folders.
- Optional: --keep-quarantine keeps templates/_quarantine (default is to remove it if present during promote).

Usage examples
--------------
# Just preview actions (safe):
python cleanup_templates_from_remap.py --root . --remap reports/templates_remap.csv --delete-duplicates

# Apply deletion of duplicates:
python cleanup_templates_from_remap.py --root . --remap reports/templates_remap.csv --delete-duplicates --apply

# Promote canonical tree to be the main templates dir (with backup) — dry run:
python cleanup_templates_from_remap.py --root . --remap reports/templates_remap.csv --promote-canonical

# Do both (delete old files, then promote), applying changes:
python cleanup_templates_from_remap.py --root . --remap reports/templates_remap.csv --delete-duplicates --promote-canonical --apply
"""

import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path


def human(path: Path) -> str:
    try:
        return path.as_posix()
    except Exception:
        return str(path)


def delete_duplicates(root: Path, remap_csv: Path, apply: bool):
    deleted = []
    skipped = []
    with remap_csv.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        if "old_path" not in rdr.fieldnames or "new_path" not in rdr.fieldnames:
            raise SystemExit("CSV must have headers: old_path,new_path")
        for row in rdr:
            old_rel = row["old_path"]
            new_rel = row["new_path"]
            if not old_rel:
                continue
            # If the path is identical, nothing to delete.
            if old_rel.strip() == new_rel.strip():
                skipped.append(("same", old_rel))
                continue

            old_abs = (root / old_rel).resolve()
            if old_abs.exists() and old_abs.is_file():
                if apply:
                    old_abs.unlink()
                deleted.append(old_rel)
            else:
                skipped.append(("missing", old_rel))

    return {"deleted": deleted, "skipped": skipped}


def promote_canonical(root: Path, apply: bool, keep_quarantine: bool = False):
    tmpl = root / "templates"
    canonical = root / "templates_canonical"
    if not canonical.exists():
        raise SystemExit(
            f"Missing: {human(canonical)} - Run consolidate_templates.py first."
        )

    # Prepare backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / f"templates_backup_{ts}"

    # Optional cleanup inside canonical: remove quarantine/duplicates/unsorted if present
    to_prune = []
    for rel in ["_quarantine", "_duplicates", "_unsorted"]:
        p = canonical / rel
        if p.exists() and p.is_dir() and not keep_quarantine:
            to_prune.append(p)

    # Dry-run printouts
    actions = []
    if tmpl.exists():
        actions.append(f"Backup {human(tmpl)} -> {human(backup_dir)}")
    for p in to_prune:
        actions.append(f"Remove {human(p)} (from canonical)")
    actions.append(
        f"Replace {human(tmpl)} with {human(canonical)} (move canonical -> templates)"
    )

    if not apply:
        return {"actions": actions, "backup": human(backup_dir)}

    # Apply
    if tmpl.exists():
        shutil.move(str(tmpl), str(backup_dir))
    # prune in canonical
    for p in to_prune:
        shutil.rmtree(p, ignore_errors=True)
    # Move canonical to templates (rename)
    shutil.move(str(canonical), str(tmpl))
    return {"applied": True, "backup": human(backup_dir)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default=".",
        help="Project root where templates/ and templates_canonical/ live",
    )
    ap.add_argument(
        "--remap", required=True, help="Path to reports/templates_remap.csv"
    )
    ap.add_argument(
        "--delete-duplicates",
        action="store_true",
        help="Delete old template files per CSV (old_path != new_path)",
    )
    ap.add_argument(
        "--promote-canonical",
        action="store_true",
        help="Backup ./templates and replace with ./templates_canonical",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply changes. Otherwise, dry-run only.",
    )
    ap.add_argument(
        "--keep-quarantine",
        action="store_true",
        help="Keep _quarantine/_duplicates/_unsorted when promoting canonical",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    remap_csv = (root / args.remap).resolve()
    if not remap_csv.exists():
        raise SystemExit(f"CSV not found: {human(remap_csv)}")

    summary = {"root": human(root), "remap": human(remap_csv), "apply": args.apply}

    if args.delete_duplicates:
        res = delete_duplicates(root, remap_csv, args.apply)
        summary["delete_duplicates"] = res

    if args.promote_canonical:
        res = promote_canonical(root, args.apply, keep_quarantine=args.keep_quarantine)
        summary["promote_canonical"] = res

    if not args.delete_duplicates and not args.promote_canonical:
        summary["note"] = (
            "Nothing selected. Use --delete-duplicates and/or --promote-canonical."
        )

    import json

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
