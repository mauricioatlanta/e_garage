"""
Management command para diagnosticar por qué el logo no aparece en los templates.
Ejecutar: python manage.py debug_company_logo [username]
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from taller.models.company_settings import CompanySettings
from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa
import os


class Command(BaseCommand):
    help = "Diagnostica por qué el logo no aparece en los templates"

    def add_arguments(self, parser):
        parser.add_argument(
            "username",
            nargs="?",
            type=str,
            help="Usuario específico a diagnosticar (opcional)",
        )

    def handle(self, *args, **options):
        username = options.get("username")

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔍 DIAGNÓSTICO DE LOGO - COMPANY_BRANDING"))
        self.stdout.write("=" * 80)

        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Usuario '{username}' no encontrado"))
                return
        else:
            # Buscar usuarios con CompanySettings
            users = User.objects.filter(company_settings__isnull=False).distinct()[:10]
            if not users.exists():
                self.stdout.write(
                    self.style.WARNING("⚠️  No se encontraron usuarios con CompanySettings")
                )
                return

        for user in users:
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(f"👤 Usuario: {user.username} (ID: {user.id})")
            self.stdout.write(f"{'='*80}")

            # 1. Verificar Empresa
            try:
                empresa = Empresa.objects.get(user=user)
                self.stdout.write(f"\n🏢 Empresa: {empresa.nombre_taller}")
                self.stdout.write(f"   País: {empresa.pais}")
            except Empresa.DoesNotExist:
                self.stdout.write(self.style.ERROR("❌ No tiene Empresa asociada"))
                continue

            # 2. Verificar CompanySettings (PRIORIDAD MÁXIMA)
            self.stdout.write(f"\n📋 CompanySettings (Prioridad Máxima):")
            try:
                company_settings = CompanySettings.objects.filter(user=user).first()
                if company_settings:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"   ✅ CompanySettings encontrado (ID: {company_settings.id})"
                        )
                    )
                    self.stdout.write(f"   Company Name: {company_settings.company_name}")

                    if company_settings.logo:
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Tiene logo configurado"))
                        try:
                            logo_url = company_settings.logo.url
                            self.stdout.write(f"   URL relativa: {logo_url}")

                            # Verificar archivo físico
                            if hasattr(company_settings.logo, "path"):
                                logo_path = company_settings.logo.path
                                self.stdout.write(f"   Ruta física: {logo_path}")
                                if os.path.exists(logo_path):
                                    file_size = os.path.getsize(logo_path) / 1024
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"   ✅ Archivo existe ({file_size:.2f} KB)"
                                        )
                                    )
                                else:
                                    self.stdout.write(
                                        self.style.ERROR(f"   ❌ Archivo NO existe físicamente")
                                    )

                            # Simular build_absolute_uri
                            # Nota: En el servidor real, esto se hace con request.build_absolute_uri()
                            if logo_url and not logo_url.startswith(("http://", "https://")):
                                # URL absoluta simulada (en producción sería con el dominio real)
                                absolute_url = f"https://www.egarage.cl{logo_url}"
                                self.stdout.write(f"   URL absoluta (simulada): {absolute_url}")
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"   ❌ Error obteniendo URL del logo: {e}")
                            )
                    else:
                        self.stdout.write(self.style.WARNING("   ⚠️  NO tiene logo configurado"))
                else:
                    self.stdout.write(self.style.WARNING("   ⚠️  CompanySettings NO EXISTE"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error: {e}"))

            # 3. Verificar ConfiguracionEmpresa (FALLBACK)
            self.stdout.write(f"\n📋 ConfiguracionEmpresa (Fallback):")
            try:
                config = ConfiguracionEmpresa.objects.get(empresa=empresa)
                if config.logo:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Tiene logo: {config.logo.url}"))
                else:
                    self.stdout.write(self.style.WARNING("   ⚠️  NO tiene logo"))
            except ConfiguracionEmpresa.DoesNotExist:
                self.stdout.write(self.style.WARNING("   ⚠️  ConfiguracionEmpresa NO EXISTE"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error: {e}"))

            # 4. Verificar Empresa.logo (Último fallback)
            self.stdout.write(f"\n📋 Empresa.logo (Último fallback):")
            if empresa.logo:
                self.stdout.write(self.style.SUCCESS(f"   ✅ Tiene logo: {empresa.logo.url}"))
            else:
                self.stdout.write(self.style.WARNING("   ⚠️  NO tiene logo"))

        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS("✅ DIAGNÓSTICO COMPLETADO"))
        self.stdout.write("=" * 80)
        self.stdout.write("\n💡 RECOMENDACIONES:")
        self.stdout.write("   1. Si CompanySettings NO EXISTE, crea uno desde Settings")
        self.stdout.write(
            "   2. Si CompanySettings existe pero NO tiene logo, sube un logo desde Settings"
        )
        self.stdout.write("   3. Si el archivo NO existe físicamente, vuelve a subir el logo")
        self.stdout.write("   4. Verifica los logs del servidor buscando '[COMPANY_BRANDING]'")
        self.stdout.write("   5. Reinicia el servidor después de subir el logo")
        self.stdout.write("\n")
