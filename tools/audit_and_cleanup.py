# tools/audit_and_cleanup.py
"""
Audita la raíz del repo (donde está manage.py o la carpeta del proyecto)
- Genera un informe Markdown con:
  * archivos sueltos sospechosos (backups, pruebas, checkers)
  * scripts de carga de datos
  * notas y checklists (.md)
  * conteo de apps Django y templates
  * recomendaciones de movimiento
- (Opcional) con --apply mueve los archivos a carpetas seguras:
    /docs, /scripts, /_backup
Uso:
  python tools/audit_and_cleanup.py                # solo informe
  python tools/audit_and_cleanup.py --apply        # aplica movimientos
  python tools/audit_and_cleanup.py --root E:/projecto/e_garage
"""
from __future__ import annotations
import argparse, re, shutil, sys
from pathlib import Path
from datetime import datetime

SUSPECT_PATTERNS = [
    r"backup.*\.py$", r".*final.*working.*\.py$", r"check_.*\.py$",
    r"arreglo_.*\.md$", r"bugfix_.*\.md$", r"checklist.*\.md$",
    r"confirmaci[oó]n_.*", r"acceso_.*\.py$", r"agregar_.*\.py$",
    r"cargar_.*\.py$", r"comando_.*\.py$", r"clear_.*\.py$",
    r"configurar_.*\.py$", r"company_settings.*\.py$",
    r".*COMPLETADO.*\.md$", r".*MANUAL.*\.md$",
    r"debug_.*\.py$", r"diagnostico_.*\.py$", r"fix_.*\.py$",
    r"crear_.*\.py$", r"demo_.*\.py$", r"generar_.*\.py$",
    r"limpiar_.*\.py$", r"migrar_.*\.py$", r"actualizar_.*\.py$",
    r"corregir_.*\.py$", r"completar_.*\.py$", r"aplicar_.*\.py$",
    r"buscar_.*\.py$", r"encontrar_.*\.py$", r"mostrar_.*\.py$",
    r"listar_.*\.py$", r"consultar_.*\.py$", r"eliminar_.*\.py$",
    r"deploy_.*\.py$", r"monitoring_.*\.py$", r"auditor_.*\.py$",
    r"automatizacion\.py$", r"analisis_.*\.py$", r"estado_.*\.py$",
    r"esquema\.sql$", r"bom_files\.txt$", r"auditor_resultado\.txt$",
    r"django_check_deploy_prod\.txt$", r"input\.css$", r"moneda\.py$",
    r"context_processors\.py$", r"models\.py$", r"ia_views\.py$",
    r"onboarding_.*\.py$", r"migration_script\.py$", r"mark_migration\.py$",
    r"get-pip\.py$", r"package-lock\.json$", r"package\.json$",
    r"landing_egarage\.html$", r"company_settings\.html$", r"debug_js\.html$",
    r"diagnostico_imagenes\.html$", r"crear_documento_moderno_backup\.html$",
    r"invoice_.*\.pdf$", r"\.ps1$", r"\.sh$"
]
DATA_LOADERS = [r"cargar_.*\.py$", r".*_fixtures?\.py$"]
NOTES_MD     = [r".*\.md$"]

MOVE_MAP = {
    "scripts": [
        r"cargar_.*\.py$", r"agregar_.*\.py$", r"check_.*\.py$", 
        r"acceso_.*\.py$", r"comando_.*\.py$", r"clear_.*\.py$", 
        r"configurar_.*\.py$", r"debug_.*\.py$", r"diagnostico_.*\.py$",
        r"fix_.*\.py$", r"crear_.*\.py$", r"demo_.*\.py$", r"generar_.*\.py$",
        r"limpiar_.*\.py$", r"migrar_.*\.py$", r"actualizar_.*\.py$",
        r"corregir_.*\.py$", r"completar_.*\.py$", r"aplicar_.*\.py$",
        r"buscar_.*\.py$", r"encontrar_.*\.py$", r"mostrar_.*\.py$",
        r"listar_.*\.py$", r"consultar_.*\.py$", r"eliminar_.*\.py$",
        r"deploy_.*\.py$", r"monitoring_.*\.py$", r"auditor_.*\.py$",
        r"automatizacion\.py$", r"analisis_.*\.py$", r"estado_.*\.py$",
        r"onboarding_.*\.py$", r"migration_script\.py$", r"mark_migration\.py$",
        r"company_settings_views\.py$", r"ia_views\.py$", r"context_processors\.py$",
        r"models\.py$", r"moneda\.py$", r"esquema\.sql$", r"bom_files\.txt$",
        r"auditor_resultado\.txt$", r"django_check_deploy_prod\.txt$",
        r"input\.css$", r"get-pip\.py$", r"package-lock\.json$", r"package\.json$",
        r"landing_egarage\.html$", r"company_settings\.html$", r"debug_js\.html$",
        r"diagnostico_imagenes\.html$", r"crear_documento_moderno_backup\.html$",
        r"invoice_.*\.pdf$", r"\.ps1$", r"\.sh$"
    ],
    "docs":    [r".*\.md$"],
    "_backup": [r".*backup.*", r".*final.*working.*"],
}

DJANGO_APP_HINTS = ["apps.py", "models.py", "views.py", "urls.py", "migrations"]

def match_any(name:str, patterns:list[str]) -> bool:
    return any(re.fullmatch(p, name, flags=re.IGNORECASE) for p in patterns)

def find_manage_py(root:Path) -> Path|None:
    for p in [root, *root.glob("**/")]:
        cand = p / "manage.py"
        if cand.exists():
            return cand
    return None

def is_django_app_dir(d:Path) -> bool:
    try:
        entries = {e.name for e in d.iterdir()}
    except PermissionError:
        return False
    hits = sum(1 for h in DJANGO_APP_HINTS if h in entries or any(x.name=="__init__.py" for x in d.glob("migrations")))
    return hits >= 2 and (d/"__init__.py").exists()

def classify_files(root:Path):
    suspects, loaders, notes, others = [], [], [], []
    for p in root.iterdir():
        if p.name.startswith(".") or p.name in {"venv",".venv","node_modules","__pycache__"}:
            continue
        if p.is_dir():
            continue
        name = p.name
        if match_any(name, SUSPECT_PATTERNS): suspects.append(p)
        elif match_any(name, DATA_LOADERS):   loaders.append(p)
        elif match_any(name, NOTES_MD):       notes.append(p)
        else:                                 others.append(p)
    return suspects, loaders, notes, others

def ensure_dirs(root:Path, dirs:list[str]):
    for d in dirs:
        (root/d).mkdir(exist_ok=True)

def move_if_needed(root:Path, targets:dict[str,list[str]], files:list[Path], apply:bool, decisions:list[str]):
    for f in files:
        dest_folder = None
        for folder, pats in targets.items():
            if match_any(f.name, pats):
                dest_folder = folder
                break
        if dest_folder:
            dest = root/dest_folder/f.name
            if apply:
                # Evita sobrescribir
                final = dest
                i=1
                while final.exists():
                    final = dest.with_name(f"{dest.stem}__{i}{dest.suffix}")
                    i+=1
                shutil.move(str(f), str(final))
                decisions.append(f"MOVED  {f.name} -> {final.relative_to(root)}")
            else:
                decisions.append(f"WOULD MOVE {f.name} -> {dest_folder}/{f.name}")
        else:
            decisions.append(f"KEEP   {f.name}")

def scan_apps(root:Path):
    apps=[]
    for d in root.iterdir():
        if d.is_dir() and (d/"__init__.py").exists() and is_django_app_dir(d):
            apps.append(d.name)
    return sorted(apps)

def count_templates(root:Path):
    total=0
    for d in ["templates","templates_canonical","taller","frontend"]:
        p = root/d if isinstance(d, Path) else root/str(d)
        if p.exists():
            total += sum(1 for _ in p.rglob("*.html"))
    return total

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default=".")
    ap.add_argument("--apply", action="store_true", help="mover archivos (no solo informe)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    manage = find_manage_py(root)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report = root / f"eg_cleanup_report_{timestamp}.md"

    suspects, loaders, notes, others = classify_files(root)
    apps = scan_apps(root)
    templates_count = count_templates(root)

    decisions=[]
    ensure_dirs(root, ["scripts","docs","_backup"])

    move_if_needed(root, MOVE_MAP, suspects+loaders+notes, args.apply, decisions)

    with report.open("w", encoding="utf-8") as fh:
        fh.write(f"# eGarage – Auditoría de raíz\n\n")
        fh.write(f"- Fecha: {timestamp}\n")
        fh.write(f"- Root: `{root}`\n")
        fh.write(f"- manage.py: {manage if manage else 'NO ENCONTRADO'}\n")
        fh.write(f"- Apps Django detectadas: {len(apps)} → {', '.join(apps)}\n")
        fh.write(f"- Templates .html contados: {templates_count}\n\n")

        def wsec(title, items):
            fh.write(f"## {title} ({len(items)})\n")
            for p in items:
                fh.write(f"- {p.name}\n")
            fh.write("\n")

        wsec("Sospechosos / pruebas / checkers", suspects)
        wsec("Scripts de carga de datos", loaders)
        wsec("Notas/Checklists (.md)", notes)
        wsec("Otros archivos sueltos en raíz", others)

        fh.write("## Decisiones\n")
        fh.write("```\n" + "\n".join(decisions) + "\n```\n")
        fh.write("\n> NOTA: ejecuta con `--apply` para realizar los movimientos.\n")

    print(f"✅ Informe generado: {report.name}")
    if args.apply:
        print("✅ Movimientos aplicados (ver sección 'Decisiones' en el informe).")
    else:
        print("ℹ️ Modo simulación. Usa --apply para mover archivos.")
if __name__ == "__main__":
    sys.exit(main())
