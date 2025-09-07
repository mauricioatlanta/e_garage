import pathlib
import sys

ROOT = pathlib.Path("templates")
allowed_prefixes = [
    "taller/common",
    "taller/cl/es",
    "taller/cl/en",
    "taller/us/es",
    "taller/us/en",
    "_deprecated",
]
bad = []
for p in ROOT.rglob("*.html"):
    rel = p.as_posix().split("templates/", 1)[-1]
    if not any(rel.startswith(pref + "/") or rel == pref for pref in allowed_prefixes):
        bad.append(rel)
if bad:
    print("❌ Templates fuera de estructura canónica:")
    for r in bad:
        print(" -", r)
    sys.exit(1)
print("✅ Templates OK")
