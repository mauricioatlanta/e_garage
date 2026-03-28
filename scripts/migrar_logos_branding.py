#!/usr/bin/env python
"""
Script para migrar logos de Empresa a ConfiguracionEmpresa
y sincronizar los dos sistemas de branding
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()


from django.core.files.base import ContentFile

from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa


def migrar_logos_empresa_a_configuracion():
    print("🔄 MIGRANDO LOGOS DE EMPRESA A CONFIGURACION_EMPRESA")
    print("=" * 60)

    empresas_con_logo = Empresa.objects.exclude(logo__isnull=True).exclude(logo="")
    print(f"📊 Empresas con logo en modelo Empresa: {empresas_con_logo.count()}")

    migrados = 0
    errores = 0

    for empresa in empresas_con_logo:
        print(f"\n🏢 Procesando: {empresa.nombre_taller}")
        print(f"   Logo actual: {empresa.logo}")

        try:
            # Obtener o crear ConfiguracionEmpresa
            config, created = ConfiguracionEmpresa.objects.get_or_create(
                empresa=empresa,
                defaults={
                    "nombre_publico": empresa.nombre_taller,
                    "moneda": "USD" if empresa.pais == "US" else "CLP",
                    "sales_tax_rate": 0,
                },
            )

            if created:
                print("   ✅ ConfiguracionEmpresa creada")
            else:
                print("   ℹ️ ConfiguracionEmpresa ya existía")

            # Migrar logo si no existe en configuración
            if empresa.logo and not config.logo:
                print("   🔄 Migrando logo...")

                # Verificar que el archivo físico existe
                if empresa.logo.storage.exists(empresa.logo.name):
                    # Leer el archivo
                    with empresa.logo.open("rb") as f:
                        logo_content = f.read()

                    # Generar nuevo nombre de archivo
                    original_name = os.path.basename(empresa.logo.name)
                    new_name = f"logos/{original_name}"

                    # Crear el archivo en ConfiguracionEmpresa
                    config.logo.save(original_name, ContentFile(logo_content), save=False)
                    config.save()

                    print(f"   ✅ Logo migrado a: {config.logo.url}")
                    migrados += 1
                else:
                    print(f"   ❌ Archivo físico no existe: {empresa.logo.name}")
                    errores += 1
            elif config.logo:
                print(f"   ✅ Logo ya existe en ConfiguracionEmpresa: {config.logo.url}")
            else:
                print("   ⚠️ No hay logo para migrar")

        except Exception as e:
            print(f"   ❌ Error migrando {empresa.nombre_taller}: {e}")
            errores += 1

    print("\n📊 RESUMEN:")
    print(f"   ✅ Logos migrados: {migrados}")
    print(f"   ❌ Errores: {errores}")


def sincronizar_nombres_publicos():
    print("\n🔄 SINCRONIZANDO NOMBRES PÚBLICOS")
    print("=" * 40)

    configs = ConfiguracionEmpresa.objects.select_related("empresa").all()
    actualizados = 0

    for config in configs:
        if not config.nombre_publico and config.empresa.nombre_taller:
            config.nombre_publico = config.empresa.nombre_taller
            config.save()
            print(f"   ✅ {config.empresa.nombre_taller}: nombre_publico actualizado")
            actualizados += 1

    print(f"   📊 Nombres actualizados: {actualizados}")


def verificar_estado_final():
    print("\n🔍 VERIFICACIÓN FINAL")
    print("=" * 30)

    configs = ConfiguracionEmpresa.objects.select_related("empresa").all()
    print(f"📊 Total configuraciones: {configs.count()}")

    configs_con_logo = configs.exclude(logo__isnull=True).exclude(logo="")
    print(f"📷 Configuraciones con logo: {configs_con_logo.count()}")

    for config in configs_con_logo:
        print(f"   ✅ {config.empresa.nombre_taller}: {config.logo.url}")


if __name__ == "__main__":
    migrar_logos_empresa_a_configuracion()
    sincronizar_nombres_publicos()
    verificar_estado_final()

    print("\n🎯 MIGRACIÓN COMPLETADA")
    print("=" * 30)
    print("Ahora los context processors deberían mostrar los logos correctamente.")
    print("Usa la vista de configuración en /taller/settings/editar/ para subir nuevos logos.")
