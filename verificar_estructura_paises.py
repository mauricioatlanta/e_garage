"""Verificar estructura final de templates por país."""

from pathlib import Path

BASE_DIR = Path(r"E:\projecto\e_garage")

print("=" * 80)
print("VERIFICACIÓN DE ESTRUCTURA POR PAÍS")
print("=" * 80)

countries = ["cl", "us", "pe", "co", "ec", "ve", "br", "mx"]

for country in countries:
    files = [
        f
        for f in BASE_DIR.rglob(f"templates/{country}/**/*.html")
        if f.is_file()
        and "_archive" not in str(f)
        and "revision" not in str(f)
        and "backup" not in str(f)
        and ".venv" not in str(f)
    ]

    if files:
        print(f"\n{country.upper()}: {len(files)} archivos")
        # Agrupar por módulo
        modules = {}
        for f in files:
            rel = f.relative_to(BASE_DIR)
            parts = rel.parts
            if len(parts) >= 4:
                module = parts[3]  # templates/{country}/{lang}/{module}
                if module not in modules:
                    modules[module] = []
                modules[module].append(rel)

        for module, file_list in sorted(modules.items()):
            print(f"  {module}: {len(file_list)} archivos")
            for f in sorted(file_list)[:3]:
                print(f"    - {f}")
            if len(file_list) > 3:
                print(f"    ... y {len(file_list) - 3} más")

print("\n" + "=" * 80)
print("VERIFICACIÓN COMPLETADA")
print("=" * 80)
