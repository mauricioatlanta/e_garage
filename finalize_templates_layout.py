#!/usr/bin/env python3
"""
finalize_templates_layout.py

Goal
----
Keep the deep layout (e.g. templates/taller/{cl/es|us/en|common}/...)
and clean up the "short" copies (templates/{cl|us|common}/...).

What it does
------------
- Scans templates/ for "short" HTML files under: templates/cl/es, templates/us/en, templates/common
- For each short file, finds *candidate deep counterparts* under templates/taller/** with the same filename.
- Compares content (SHA256). If identical to exactly one deep file:
    - By default, DRY RUN prints planned action.
    - With --apply, moves the short file into a backup folder (safe) or deletes with --delete.
- If different content or multiple deep candidates:
    - Leaves the short file in place and flags in the report for manual review.
- Writes a JSON report to reports/finalize_templates_report.json

Usage
-----
# Dry run (recommended first)
python finalize_templates_layout.py --root .

# Apply: move short copies to backup (safe)
python finalize_templates_layout.py --root . --apply

# Apply: delete short copies (dangerous, only if you're sure)
python finalize_templates_layout.py --root . --apply --delete

# Extra: limit to certain subpaths (speeds up trial runs)
python finalize_templates_layout.py --root . --only cl/es us/en common
"""

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

SHORT_PREFIXES = ["templates/cl/es", "templates/us/en", "templates/common"]
DEEP_PREFIX = "templates/taller"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_deep_candidates(templates_root: Path, filename: str):
    return list((templates_root / "taller").rglob(filename))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root with ./templates")
    ap.add_argument("--apply", action="store_true", help="Apply changes (otherwise, dry run)")
    ap.add_argument("--delete", action="store_true", help="Delete instead of backup-move")
    ap.add_argument(
        "--only", nargs="*", help="Limit to these short prefixes (cl/es, us/en, common)"
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    templates = root / "templates"
    if not templates.exists():
        raise SystemExit(f"Missing templates dir: {templates}")

    # Build list of short prefixes to consider
    prefixes = []
    for pref in SHORT_PREFIXES:
        if args.only and not any(pref.endswith(x) for x in args.only):
            continue
        p = root / pref
        if p.exists():
            prefixes.append(p)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / f"templates_short_backup_{ts}"
    backup_dir.mkdir(exist_ok=True)

    report = {
        "root": str(root),
        "apply": args.apply,
        "delete": args.delete,
        "backup_dir": str(backup_dir),
        "processed": [],
        "kept_for_review": [],
        "missing_deep": [],
        "stats": {"short_files": 0, "moved_or_deleted": 0, "kept": 0},
    }

    short_files = []
    for pref in prefixes:
        short_files.extend(p for p in pref.rglob("*.html") if p.is_file())
    report["stats"]["short_files"] = len(short_files)

    for short in short_files:
        fname = short.name
        deep_candidates = find_deep_candidates(templates, fname)

        if not deep_candidates:
            report["missing_deep"].append(str(short.relative_to(root)))
            report["stats"]["kept"] += 1
            continue

        # calc hash for short
        h_short = sha256(short)

        # match identical deep candidates
        identical = [d for d in deep_candidates if sha256(d) == h_short]

        if len(identical) == 1:
            deep = identical[0]
            action = {
                "short": str(short.relative_to(root)),
                "deep": str(deep.relative_to(root)),
                "action": "delete" if args.delete else "backup_move",
            }
            if args.apply:
                if args.delete:
                    short.unlink(missing_ok=True)
                else:
                    # replicate folder structure inside backup
                    dst = backup_dir / short.relative_to(root / "templates")
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(short), str(dst))
                report["stats"]["moved_or_deleted"] += 1
            report["processed"].append(action)
        else:
            # ambiguous or different content -> keep for manual review
            keep_entry = {
                "short": str(short.relative_to(root)),
                "candidates": [str(d.relative_to(root)) for d in deep_candidates],
                "identical_matches": len(identical),
            }
            report["kept_for_review"].append(keep_entry)
            report["stats"]["kept"] += 1

    # Write report
    (root / "reports").mkdir(exist_ok=True)
    out = root / "reports" / "finalize_templates_report.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(
        json.dumps(
            {
                "backup_dir": str(backup_dir),
                "short_files_scanned": report["stats"]["short_files"],
                "moved_or_deleted": report["stats"]["moved_or_deleted"],
                "kept_for_review": len(report["kept_for_review"]),
                "missing_deep": len(report["missing_deep"]),
                "report": str(out),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
