from pathlib import Path

p = Path(r"e:\projecto\e_garage\tabla_mecanico_actual.py")
if not p.exists():
    print("MISSING")
    raise SystemExit(2)
raw = p.read_bytes()
if b"\x00" in raw:
    cleaned = raw.replace(b"\x00", b"")
    p.write_bytes(cleaned)
    print("REMOVED_NULLS")
else:
    print("NO_NULLS")
