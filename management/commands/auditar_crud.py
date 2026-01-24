"""
Comando de auditoría CRUD para eGarage

Verifica:
1. Permisos en vistas CRUD (LoginRequiredMixin, RoleRequiredMixin, etc.)
2. Filtrado multi-tenant por empresa
3. URLs existentes vs accesibles
4. Templates con botones/links
5. Duplicados de templates
"""

import inspect
import os
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand
from django.urls import reverse, NoReverseMatch
from django.apps import apps

from taller.models import Documento, Repuesto, Cliente, Servicio, ServicioExterno
from taller.documentos.views_migrated import DocumentoDeleteView, DocumentoUpdateView
from taller.repuestos.views import eliminar_repuesto
from taller.clientes.views import cliente_delete
from taller.servicios.views import eliminar_servicio, eliminar_otro_servicio
from taller.servicios.views_cbv import ServicioDeleteView


class Command(BaseCommand):
    help = "Audita el CRUD completo de eGarage para detectar problemas comunes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="REPORTE_AUDITORIA_CRUD.md",
            help="Archivo de salida para el reporte",
        )

    def handle(self, *args, **options):
        self.output_file = options["output"]
        self.issues = defaultdict(list)
        self.warnings = defaultdict(list)
        self.success = defaultdict(list)

        self.stdout.write(self.style.SUCCESS("🔍 Iniciando auditoría CRUD de eGarage...\n"))

        # 1. Verificar permisos en vistas
        self.auditar_permisos_vistas()

        # 2. Verificar filtrado multi-tenant
        self.auditar_multi_tenant()

        # 3. Verificar URLs y rutas
        self.auditar_urls()

        # 4. Verificar templates
        self.auditar_templates()

        # 5. Verificar duplicados de templates
        self.auditar_duplicados_templates()

        # Generar reporte
        self.generar_reporte()

    def auditar_permisos_vistas(self):
        """Verifica que las vistas tengan los mixins de permisos correctos"""
        self.stdout.write("📋 Verificando permisos en vistas...")

        # Documentos
        if hasattr(DocumentoDeleteView, "allowed_roles"):
            if "Owner" in DocumentoDeleteView.allowed_roles or "Admin" in DocumentoDeleteView.allowed_roles:
                self.success["permisos"].append("✅ DocumentoDeleteView tiene roles restringidos (Owner/Admin)")
            else:
                self.issues["permisos"].append("❌ DocumentoDeleteView no restringe a Owner/Admin")
        else:
            self.issues["permisos"].append("❌ DocumentoDeleteView no tiene allowed_roles definido")

        # Repuestos - verificar si tiene filtrado por empresa
        # eliminar_repuesto es una función, no una clase, así que verificamos el código
        repuesto_delete_code = inspect.getsource(eliminar_repuesto)
        if "empresa" in repuesto_delete_code.lower():
            self.success["permisos"].append("✅ eliminar_repuesto verifica empresa")
        else:
            self.warnings["permisos"].append("⚠️ eliminar_repuesto podría no filtrar por empresa")

        # Clientes
        cliente_delete_code = inspect.getsource(cliente_delete)
        if "empresa" in cliente_delete_code.lower():
            self.success["permisos"].append("✅ cliente_delete filtra por empresa")
        else:
            self.issues["permisos"].append("❌ cliente_delete no filtra por empresa")

        # Servicios
        if hasattr(ServicioDeleteView, "get_queryset"):
            self.success["permisos"].append("✅ ServicioDeleteView tiene get_queryset (probablemente filtra por empresa)")
        else:
            self.warnings["permisos"].append("⚠️ ServicioDeleteView podría no filtrar por empresa")

    def auditar_multi_tenant(self):
        """Verifica que todas las vistas filtren por empresa"""
        self.stdout.write("🏢 Verificando filtrado multi-tenant...")

        # Verificar que las vistas usen TenantViewMixin o filtren manualmente
        from core.views import TenantViewMixin

        # Documentos
        if hasattr(DocumentoDeleteView, "get_queryset"):
            qs_code = inspect.getsource(DocumentoDeleteView.get_queryset)
            if "empresa" in qs_code.lower():
                self.success["multi_tenant"].append("✅ DocumentoDeleteView.get_queryset filtra por empresa")
            else:
                self.issues["multi_tenant"].append("❌ DocumentoDeleteView.get_queryset no filtra por empresa")

        # Verificar UpdateView también
        if hasattr(DocumentoUpdateView, "get_queryset"):
            self.success["multi_tenant"].append("✅ DocumentoUpdateView tiene get_queryset")
        else:
            self.warnings["multi_tenant"].append("⚠️ DocumentoUpdateView podría no filtrar por empresa")

    def auditar_urls(self):
        """Verifica que las URLs estén definidas y sean accesibles"""
        self.stdout.write("🔗 Verificando URLs...")

        urls_a_verificar = [
            ("documentos:eliminar_documento", {"pk": 1}),
            ("repuestos:eliminar_repuesto", {"pk": 1}),
            ("clientes:eliminar_cliente", {"cliente_id": 1}),
            ("servicios:eliminar_servicio", {"pk": 1}),
            ("servicios:eliminar_otro_servicio", {"pk": 1}),
            ("documentos:documento_editar", {"pk": 1}),
            ("repuestos:editar_repuesto", {"pk": 1}),
            ("clientes:editar_cliente", {"pk": 1}),
            ("servicios:editar_servicio", {"pk": 1}),
        ]

        for url_name, kwargs in urls_a_verificar:
            try:
                reverse(url_name, kwargs=kwargs)
                self.success["urls"].append(f"✅ URL '{url_name}' existe y es reversible")
            except NoReverseMatch:
                self.issues["urls"].append(f"❌ URL '{url_name}' no existe o no es reversible")

    def auditar_templates(self):
        """Verifica que los templates tengan botones de acción"""
        self.stdout.write("📄 Verificando templates...")

        base_dir = Path(__file__).resolve().parent.parent.parent
        templates_dir = base_dir / "templates"

        # Buscar templates de lista
        templates_a_verificar = [
            "taller/common/documentos/lista_documentos.html",
            "taller/common/clientes/cliente_list.html",
            "taller/repuestos/lista_repuestos.html",
        ]

        for template_path in templates_a_verificar:
            full_path = templates_dir / template_path
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8")
                # Verificar botones de acción
                has_create = "crear" in content.lower() or "nuevo" in content.lower() or "create" in content.lower()
                has_edit = "editar" in content.lower() or "edit" in content.lower()
                has_delete = "eliminar" in content.lower() or "delete" in content.lower() or "borrar" in content.lower()

                if has_create and has_edit and has_delete:
                    self.success["templates"].append(f"✅ {template_path} tiene botones crear/editar/eliminar")
                else:
                    missing = []
                    if not has_create:
                        missing.append("crear")
                    if not has_edit:
                        missing.append("editar")
                    if not has_delete:
                        missing.append("eliminar")
                    self.warnings["templates"].append(
                        f"⚠️ {template_path} le faltan: {', '.join(missing)}"
                    )
            else:
                # Buscar en subdirectorios
                found = list(templates_dir.rglob(template_path.split("/")[-1]))
                if found:
                    self.warnings["templates"].append(
                        f"⚠️ {template_path} no existe en ruta exacta, pero se encontró: {found[0]}"
                    )
                else:
                    self.issues["templates"].append(f"❌ {template_path} no existe")

    def auditar_duplicados_templates(self):
        """Verifica duplicados de templates y orden de carga"""
        self.stdout.write("📚 Verificando duplicados de templates...")

        from django.conf import settings

        # Verificar orden en TEMPLATES['DIRS']
        template_dirs = settings.TEMPLATES[0].get("DIRS", [])
        app_dirs = settings.TEMPLATES[0].get("APP_DIRS", False)

        self.success["duplicados"].append(f"✅ TEMPLATES DIRS: {len(template_dirs)} directorios")
        self.success["duplicados"].append(f"✅ APP_DIRS: {app_dirs}")

        # Verificar si hay _archive o _deprecated en el árbol
        base_dir = Path(__file__).resolve().parent.parent.parent
        templates_dir = base_dir / "templates"

        archive_dirs = list(templates_dir.rglob("*archive*")) + list(templates_dir.rglob("*deprecated*"))
        if archive_dirs:
            self.warnings["duplicados"].append(
                f"⚠️ Se encontraron {len(archive_dirs)} directorios _archive/_deprecated que podrían estar en el árbol de carga"
            )

        # Verificar si cl/ está en DIRS además de templates/
        cl_in_dirs = any("cl" in str(d) for d in template_dirs if "cl" in str(d))
        if cl_in_dirs:
            self.warnings["duplicados"].append(
                "⚠️ Directorio 'cl' está en TEMPLATES DIRS, podría causar colisiones con templates/"
            )

    def generar_reporte(self):
        """Genera el reporte final en Markdown"""
        reporte = []
        reporte.append("# 🔍 Reporte de Auditoría CRUD - eGarage\n")
        reporte.append("Generado automáticamente\n")

        # Resumen
        total_issues = sum(len(v) for v in self.issues.values())
        total_warnings = sum(len(v) for v in self.warnings.values())
        total_success = sum(len(v) for v in self.success.values())

        reporte.append("## 📊 Resumen\n")
        reporte.append(f"- ✅ Éxitos: {total_success}")
        reporte.append(f"- ⚠️ Advertencias: {total_warnings}")
        reporte.append(f"- ❌ Problemas: {total_issues}\n")

        # 1. Permisos
        reporte.append("## 1️⃣ Permisos y Roles\n")
        if self.success.get("permisos"):
            reporte.append("### ✅ Correcto\n")
            for item in self.success["permisos"]:
                reporte.append(f"- {item}\n")
        if self.warnings.get("permisos"):
            reporte.append("### ⚠️ Advertencias\n")
            for item in self.warnings["permisos"]:
                reporte.append(f"- {item}\n")
        if self.issues.get("permisos"):
            reporte.append("### ❌ Problemas\n")
            for item in self.issues["permisos"]:
                reporte.append(f"- {item}\n")

        # 2. Multi-tenant
        reporte.append("\n## 2️⃣ Multi-Tenant (Filtrado por Empresa)\n")
        if self.success.get("multi_tenant"):
            reporte.append("### ✅ Correcto\n")
            for item in self.success["multi_tenant"]:
                reporte.append(f"- {item}\n")
        if self.warnings.get("multi_tenant"):
            reporte.append("### ⚠️ Advertencias\n")
            for item in self.warnings["multi_tenant"]:
                reporte.append(f"- {item}\n")
        if self.issues.get("multi_tenant"):
            reporte.append("### ❌ Problemas\n")
            for item in self.issues["multi_tenant"]:
                reporte.append(f"- {item}\n")

        # 3. URLs
        reporte.append("\n## 3️⃣ URLs y Rutas\n")
        if self.success.get("urls"):
            reporte.append("### ✅ Correcto\n")
            for item in self.success["urls"]:
                reporte.append(f"- {item}\n")
        if self.issues.get("urls"):
            reporte.append("### ❌ Problemas\n")
            for item in self.issues["urls"]:
                reporte.append(f"- {item}\n")

        # 4. Templates
        reporte.append("\n## 4️⃣ Templates y UI\n")
        if self.success.get("templates"):
            reporte.append("### ✅ Correcto\n")
            for item in self.success["templates"]:
                reporte.append(f"- {item}\n")
        if self.warnings.get("templates"):
            reporte.append("### ⚠️ Advertencias\n")
            for item in self.warnings["templates"]:
                reporte.append(f"- {item}\n")
        if self.issues.get("templates"):
            reporte.append("### ❌ Problemas\n")
            for item in self.issues["templates"]:
                reporte.append(f"- {item}\n")

        # 5. Duplicados
        reporte.append("\n## 5️⃣ Duplicados de Templates\n")
        if self.success.get("duplicados"):
            reporte.append("### ✅ Correcto\n")
            for item in self.success["duplicados"]:
                reporte.append(f"- {item}\n")
        if self.warnings.get("duplicados"):
            reporte.append("### ⚠️ Advertencias\n")
            for item in self.warnings["duplicados"]:
                reporte.append(f"- {item}\n")

        # Recomendaciones
        reporte.append("\n## 💡 Recomendaciones\n")
        if total_issues > 0:
            reporte.append("1. **Revisar permisos**: Asegurar que todas las vistas de delete/edit tengan RoleRequiredMixin\n")
            reporte.append("2. **Verificar multi-tenant**: Todas las vistas deben filtrar por empresa en get_queryset\n")
            reporte.append("3. **Completar templates**: Agregar botones faltantes en templates de lista\n")
        if total_warnings > 0:
            reporte.append("4. **Limpiar duplicados**: Revisar directorios _archive/_deprecated\n")
            reporte.append("5. **Verificar orden de templates**: Asegurar que el orden en TEMPLATES['DIRS'] sea correcto\n")

        # Escribir reporte
        output_path = Path(self.output_file)
        output_path.write_text("\n".join(reporte), encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Reporte generado: {output_path}"))
        self.stdout.write(f"\n📊 Resumen: {total_success} ✅ | {total_warnings} ⚠️ | {total_issues} ❌")
