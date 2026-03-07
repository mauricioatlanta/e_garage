import ast, pathlib

FILES = [
    "taller/analytics/funcionalidades_adicionales.py",
    "taller/vehiculos/api_helpers.py",
    "wsgi_production.py",
    "deploy_pythonanywhere/wsgi_production.py",
]

HEADER = '"""eGarage — módulo limpiado para pre-commit (docstring al inicio)."""\n'


def fix_file(path: pathlib.Path):
    src = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(src)
    except Exception:
        print(f"!! {path}: no se pudo parsear, lo salto.")
        return

    lines = src.splitlines()
    # Encuentra TODAS las expresiones top-level que sean strings sueltas (posibles docstrings de módulo)
    top_string_exprs = []
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(getattr(node, "value", None), ast.Constant)
            and isinstance(node.value.value, str)
        ):
            s = node.lineno
            e = getattr(node, "end_lineno", s)
            top_string_exprs.append((s, e))

    # 1) Comenta TODAS las docstrings sueltas (para evitar múltiples). Luego añadiremos una única arriba.
    for s, e in reversed(top_string_exprs):
        block = lines[s - 1 : e]
        # si ya parecen comentario, salta
        if all((ln.strip().startswith("#") or ln.strip() == "") for ln in block):
            continue
        commented = [("# " + ln) if ln.strip() else ln for ln in block]
        lines[s - 1 : e] = commented

    new_src = "\n".join(lines)

    # 2) Asegura una docstring en la línea 1
    # Si el archivo no empieza con triple-quote, insértala
    start = new_src.lstrip()
    has_header = start.startswith('"""') or start.startswith("r'''") or start.startswith("'''")
    if not has_header:
        new_src = HEADER + new_src

    path.write_text(new_src, encoding="utf-8")
    print(f"✔ Arreglado: {path}")


for f in FILES:
    p = pathlib.Path(f)
    if p.exists():
        fix_file(p)
    else:
        print(f"(?) No existe: {f}")
