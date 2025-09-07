#!/usr/bin/env python
"""
Script para identificar y migrar automáticamente todas las vistas que usan templates hardcodeados.
Paso 6B: Extensión de la migración a todas las vistas del sistema.
"""

import glob
import os
import re
from pathlib import Path


class GlobalTemplateMigrator:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.migrations_made = []
        self.errors = []

    def log(self, message, level="INFO"):
        print(f"[{level}] {message}")

    def find_hardcoded_templates(self):
        """Encontrar todas las vistas que usan templates hardcodeados"""
        self.log("🔍 Buscando vistas con templates hardcodeados...")

        # Buscar archivos Python con render() calls
        python_files = glob.glob(str(self.base_path / "**/*.py"), recursive=True)
        hardcoded_templates = []

        for py_file in python_files:
            if "templates_canonical" in py_file or "verificar_" in py_file:
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Buscar patrones de render con templates hardcodeados
                    render_patterns = [
                        r"render\(request,\s*['\"]([^'\"]+\.html)['\"]",
                        r"TemplateResponse\(request,\s*['\"]([^'\"]+\.html)['\"]",
                        r"template_name\s*=\s*['\"]([^'\"]+\.html)['\"]",
                    ]

                    for pattern in render_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if not match.startswith("taller/"):
                                # Es un template que podría necesitar migración
                                hardcoded_templates.append(
                                    {
                                        "file": py_file,
                                        "template": match,
                                        "pattern": pattern,
                                    }
                                )

            except (UnicodeDecodeError, PermissionError):
                continue

        return hardcoded_templates

    def categorize_templates(self, hardcoded_templates):
        """Categorizar templates por tipo para migración inteligente"""
        categories = {
            "dashboard": [],
            "onboarding": [],
            "auth": [],
            "common": [],
            "other": [],
        }

        for item in hardcoded_templates:
            template = item["template"]
            if "dashboard" in template or "centro_operaciones" in template:
                categories["dashboard"].append(item)
            elif "bienvenida" in template or "onboarding" in template:
                categories["onboarding"].append(item)
            elif "login" in template or "signup" in template or "auth" in template:
                categories["auth"].append(item)
            elif "base" in template or "common" in template:
                categories["common"].append(item)
            else:
                categories["other"].append(item)

        return categories

    def create_template_directories(self):
        """Crear directorios necesarios para templates canónicos"""
        self.log("📁 Creando estructura de directorios...")

        base_dirs = [
            "templates_canonical/taller/cl/es/",
            "templates_canonical/taller/cl/en/",
            "templates_canonical/taller/us/es/",
            "templates_canonical/taller/us/en/",
        ]

        subdirs = ["dashboard", "onboarding", "auth", "common"]

        for base_dir in base_dirs:
            for subdir in subdirs:
                full_path = self.base_path / base_dir / subdir
                full_path.mkdir(parents=True, exist_ok=True)

        self.log("✅ Directorios creados")

    def migrate_templates_to_canonical(self, categories):
        """Migrar templates existentes a estructura canónica"""
        self.log("📋 Migrando templates a estructura canónica...")

        # Buscar templates existentes
        template_dirs = [
            "templates/",
            "templates_new/templates/",
            "taller/templates/",
        ]

        migrated_count = 0

        for category_name, items in categories.items():
            for item in items:
                template_name = item["template"]

                # Buscar el template en directorios existentes
                template_found = False
                for template_dir in template_dirs:
                    source_path = self.base_path / template_dir / template_name
                    if source_path.exists():
                        # Copiar a estructura canónica
                        target_dirs = [
                            f"templates_canonical/taller/cl/es/{category_name}/",
                            f"templates_canonical/taller/cl/en/{category_name}/",
                            f"templates_canonical/taller/us/es/{category_name}/",
                            f"templates_canonical/taller/us/en/{category_name}/",
                        ]

                        template_filename = Path(template_name).name

                        for target_dir in target_dirs:
                            target_path = (
                                self.base_path / target_dir / template_filename
                            )
                            target_path.parent.mkdir(parents=True, exist_ok=True)

                            if not target_path.exists():
                                import shutil

                                shutil.copy2(source_path, target_path)
                                migrated_count += 1

                        template_found = True
                        break

                if not template_found:
                    self.log(f"⚠️  Template no encontrado: {template_name}", "WARNING")

        self.log(f"✅ {migrated_count} templates migrados")

    def generate_migration_patches(self, categories):
        """Generar parches de migración para las vistas"""
        self.log("🔧 Generando parches de migración...")

        migration_template = """
# Migración automática para usar template resolution
from taller.utils.templates import select_country_lang_template
from django.utils.translation import get_language
from django.template.response import TemplateResponse

# ANTES:
# return render(request, '{original_template}', context)

# DESPUÉS:
template_name = select_country_lang_template(
    "{canonical_template}", 
    getattr(request.user.empresa, 'pais', 'cl').lower(), 
    get_language()
)
return TemplateResponse(request, template_name, context)
"""

        migration_file = self.base_path / "MIGRATION_PATCHES.md"

        with open(migration_file, "w", encoding="utf-8") as f:
            f.write("# PATCHES DE MIGRACIÓN AUTOMÁTICA\n\n")
            f.write(
                "Este archivo contiene los parches necesarios para migrar todas las vistas.\n\n"
            )

            for category_name, items in categories.items():
                if items:
                    f.write(f"## {category_name.upper()}\n\n")

                    for item in items:
                        template_name = item["template"]
                        canonical_name = f"{category_name}/{Path(template_name).name}"

                        f.write(f"### {item['file']}\n")
                        f.write(
                            f"**Template**: `{template_name}` → `{canonical_name}`\n\n"
                        )
                        f.write("```python\n")
                        f.write(
                            migration_template.format(
                                original_template=template_name,
                                canonical_template=canonical_name,
                            )
                        )
                        f.write("```\n\n")

    def apply_critical_migrations(self, categories):
        """Aplicar migraciones críticas automáticamente"""
        self.log("🚨 Aplicando migraciones críticas...")

        critical_files = [
            "taller/views_extra/country_views.py",
            "taller/views_extra/dashboard_empresa.py",
        ]

        critical_migrations = {
            "dashboard_usa.html": "dashboard/dashboard_usa.html",
            "onboarding/bienvenida_chile.html": "onboarding/bienvenida_chile.html",
            "dashboard_chile.html": "dashboard/dashboard_chile.html",
        }

        migrations_applied = 0

        for file_path in critical_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                original_content = content

                for old_template, new_template in critical_migrations.items():
                    if f"'{old_template}'" in content or f'"{old_template}"' in content:
                        # Reemplazar el render call
                        old_pattern = (
                            rf"render\(request,\s*['\"{old_template}\"'],\s*([^)]+)\)"
                        )
                        new_code = f"""# Usar template resolution
    from taller.utils.templates import select_country_lang_template
    from django.utils.translation import get_language
    from django.template.response import TemplateResponse
    
    template_name = select_country_lang_template(
        "{new_template}", 
        getattr(request.user.empresa, 'pais', 'cl').lower(), 
        get_language()
    )
    
    return TemplateResponse(request, template_name, \\1)"""

                        content = re.sub(old_pattern, new_code, content)
                        migrations_applied += 1

                if content != original_content:
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.log(f"✅ Migrado: {file_path}")

        self.log(f"✅ {migrations_applied} migraciones críticas aplicadas")

    def run_migration(self):
        """Ejecutar migración completa"""
        self.log("🚀 Iniciando migración global de templates")
        self.log("=" * 60)

        # 1. Encontrar templates hardcodeados
        hardcoded = self.find_hardcoded_templates()
        self.log(f"📊 Encontrados {len(hardcoded)} templates hardcodeados")

        # 2. Categorizar
        categories = self.categorize_templates(hardcoded)
        for cat, items in categories.items():
            if items:
                self.log(f"  {cat}: {len(items)} templates")

        # 3. Crear directorios
        self.create_template_directories()

        # 4. Migrar templates
        self.migrate_templates_to_canonical(categories)

        # 5. Generar patches
        self.generate_migration_patches(categories)

        # 6. Aplicar migraciones críticas
        self.apply_critical_migrations(categories)

        self.log("=" * 60)
        self.log("✅ MIGRACIÓN GLOBAL COMPLETADA")
        self.log("📝 Revisar MIGRATION_PATCHES.md para migraciones pendientes")


if __name__ == "__main__":
    migrator = GlobalTemplateMigrator()
    migrator.run_migration()
