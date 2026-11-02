"""
Genera un paquete de contenido de marketing para una funcionalidad de eGarage.

Uso:
  python manage.py generar_contenido_marketing \\
      --feature "Briefing inteligente para desarmadurías" \\
      --descripcion "Panel que analiza indicadores del negocio y entrega alertas, resumen y recomendaciones" \\
      --idioma es

Opciones completas:
  --feature       Nombre de la funcionalidad (requerido)
  --descripcion   Descripción de la funcionalidad (requerido)
  --publico       Público objetivo (default: talleres en Latinoamérica)
  --idioma        Código de idioma, ej. 'es' (default: es)
  --pais          Código de país, ej. 'CL', 'MX' (default: CL)
  --force         Sobreescribir si la carpeta ya existe
  --dry-run       Imprimir contenido sin crear archivos
"""

import json
import os
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from taller.services.marketing_content_service import MarketingContentService, slugify

# Directorio raíz donde se guarda el contenido generado
_MARKETING_ROOT = Path(__file__).resolve().parents[3] / "marketing" / "contenido_generado"


class Command(BaseCommand):
    help = "Genera un paquete de contenido de marketing para una funcionalidad de eGarage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--feature",
            required=True,
            help="Nombre de la funcionalidad, ej. 'Briefing inteligente'",
        )
        parser.add_argument(
            "--descripcion",
            required=True,
            help="Descripción corta de la funcionalidad",
        )
        parser.add_argument(
            "--publico",
            default="Dueños de talleres mecánicos y casas de repuestos en Latinoamérica",
            help="Público objetivo (default: talleres en Latinoamérica)",
        )
        parser.add_argument(
            "--idioma",
            default="es",
            help="Código de idioma (default: es)",
        )
        parser.add_argument(
            "--pais",
            default="CL",
            help="Código de país ISO (default: CL)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Sobreescribir contenido existente si la carpeta ya existe",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Imprimir el contenido en pantalla sin crear archivos",
        )

    def handle(self, *args, **options):
        feature    = options["feature"].strip()
        descripcion = options["descripcion"].strip()
        publico    = options["publico"].strip()
        idioma     = options["idioma"].strip() or "es"
        pais       = options["pais"].strip().upper() or "CL"
        force      = options["force"]
        dry_run    = options["dry_run"]

        if not feature:
            raise CommandError("--feature no puede estar vacío")
        if not descripcion:
            raise CommandError("--descripcion no puede estar vacío")

        today = date.today()
        slug = slugify(feature)
        folder_name = f"{today.isoformat()}-{slug}"
        dest = _MARKETING_ROOT / folder_name

        if not dry_run:
            if dest.exists() and not force:
                raise CommandError(
                    f"La carpeta ya existe: {dest}\n"
                    "Usa --force para sobreescribir."
                )

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n  eGarage · Marketing Content Generator\n"
            f"  Feature   : {feature}\n"
            f"  Descripción: {descripcion}\n"
            f"  Público   : {publico}\n"
            f"  País      : {pais} | Idioma: {idioma}\n"
            f"  Carpeta   : {folder_name}\n"
            f"  Modo      : {'DRY-RUN (sin archivos)' if dry_run else 'GENERANDO ARCHIVOS'}\n"
        ))

        self.stdout.write("  Llamando al servicio de contenido...")
        pkg = MarketingContentService.generate(
            feature=feature,
            descripcion=descripcion,
            publico=publico,
            idioma=idioma,
            pais=pais,
            fecha=today,
        )

        fuente = "fallback (sin API key)" if pkg.fallback_used else f"AI ({pkg.modelo})"
        self.stdout.write(self.style.SUCCESS(f"  Contenido generado via {fuente}"))

        files = _build_files(pkg)

        if dry_run:
            self._print_dry_run(files, pkg)
            return

        dest.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            (dest / filename).write_text(content, encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"\n  Archivos creados en: {dest}"))
        for filename in files:
            self.stdout.write(f"    ✓ {filename}")
        self.stdout.write("")
        self.stdout.write("  Revisa el contenido antes de publicar.")
        self.stdout.write("  No se ha publicado en ninguna red social.\n")

    def _print_dry_run(self, files: dict, pkg) -> None:
        self.stdout.write(self.style.WARNING("\n  === DRY-RUN — contenido NO guardado ===\n"))
        self.stdout.write(f"  propuesta_valor: {pkg.propuesta_valor}\n")
        self.stdout.write(self.style.MIGRATE_HEADING("  [facebook.md]"))
        self.stdout.write(pkg.facebook["texto"])
        self.stdout.write(self.style.MIGRATE_HEADING("\n  [instagram.md]"))
        self.stdout.write(pkg.instagram["texto"])
        self.stdout.write(self.style.MIGRATE_HEADING("\n  [tiktok.md — gancho]"))
        self.stdout.write(pkg.tiktok["gancho"])
        self.stdout.write(self.style.MIGRATE_HEADING("\n  [hashtags.md]"))
        self.stdout.write("  " + "  ".join(f"#{h}" for h in pkg.hashtags))
        self.stdout.write("")


# ---------------------------------------------------------------------------
# Construcción del contenido de cada archivo
# ---------------------------------------------------------------------------

def _build_files(pkg) -> dict[str, str]:
    return {
        "facebook.md":  _facebook_md(pkg),
        "instagram.md": _instagram_md(pkg),
        "tiktok.md":    _tiktok_md(pkg),
        "reel_guion.md":_reel_md(pkg),
        "historias.md": _historias_md(pkg),
        "hashtags.md":  _hashtags_md(pkg),
        "paquete.json": json.dumps(pkg.to_dict(), ensure_ascii=False, indent=2),
    }


def _facebook_md(pkg) -> str:
    return (
        f"# Facebook — {pkg.feature}\n\n"
        f"> Generado: {pkg.fecha.isoformat()} | "
        f"Fuente: {'fallback' if pkg.fallback_used else pkg.modelo}\n\n"
        f"---\n\n"
        f"{pkg.facebook['texto']}\n"
    )


def _instagram_md(pkg) -> str:
    return (
        f"# Instagram — {pkg.feature}\n\n"
        f"> Generado: {pkg.fecha.isoformat()} | "
        f"Fuente: {'fallback' if pkg.fallback_used else pkg.modelo}\n\n"
        f"---\n\n"
        f"{pkg.instagram['texto']}\n"
    )


def _tiktok_md(pkg) -> str:
    tk = pkg.tiktok
    pantalla = "\n".join(f"- {l}" for l in tk["texto_pantalla"])
    escenas  = "\n".join(f"{i+1}. {e}" for i, e in enumerate(tk["escenas"]))
    return (
        f"# TikTok — {pkg.feature}\n\n"
        f"> Generado: {pkg.fecha.isoformat()} | "
        f"Fuente: {'fallback' if pkg.fallback_used else pkg.modelo}\n\n"
        f"---\n\n"
        f"## Gancho\n{tk['gancho']}\n\n"
        f"## Guion (20-30s)\n{tk['guion']}\n\n"
        f"## Texto en pantalla\n{pantalla}\n\n"
        f"## Escenas sugeridas\n{escenas}\n\n"
        f"## Llamada a la acción\n{tk['cta']}\n"
    )


def _reel_md(pkg) -> str:
    rows = "\n".join(
        f"| {e['tiempo']} | {e['texto']} | {e['visual']} |"
        for e in pkg.reel["escenas"]
    )
    return (
        f"# Guion Reel — {pkg.feature}\n\n"
        f"> Generado: {pkg.fecha.isoformat()} | "
        f"Fuente: {'fallback' if pkg.fallback_used else pkg.modelo}\n\n"
        f"---\n\n"
        f"| Tiempo | Texto en pantalla | Visual sugerido |\n"
        f"|--------|-------------------|-----------------|\n"
        f"{rows}\n"
    )


def _historias_md(pkg) -> str:
    pantallas = ""
    for h in pkg.historias:
        cta_note = " **(CTA)**" if h.get("cta") else ""
        pantallas += f"## Pantalla {h['pantalla']}{cta_note}\n{h['texto']}\n\n"
    return (
        f"# Historias — {pkg.feature}\n\n"
        f"> Generado: {pkg.fecha.isoformat()} | "
        f"Fuente: {'fallback' if pkg.fallback_used else pkg.modelo}\n\n"
        f"---\n\n"
        f"{pantallas}"
    )


def _hashtags_md(pkg) -> str:
    tags = "  ".join(f"#{h}" for h in pkg.hashtags)
    raw_list = "\n".join(f"- #{h}" for h in pkg.hashtags)
    return (
        f"# Hashtags — {pkg.feature}\n\n"
        f"> Generado: {pkg.fecha.isoformat()}\n\n"
        f"---\n\n"
        f"## Listos para copiar\n"
        f"{tags}\n\n"
        f"## Lista individual\n"
        f"{raw_list}\n"
    )
