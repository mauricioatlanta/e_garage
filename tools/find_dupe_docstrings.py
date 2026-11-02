#!/usr/bin/env python3
"""
Herramienta para detectar docstrings duplicados en archivos Python.
"""

import ast
import pathlib
import sys


def main():
    root = pathlib.Path(".")
    bad = []

    for p in root.rglob("*.py"):
        # omite zonas ruidosas (ajusta a tu repo)
        if any(
            part in p.parts
            for part in (
                "templates_backup_",
                "_disabled_templates",
                "templates",
                ".venv",
                "node_modules",
                "__pycache__",
            )
        ):
            continue
        try:
            src = p.read_text(encoding="utf-8")
            mod = ast.parse(src, filename=str(p))
        except Exception:
            continue

        # cuenta string literals a nivel módulo
        top_strs = [
            n
            for n in mod.body
            if isinstance(n, ast.Expr)
            and isinstance(getattr(n, "value", None), ast.Constant)
            and isinstance(n.value.value, str)
        ]
        if len(top_strs) > 1:
            bad.append((p, len(top_strs)))

    if bad:
        print("Archivos con >1 docstring a nivel módulo:")
        for p, n in bad:
            print(f"  {p}  ({n} docstrings)")
        sys.exit(1)
    else:
        print("OK: sin docstrings duplicados.")


if __name__ == "__main__":
    main()
