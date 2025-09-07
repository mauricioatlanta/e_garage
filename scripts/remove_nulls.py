import sys
from pathlib import Path

p = Path(r"e:\projecto\e_garage\taller\reportes\exporters.py")
if not p.exists():
    print("MISSING")
    sys.exit(1)
raw = p.read_bytes()
if b"\x00" in raw:
    p.write_bytes(raw.replace(b"\x00", b""))
    print("REMOVED_NULLS")
else:
    print("NO_NULLS")
