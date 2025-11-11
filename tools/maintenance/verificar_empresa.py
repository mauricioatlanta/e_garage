#!/usr/bin/env python
"""
Script para verificar rápidamente el estado de la empresa en la base de datos
Uso: python verificar_empresa.py
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models import ConfiguracionEmpresa, Empresa


def verificar_empresa():
    print("🔍 VERIFICANDO ESTADO DE EMPRESA EN BD")
    print("=" * 50)

    # Obtener todas las empresas
    empresas = Empresa.objects.all()
    print(f"📊 Total empresas: {empresas.count()}")

    for empresa in empresas:
        print(f"\n🏢 EMPRESA ID: {empresa.id}")
        print(f"   Usuario: {empresa.user}")
        print(f"   País: {getattr(empresa, 'pais', 'N/A')}")

        # Obtener configuración
        try:
            config = ConfiguracionEmpresa.objects.get(empresa=empresa)
            print("   ✅ Configuración encontrada")
            print(f"   📍 Dirección: {config.direccion or 'Vacía'}")
            print(f"   📞 Teléfono: {config.telefono or 'Vacío'}")
            print(f"   📧 Email: {config.email_contacto or 'Vacío'}")
            print(f"   🌐 Sitio web: {config.sitio_web or 'Vacío'}")
            print(f"   💰 Moneda: {config.moneda or 'Vacía'}")
            print(f"   🧾 Tasa impuesto: {config.tasa_impuesto or 'Vacía'}")
            print(f"   🎯 Aplicar impuesto por defecto: {config.aplicar_impuesto_por_defecto}")
            print(f"   🎨 Color marca: {getattr(config, 'brand_color', 'N/A')}")
            print(f"   👥 Dividir por técnico: {getattr(config, 'dividir_por_tecnico', 'N/A')}")

        except ConfiguracionEmpresa.DoesNotExist:
            print("   ❌ NO HAY CONFIGURACIÓN")
        except Exception as e:
            print(f"   ⚠️ ERROR: {e}")

    print("\n" + "=" * 50)
    print("✅ VERIFICACIÓN COMPLETADA")


if __name__ == "__main__":
    verificar_empresa()
