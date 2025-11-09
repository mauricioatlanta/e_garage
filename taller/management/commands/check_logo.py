"""Management command para verificar y diagnosticar el logo de la empresa."""

import os

from django.core.cache import cache
from django.core.management.base import BaseCommand

from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa


class Command(BaseCommand):
    help = "Verifica y diagnostica el logo de las empresas"

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔍 DIAGNÓSTICO DE LOGOS DE EMPRESAS"))
        self.stdout.write("=" * 80)

        # Obtener todas las empresas
        empresas = Empresa.objects.all()

        if not empresas.exists():
            self.stdout.write(
                self.style.WARNING("\n⚠️  No hay empresas registradas en el sistema.")
            )
        else:
            self.stdout.write(f"\n📊 Total de empresas: {empresas.count()}\n")

            for empresa in empresas:
                self.stdout.write(f"\n{'='*60}")
                self.stdout.write(f"🏢 Empresa: {empresa.nombre_taller}")
                self.stdout.write(f"👤 Usuario: {empresa.user.username}")
                self.stdout.write(f"🌍 País: {empresa.pais}")
                self.stdout.write(f"{'='*60}")

                # Verificar logo en Empresa
                if empresa.logo:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Logo en Empresa: {empresa.logo.url}")
                    )
                    self.stdout.write(f"   Ruta del archivo: {empresa.logo.path}")
                    # Verificar si el archivo existe
                    if os.path.exists(empresa.logo.path):
                        self.stdout.write(
                            self.style.SUCCESS("   ✅ Archivo existe físicamente")
                        )
                        file_size = os.path.getsize(empresa.logo.path) / 1024  # KB
                        self.stdout.write(f"   📦 Tamaño: {file_size:.2f} KB")
                    else:
                        self.stdout.write(
                            self.style.ERROR("   ❌ Archivo NO existe físicamente")
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR("❌ Logo en Empresa: NO CONFIGURADO")
                    )

                # Verificar ConfiguracionEmpresa
                try:
                    config = ConfiguracionEmpresa.objects.get(empresa=empresa)
                    if config.logo:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Logo en ConfiguracionEmpresa: {config.logo.url}"
                            )
                        )
                        self.stdout.write(f"   Ruta del archivo: {config.logo.path}")
                        if os.path.exists(config.logo.path):
                            self.stdout.write(
                                self.style.SUCCESS("   ✅ Archivo existe físicamente")
                            )
                            file_size = os.path.getsize(config.logo.path) / 1024
                            self.stdout.write(f"   📦 Tamaño: {file_size:.2f} KB")
                        else:
                            self.stdout.write(
                                self.style.ERROR("   ❌ Archivo NO existe físicamente")
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                "❌ Logo en ConfiguracionEmpresa: NO CONFIGURADO"
                            )
                        )
                except ConfiguracionEmpresa.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING("⚠️  ConfiguracionEmpresa: NO EXISTE")
                    )

                # Verificar caché
                cache_key = f"company_branding_{empresa.user.id}"
                cached_data = cache.get(cache_key)
                if cached_data:
                    self.stdout.write("\n📦 Datos en caché:")
                    self.stdout.write(
                        f"   - company_name: {cached_data.get('company_name', 'N/A')}"
                    )
                    self.stdout.write(
                        f"   - company_logo_url: {cached_data.get('company_logo_url', 'N/A')}"
                    )
                    self.stdout.write(
                        f"   - primary_color: {cached_data.get('primary_color', 'N/A')}"
                    )
                else:
                    self.stdout.write("\n📦 Caché: NO HAY DATOS EN CACHÉ")

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(
            self.style.SUCCESS("🔄 LIMPIANDO CACHÉ DE TODAS LAS EMPRESAS...")
        )
        self.stdout.write("=" * 80)

        for empresa in empresas:
            cache_key = f"company_branding_{empresa.user.id}"
            cache.delete(cache_key)
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Caché limpiado para: {empresa.nombre_taller} (user_id: {empresa.user.id})"
                )
            )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ DIAGNÓSTICO COMPLETADO"))
        self.stdout.write("=" * 80)
        self.stdout.write("\n💡 RECOMENDACIONES:")
        self.stdout.write(
            "   1. Si el logo NO está configurado, ve a Settings y sube un logo"
        )
        self.stdout.write(
            "   2. Si el archivo NO existe físicamente, vuelve a subir el logo"
        )
        self.stdout.write(
            "   3. Después de subir el logo, recarga la página del dashboard"
        )
        self.stdout.write(
            "   4. El caché ha sido limpiado, los cambios deberían verse inmediatamente"
        )
        self.stdout.write("\n")
