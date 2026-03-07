#!/usr/bin/env python
"""
Script de migración automática para vistas que usan templates hardcodeados.
Convierte render() calls a usar template resolution.
"""

import re
import shutil
from pathlib import Path


class TemplateViewMigrator:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.changes_made = []
        self.templates_copied = []

    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")

    def ensure_templates_exist(self, template_path):
        """Asegurar que el template existe en todos los directorios canónicos"""
        # Directorio base donde debería estar el template
        base_template_dir = self.base_path / "templates"
        full_template_path = base_template_dir / template_path

        if not full_template_path.exists():
            self.log(f"⚠️  Template no encontrado: {template_path}", "WARNING")
            return False

        # Directorios canónicos donde copiar
        canonical_dirs = [
            "templates_canonical/taller/cl/es",
            "templates_canonical/taller/cl/en",
            "templates_canonical/taller/us/es",
            "templates_canonical/taller/us/en",
        ]

        # Extraer la parte después de 'taller/'
        if template_path.startswith("taller/"):
            relative_path = template_path[7:]  # Quitar 'taller/'
        else:
            relative_path = template_path

        for canonical_dir in canonical_dirs:
            target_path = self.base_path / canonical_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)

            if not target_path.exists():
                shutil.copy2(full_template_path, target_path)
                self.templates_copied.append(str(target_path))
                self.log(f"✅ Copiado: {template_path} → {canonical_dir}/{relative_path}")

        return True

    def migrate_view_file(self, file_path):
        """Migrar un archivo de vista específico"""
        self.log(f"🔍 Analizando: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Patrón para encontrar render() calls con templates hardcodeados
        pattern = r'render\(\s*request\s*,\s*[\'"]taller/([^\'\"]+\.html)[\'"]\s*,\s*([^)]+)\)'

        matches = re.finditer(pattern, content)
        changes_in_file = 0

        for match in matches:
            template_path = f"taller/{match.group(1)}"
            relative_template = match.group(1)
            context_var = match.group(2)

            self.log(f"🎯 Encontrado: {template_path}")

            # Asegurar que el template exista en directorios canónicos
            if self.ensure_templates_exist(template_path):
                # Crear el código de reemplazo
                replacement = f"""# Usar template resolution en lugar de template hardcodeado
    from taller.utils.templates import select_country_lang_template
    from django.utils.translation import get_language
    from django.template.response import TemplateResponse

    template_name = select_country_lang_template(
        "{relative_template}",
        getattr(request.user.empresa, 'pais', 'cl').lower(),
        get_language()
    )

    return TemplateResponse(request, template_name, {context_var})"""

                # Reemplazar la línea original
                original_line = match.group(0)
                content = content.replace(f"return {original_line}", replacement)
                changes_in_file += 1

                self.changes_made.append(
                    {
                        "file": file_path,
                        "template": template_path,
                        "replaced": original_line,
                    }
                )

        if changes_in_file > 0:
            # Escribir el archivo modificado
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"✅ Migrado: {file_path} ({changes_in_file} cambios)")
        else:
            self.log(f"ℹ️  Sin cambios: {file_path}")

    def find_and_migrate_views(self):
        """Encontrar y migrar todas las vistas que usan templates hardcodeados"""
        self.log("🚀 Iniciando migración automática de vistas")
        self.log("=" * 60)

        # Archivos de vistas a revisar
        view_files = [
            "taller/documentos/views_moderno.py",
            "taller/views_extra/configuracion.py",
            "taller/taller_main_urls.py",
        ]

        for view_file in view_files:
            file_path = self.base_path / view_file
            if file_path.exists():
                self.migrate_view_file(file_path)
            else:
                self.log(f"⚠️  Archivo no encontrado: {view_file}", "WARNING")

        # Resumen
        self.log("=" * 60)
        self.log("📋 RESUMEN DE MIGRACIÓN")
        self.log(
            f"✅ Archivos modificados: {len(set(change['file'] for change in self.changes_made))}"
        )
        self.log(f"✅ Templates migrados: {len(self.changes_made)}")
        self.log(f"✅ Templates copiados: {len(self.templates_copied)}")

        if self.changes_made:
            self.log("\n📝 CAMBIOS REALIZADOS:")
            for change in self.changes_made:
                self.log(f"  📁 {change['file']}")
                self.log(f"    🎯 Template: {change['template']}")

        self.log("\n🎉 ¡Migración automática completada!")


if __name__ == "__main__":
    print("🔧 Migrador Automático de Template Resolution - E-Garage")
    print("Convierte vistas que usan render() hardcodeado a template resolution")
    print()

    migrator = TemplateViewMigrator()
    migrator.find_and_migrate_views()
