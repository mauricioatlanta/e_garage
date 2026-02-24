"""
Management command para verificar logos en ConfiguracionEmpresa.
Útil cuando CompanySettings no existe en el servidor.
"""

from django.core.management.base import BaseCommand
from taller.models import ConfiguracionEmpresa
import os


class Command(BaseCommand):
    help = "Verifica logos en ConfiguracionEmpresa"

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔍 DIAGNÓSTICO DE LOGOS EN ConfiguracionEmpresa"))
        self.stdout.write("=" * 80)

        configs = ConfiguracionEmpresa.objects.all()
        
        if not configs.exists():
            self.stdout.write(self.style.WARNING("\n⚠️  No hay ConfiguracionEmpresa registrados."))
            return
        
        self.stdout.write(f"\n📊 Total de ConfiguracionEmpresa: {configs.count()}\n")

        for config in configs:
            self.stdout.write(f"\n{'='*60}")
            empresa = config.empresa
            if empresa:
                self.stdout.write(f"🏢 Empresa: {empresa.nombre_taller}")
                self.stdout.write(f"👤 Usuario: {empresa.user.username if empresa.user else 'N/A'}")
                self.stdout.write(f"🌍 País: {empresa.pais}")
            else:
                self.stdout.write("⚠️  No tiene Empresa asociada")
            self.stdout.write(f"{'='*60}")
            
            if config.logo:
                self.stdout.write(self.style.SUCCESS(f"✅ Tiene logo configurado"))
                try:
                    logo_url = config.logo.url
                    self.stdout.write(f"   URL relativa: {logo_url}")
                    
                    # Verificar archivo físico
                    if hasattr(config.logo, 'path'):
                        logo_path = config.logo.path
                        self.stdout.write(f"   Ruta física: {logo_path}")
                        if os.path.exists(logo_path):
                            file_size = os.path.getsize(logo_path) / 1024
                            self.stdout.write(self.style.SUCCESS(f"   ✅ Archivo existe ({file_size:.2f} KB)"))
                        else:
                            self.stdout.write(self.style.ERROR("   ❌ Archivo NO existe físicamente"))
                    
                    # Simular URL absoluta
                    if logo_url and not logo_url.startswith(('http://', 'https://')):
                        absolute_url = f"https://www.egarage.cl{logo_url}"
                        self.stdout.write(f"   URL absoluta (simulada): {absolute_url}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ❌ Error obteniendo URL: {e}"))
            else:
                self.stdout.write(self.style.WARNING("❌ NO tiene logo configurado"))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ DIAGNÓSTICO COMPLETADO"))
        self.stdout.write("=" * 80)
        self.stdout.write("\n")







