"""
Management command para verificar logos existentes en ConfiguracionEmpresa y Empresa.
"""

from django.core.management.base import BaseCommand
from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.models.company_settings import CompanySettings


class Command(BaseCommand):
    help = "Verifica logos existentes en todas las tablas"

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔍 VERIFICACIÓN DE LOGOS EN TODAS LAS TABLAS"))
        self.stdout.write("=" * 80)

        # 1. CompanySettings
        self.stdout.write(f"\n📊 CompanySettings: {CompanySettings.objects.count()} registros")
        for cs in CompanySettings.objects.all():
            self.stdout.write(f"  User: {cs.user.username}, Company: {cs.company_name}")
            if cs.logo:
                self.stdout.write(f"    ✅ Logo: {cs.logo.url}")

        # 2. ConfiguracionEmpresa
        self.stdout.write(f"\n📊 ConfiguracionEmpresa: {ConfiguracionEmpresa.objects.count()} registros")
        for conf in ConfiguracionEmpresa.objects.all():
            empresa = conf.empresa
            self.stdout.write(f"  Empresa: {empresa.nombre_taller}, User: {empresa.user.username}")
            if conf.logo:
                try:
                    logo_url = conf.logo.url
                    self.stdout.write(self.style.SUCCESS(f"    ✅ Logo: {logo_url}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    ❌ Error obteniendo URL: {e}"))
            else:
                self.stdout.write("    ❌ No tiene logo")

        # 3. Empresa directamente
        self.stdout.write(f"\n📊 Empresa (directo): {Empresa.objects.count()} registros")
        for empresa in Empresa.objects.all():
            if hasattr(empresa, 'logo') and empresa.logo:
                try:
                    logo_url = empresa.logo.url
                    self.stdout.write(f"  Empresa: {empresa.nombre_taller}, User: {empresa.user.username}")
                    self.stdout.write(self.style.SUCCESS(f"    ✅ Logo: {logo_url}"))
                except Exception as e:
                    pass

        self.stdout.write("\n" + "=" * 80)







