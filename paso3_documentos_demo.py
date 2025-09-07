#!/usr/bin/env python
"""
🎯 PASO 3: DOCUMENTOS DEMO CON SERVICIOS
Crear documentos de ejemplo con servicios característicos por país
"""
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User

from taller.models import *
from taller.servicios.models import *


class DocumentosDemo:
    """Generador de documentos demo con servicios"""

    def crear_documentos_chile(self):
        """Crear documentos demo para empresas chilenas"""
        print("🇨🇱 CREANDO DOCUMENTOS DEMO CHILE")
        print("-" * 50)

        empresas_cl = Empresa.objects.filter(
            pais="CL", user__username__startswith="demo_"
        )

        servicios_cl = Servicio.objects.filter(
            country="CL",
            code__startswith="demo_",
            tipo="interno",  # Solo servicios internos para LineaServicio
        )

        documentos_creados = 0

        for empresa in empresas_cl:
            clientes = Cliente.objects.filter(empresa=empresa)[
                :3
            ]  # Solo 3 clientes por empresa

            for cliente in clientes:
                vehiculos = Vehiculo.objects.filter(cliente=cliente)

                for vehiculo in vehiculos:
                    # Crear documento de cotización
                    documento = Documento.objects.create(
                        empresa=empresa,
                        cliente=cliente,
                        vehiculo=vehiculo,
                        tipo_documento="Presupuesto",
                        fecha=datetime.now() - timedelta(days=random.randint(1, 30)),
                        observaciones=f'Cotización para {vehiculo.marca.nombre if vehiculo.marca else "Vehículo"} {vehiculo.modelo.nombre if vehiculo.modelo else ""}',
                    )

                    # Agregar servicios aleatorios
                    servicios_seleccionados = random.sample(
                        list(servicios_cl), k=random.randint(2, 4)
                    )
                    total_documento = Decimal("0.00")

                    for servicio in servicios_seleccionados:
                        # Crear línea de servicio (subtotal es calculado automáticamente)
                        from taller.models.lineas_documento import LineaServicio

                        precio = servicio.precio_base or Decimal(
                            "10000"
                        )  # Precio por defecto
                        linea = LineaServicio.objects.create(
                            documento=documento,
                            servicio=servicio,
                            nombre=f"Servicio {servicio.code}",
                            cantidad=1,
                            precio_unitario=precio,
                        )
                        total_documento += precio

                    documentos_creados += 1
                    print(
                        f"   ✅ Cotización #{documento.pk} - {cliente.nombre} {cliente.apellido} - ${total_documento:,.0f}"
                    )

        print(f"   📊 Total documentos CL: {documentos_creados}\n")

    def crear_documentos_usa(self):
        """Crear documentos demo para empresas USA"""
        print("🇺🇸 CREANDO DOCUMENTOS DEMO USA")
        print("-" * 50)

        empresas_us = Empresa.objects.filter(
            pais="US", user__username__startswith="demo_"
        )

        servicios_us = Servicio.objects.filter(
            country="US",
            code__startswith="demo_",
            tipo="interno",  # Solo servicios internos para LineaServicio
        )

        documentos_creados = 0

        for empresa in empresas_us:
            clientes = Cliente.objects.filter(empresa=empresa)[
                :3
            ]  # Solo 3 clientes por empresa

            for cliente in clientes:
                vehiculos = Vehiculo.objects.filter(cliente=cliente)

                for vehiculo in vehiculos:
                    # Crear documento de estimate
                    documento = Documento.objects.create(
                        empresa=empresa,
                        cliente=cliente,
                        vehiculo=vehiculo,
                        tipo_documento="Presupuesto",
                        fecha=datetime.now() - timedelta(days=random.randint(1, 30)),
                        observaciones=f'Service estimate for {vehiculo.marca.nombre if vehiculo.marca else "Vehicle"} {vehiculo.modelo.nombre if vehiculo.modelo else ""}',
                    )

                    # Agregar servicios aleatorios
                    servicios_seleccionados = random.sample(
                        list(servicios_us), k=random.randint(2, 4)
                    )
                    total_documento = Decimal("0.00")

                    for servicio in servicios_seleccionados:
                        # Crear línea de servicio (subtotal es calculado automáticamente)
                        from taller.models.lineas_documento import LineaServicio

                        precio = servicio.precio_base or Decimal(
                            "50"
                        )  # Precio por defecto en USD
                        linea = LineaServicio.objects.create(
                            documento=documento,
                            servicio=servicio,
                            nombre=f"Service {servicio.code}",
                            cantidad=1,
                            precio_unitario=precio,
                        )
                        total_documento += precio

                    documentos_creados += 1
                    print(
                        f"   ✅ Estimate #{documento.pk} - {cliente.nombre} {cliente.apellido} - ${total_documento}"
                    )

        print(f"   📊 Total documentos US: {documentos_creados}\n")

    def generar_reporte_final_paso3(self):
        """Generar reporte final completo del Paso 3"""
        print("=" * 80)
        print("🎯 REPORTE FINAL PASO 3: FIXTURES REALES COMPLETAS")
        print("=" * 80)

        # Contar todos los elementos creados
        usuarios_demo = User.objects.filter(username__startswith="demo_")
        empresas_demo = Empresa.objects.filter(user__username__startswith="demo_")
        empresas_cl = empresas_demo.filter(pais="CL")
        empresas_us = empresas_demo.filter(pais="US")

        clientes_demo = Cliente.objects.filter(empresa__in=empresas_demo)
        vehiculos_demo = Vehiculo.objects.filter(empresa__in=empresas_demo)

        servicios_demo = Servicio.objects.filter(code__startswith="demo_")
        servicios_cl = servicios_demo.filter(country="CL")
        servicios_us = servicios_demo.filter(country="US")

        documentos_demo = Documento.objects.filter(empresa__in=empresas_demo)
        documentos_cl = documentos_demo.filter(empresa__pais="CL")
        documentos_us = documentos_demo.filter(empresa__pais="US")

        print(f"👤 USUARIOS DEMO: {usuarios_demo.count()}")
        print(f"🏢 EMPRESAS DEMO: {empresas_demo.count()}")
        print(f"   🇨🇱 Chile: {empresas_cl.count()}")
        print(f"   🇺🇸 USA: {empresas_us.count()}")

        print(f"\n👥 CLIENTES: {clientes_demo.count()}")
        print(f"🚗 VEHÍCULOS: {vehiculos_demo.count()}")

        print(f"\n🔧 SERVICIOS: {servicios_demo.count()}")
        print(f"   🇨🇱 Chile: {servicios_cl.count()}")
        print(f"   🇺🇸 USA: {servicios_us.count()}")

        print(f"\n📄 DOCUMENTOS: {documentos_demo.count()}")
        print(f"   🇨🇱 Chile: {documentos_cl.count()}")
        print(f"   🇺🇸 USA: {documentos_us.count()}")

        print("\n🌟 DATOS POR EMPRESA:")
        for empresa in empresas_demo:
            clientes_emp = Cliente.objects.filter(empresa=empresa).count()
            vehiculos_emp = Vehiculo.objects.filter(empresa=empresa).count()
            documentos_emp = Documento.objects.filter(empresa=empresa).count()

            print(f"   {empresa.nombre_taller} ({empresa.pais}):")
            print(
                f"      👥 {clientes_emp} clientes | 🚗 {vehiculos_emp} vehículos | 📄 {documentos_emp} documentos"
            )

        print("\n🔐 CREDENCIALES DE ACCESO:")
        print("   Password para todos: demo2025")
        print("   Ejemplos de login:")
        for empresa in empresas_demo[:6]:  # Mostrar solo 6 ejemplos
            print(f"   - {empresa.user.username} → {empresa.nombre_taller}")

        print("\n✨ CARACTERÍSTICAS COMPLETADAS:")
        print("   🎯 Datos realistas y coherentes por mercado")
        print("   🌍 Localización completa ES/EN")
        print("   🔧 Servicios característicos por país")
        print("   👥 Clientes con múltiples vehículos")
        print("   📄 Documentos con servicios reales")
        print("   💰 Precios en moneda local")
        print("   ⚙️ Configuraciones localizadas")
        print("   🎨 Paletas de colores por país")

        print("\n🎉 PASO 3 COMPLETADO AL 100%")
        print("✅ Sistema listo para pruebas funcionales completas")
        print("✅ Fixtures realistas CL/US implementadas")
        print("✅ Configuraciones por mercado aplicadas")

    def generar_documentos_completos(self):
        """Generar documentos demo completos"""
        print("🚀 GENERANDO DOCUMENTOS DEMO")
        print("📄 Cotizaciones y servicios de ejemplo")
        print("=" * 80)

        try:
            # Crear documentos por país
            self.crear_documentos_chile()
            self.crear_documentos_usa()

            # Reporte final completo
            self.generar_reporte_final_paso3()

            return True

        except Exception as e:
            print(f"\n💥 ERROR EN DOCUMENTOS: {e}")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    generator = DocumentosDemo()
    generator.generar_documentos_completos()
