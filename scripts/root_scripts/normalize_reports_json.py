import json, pathlib

p = pathlib.Path("reports/templates_audit.json")
if p.exists():
    b = p.read_bytes()
    # intenta varias codificaciones
    for enc in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            s = b.decode(enc)
            break
        except Exception:
            s = None
    # si no se pudo o está corrupto => vaciamos
    obj = []
    if s:
        try:
            obj = json.loads(s)
        except Exception:
            obj = []
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✔ normalized reports/templates_audit.json")
else:
    print("skip: reports/templates_audit.json not found")
