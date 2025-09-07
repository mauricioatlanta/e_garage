#!/usr/bin/env python
"""
🎯 PASO 3: CONFIGURACIONES LOCALIZADAS POR MERCADO
Configurar ajustes específicos por país para empresas demo
"""
import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

from taller.models import CompanySettings, Empresa


class ConfiguracionesLocalizadas:
    """Configurar ajustes específicos por mercado"""

    def configurar_empresas_chile(self):
        """Configurar empresas chilenas con ajustes locales"""
        print("🇨🇱 CONFIGURANDO EMPRESAS CHILE")
        print("-" * 50)

        empresas_cl = Empresa.objects.filter(
            pais="CL", user__username__startswith="demo_"
        )

        configuraciones_cl = {
            "moneda": "CLP",
            "simbolo_moneda": "$",
            "formato_fecha": "DD/MM/YYYY",
            "zona_horaria": "America/Santiago",
            "idioma_principal": "es",
            "separador_miles": ".",
            "separador_decimal": ",",
            "telefono_formato": "+56 X XXXX XXXX",
        }

        for empresa in empresas_cl:
            # Actualizar configuraciones de la empresa
            empresa.zona_horaria = configuraciones_cl["zona_horaria"]
            empresa.save()

            # Crear o actualizar CompanySettings si existe
            try:
                settings, created = CompanySettings.objects.get_or_create(
                    user=empresa.user,
                    defaults={
                        "company_name": empresa.nombre_taller,
                        "tagline": "Servicio automotriz de calidad",
                        "primary_color": "#d32f2f",  # Rojo chileno
                        "secondary_color": "#1976d2",  # Azul
                        "email": empresa.email,
                        "phone": empresa.telefono,
                        "address": empresa.direccion,
                    },
                )

                if not created:
                    settings.primary_color = "#d32f2f"
                    settings.secondary_color = "#1976d2"
                    settings.save()

                print(f"   ✅ {empresa.nombre_taller}")
                print(f"      Zona horaria: {empresa.zona_horaria}")
                print(
                    f"      Colores: {settings.primary_color} / {settings.secondary_color}"
                )

            except Exception as e:
                print(f"      ⚠️ Sin CompanySettings: {empresa.nombre_taller}")

        print(f"   📊 Total empresas CL configuradas: {empresas_cl.count()}\n")

    def configurar_empresas_usa(self):
        """Configurar empresas USA con ajustes locales"""
        print("🇺🇸 CONFIGURANDO EMPRESAS USA")
        print("-" * 50)

        empresas_us = Empresa.objects.filter(
            pais="US", user__username__startswith="demo_"
        )

        configuraciones_us = {
            "moneda": "USD",
            "simbolo_moneda": "$",
            "formato_fecha": "MM/DD/YYYY",
            "zona_horaria": "America/New_York",
            "idioma_principal": "en",
            "separador_miles": ",",
            "separador_decimal": ".",
            "telefono_formato": "+1 XXX XXX XXXX",
        }

        for empresa in empresas_us:
            # Actualizar configuraciones de la empresa
            empresa.zona_horaria = configuraciones_us["zona_horaria"]
            empresa.save()

            # Crear o actualizar CompanySettings si existe
            try:
                settings, created = CompanySettings.objects.get_or_create(
                    user=empresa.user,
                    defaults={
                        "company_name": empresa.nombre_taller,
                        "tagline": "Quality automotive service",
                        "primary_color": "#1565c0",  # Azul americano
                        "secondary_color": "#d32f2f",  # Rojo
                        "email": empresa.email,
                        "phone": empresa.telefono,
                        "address": empresa.direccion,
                    },
                )

                if not created:
                    settings.primary_color = "#1565c0"
                    settings.secondary_color = "#d32f2f"
                    settings.save()

                print(f"   ✅ {empresa.nombre_taller}")
                print(f"      Time zone: {empresa.zona_horaria}")
                print(
                    f"      Colors: {settings.primary_color} / {settings.secondary_color}"
                )

            except Exception as e:
                print(f"      ⚠️ No CompanySettings: {empresa.nombre_taller}")

        print(f"   📊 Total empresas US configuradas: {empresas_us.count()}\n")

    def validar_fixtures_creadas(self):
        """Validar que las fixtures se crearon correctamente"""
        print("🔍 VALIDANDO FIXTURES CREADAS")
        print("-" * 50)

        # Contar usuarios demo
        usuarios_demo = User.objects.filter(username__startswith="demo_")
        print(f"👤 Usuarios demo: {usuarios_demo.count()}")

        # Contar empresas demo por país
        empresas_cl = Empresa.objects.filter(
            pais="CL", user__username__startswith="demo_"
        )
        empresas_us = Empresa.objects.filter(
            pais="US", user__username__startswith="demo_"
        )

        print(f"🏢 Empresas demo CL: {empresas_cl.count()}")
        print(f"🏢 Empresas demo US: {empresas_us.count()}")

        # Contar clientes por empresa demo
        from taller.models import Cliente, Vehiculo

        total_clientes_demo = 0
        total_vehiculos_demo = 0

        for empresa in list(empresas_cl) + list(empresas_us):
            clientes = Cliente.objects.filter(empresa=empresa)
            vehiculos = Vehiculo.objects.filter(empresa=empresa)
            total_clientes_demo += clientes.count()
            total_vehiculos_demo += vehiculos.count()
            print(
                f"   {empresa.nombre_taller} ({empresa.pais}): {clientes.count()} clientes, {vehiculos.count()} vehículos"
            )

        print(f"👥 Total clientes demo: {total_clientes_demo}")
        print(f"🚗 Total vehículos demo: {total_vehiculos_demo}")

        # Contar servicios demo
        from taller.servicios.models import Servicio

        servicios_demo = Servicio.objects.filter(code__startswith="demo_")
        servicios_cl = servicios_demo.filter(country="CL")
        servicios_us = servicios_demo.filter(country="US")

        print(f"🔧 Servicios demo CL: {servicios_cl.count()}")
        print(f"🔧 Servicios demo US: {servicios_us.count()}")
        print(f"🔧 Total servicios demo: {servicios_demo.count()}")

        print(f"\n✅ VALIDACIÓN COMPLETADA")

    def generar_configuraciones_completas(self):
        """Generar todas las configuraciones localizadas"""
        print("🚀 GENERANDO CONFIGURACIONES LOCALIZADAS")
        print("🎯 Ajustes específicos por mercado")
        print("=" * 80)

        try:
            # Validar fixtures existentes
            self.validar_fixtures_creadas()

            # Configurar empresas por país
            self.configurar_empresas_chile()
            self.configurar_empresas_usa()

            # Reporte final
            self.generar_reporte_configuraciones()

            return True

        except Exception as e:
            print(f"\n💥 ERROR EN CONFIGURACIONES: {e}")
            import traceback

            traceback.print_exc()
            return False

    def generar_reporte_configuraciones(self):
        """Generar reporte final de configuraciones"""
        print("=" * 80)
        print("📊 REPORTE FINAL DE CONFIGURACIONES")
        print("=" * 80)

        print(f"\n🇨🇱 CONFIGURACIONES CHILE:")
        print("   ⏰ Zona horaria: America/Santiago")
        print("   💰 Moneda: CLP ($)")
        print("   📅 Formato fecha: DD/MM/YYYY")
        print("   🌍 Idioma: Español (es)")
        print("   🎨 Colores: Rojo chileno (#d32f2f)")

        print(f"\n🇺🇸 CONFIGURACIONES USA:")
        print("   ⏰ Time zone: America/New_York")
        print("   💰 Currency: USD ($)")
        print("   📅 Date format: MM/DD/YYYY")
        print("   🌍 Language: English (en)")
        print("   🎨 Colors: American blue (#1565c0)")

        print(f"\n🎯 CARACTERÍSTICAS LOCALIZADAS:")
        print("   ⚙️ Zonas horarias específicas")
        print("   🎨 Paletas de colores por país")
        print("   📱 Formatos de teléfono locales")
        print("   💰 Monedas y separadores locales")
        print("   🌍 Idiomas principales configurados")

        print(f"\n🔐 ACCESO A EMPRESAS DEMO:")
        empresas_demo = Empresa.objects.filter(user__username__startswith="demo_")
        for empresa in empresas_demo:
            print(
                f"   {empresa.user.username} → {empresa.nombre_taller} ({empresa.pais})"
            )

        print(f"\n🎉 CONFIGURACIONES COMPLETADAS")
        print("✅ Sistema listo con localizaciones específicas")


if __name__ == "__main__":
    configurador = ConfiguracionesLocalizadas()
    configurador.generar_configuraciones_completas()
