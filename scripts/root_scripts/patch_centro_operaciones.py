import sys
from pathlib import Path

# Prefiere us/base.html si existe; si no, usa base.html
base_candidates = list(Path(".").glob("**/templates/**/us/base.html"))
BASE_TEMPLATE = "us/base.html" if base_candidates else "base.html"

# Localiza el template de /us/centro-operaciones-espacial/
cands = list(Path(".").glob("**/templates/**/centro*operaciones*espacial*.html"))
if not cands:
    print("ERROR: No se encontró el template centro-operaciones-espacial*.html")
    sys.exit(1)

tpl = cands[0]
s = tpl.read_text(encoding="utf-8")

# Asegura {% load static %}
if "{% load static %}" not in s:
    s = "{% load static %}\n" + s

# Si no extiende una base, hazlo y envuelve el contenido en block content
if "{% extends" not in s:
    s = '{% extends "' + BASE_TEMPLATE + '" %}\n' + s
    if "{% block content %}" not in s:
        lines = s.splitlines()
        head = lines[0]  # línea extends
        body = "\n".join(lines[1:])
        s = head + "\n{% block content %}\n" + body + "\n{% endblock %}\n"

tpl.write_text(s, encoding="utf-8")
print(f"OK: parcheado {tpl} usando base '{BASE_TEMPLATE}'")
