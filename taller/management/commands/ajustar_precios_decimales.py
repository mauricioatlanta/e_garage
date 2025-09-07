# -*- coding: utf-8 -*-
"""
Comando para ajustar precios de repuestos con decimales realistas en USD.
Convierte precios enteros a decimales apropiados para un taller automotriz.

Uso:
    python manage.py ajustar_precios_decimales --company "GEORGE AUTO REPAIR"
"""

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models import (Empresa, LineaOtroServicio, LineaRepuesto,
                           LineaServicio, Repuesto)
from taller.servicios.models import Servicio

RND = random.Random(42)


def get_empresa_by_name(company_name: str):
    """Obtiene la empresa por nombre"""
    try:
        return Empresa.objects.get(nombre_taller__iexact=company_name)
    except Empresa.DoesNotExist:
        try:
            return Empresa.objects.get(empresa__iexact=company_name)
        except Empresa.DoesNotExist:
            raise Empresa.DoesNotExist(
                f"No se encontró la Empresa con nombre '{company_name}'"
            )


def generar_precio_con_decimales(base_precio, variacion=0.15):
    """Genera un precio con decimales realistas"""
    # Convertir a float para cálculos
    precio_float = float(base_precio)

    # Aplicar variación aleatoria (±15% por defecto)
    variacion_factor = 1 + (RND.uniform(-variacion, variacion))
    precio_variado = precio_float * variacion_factor

    # Agregar decimales realistas (0.99, 0.95, 0.49, etc.)
    decimales_comunes = [
        0.99,
        0.95,
        0.89,
        0.79,
        0.69,
        0.59,
        0.49,
        0.39,
        0.29,
        0.19,
        0.09,
    ]
    decimal_elegido = RND.choice(decimales_comunes)

    # Redondear a la unidad y agregar decimal
    precio_entero = int(precio_variado)
    precio_final = precio_entero + decimal_elegido

    return Decimal(str(round(precio_final, 2)))


class Command(BaseCommand):
    help = "Ajusta precios de repuestos con decimales realistas en USD"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company",
            type=str,
            default="GEORGE AUTO REPAIR",
            help="Nombre de la empresa a ajustar",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Mostrar cambios sin aplicarlos"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        company_name = options["company"]
        dry_run = options["dry_run"]

        try:
            empresa = get_empresa_by_name(company_name)
        except Empresa.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"🔧 Ajustando precios con decimales para: {empresa.nombre_taller}"
            )
        )

        # ==========================================
        # 1. AJUSTAR PRECIOS DE REPUESTOS
        # ==========================================
        self.stdout.write("\n📦 Ajustando precios de repuestos con decimales...")

        # Definir precios base realistas en USD para repuestos
        precios_base_repuestos = {
            "Filtro de aceite": (8.99, 12.99),
            "Filtro de aire": (12.99, 18.99),
            "Pastillas de freno": (25.99, 45.99),
            "Batería 12V": (89.99, 149.99),
            "Amortiguador delantero": (45.99, 89.99),
            "Correa de distribución": (35.99, 65.99),
            "Bujía iridio": (12.99, 24.99),
            "Aceite sintético 5W-30": (28.99, 42.99),
            "Sensor de oxígeno": (45.99, 89.99),
            "Bobina de encendido": (35.99, 65.99),
            "Bomba de agua": (25.99, 45.99),
            "Termostato": (8.99, 15.99),
            "Alternador": (89.99, 159.99),
            "Radiador": (125.99, 225.99),
            "Filtro de combustible": (15.99, 28.99),
            "Kit embrague": (89.99, 159.99),
            "Disco de freno": (35.99, 65.99),
            "Lámpara H7": (8.99, 15.99),
            "Líquido frenos DOT4": (12.99, 18.99),
        }

        repuestos_ajustados = 0
        for repuesto in Repuesto.objects.filter(empresa=empresa):
            # Buscar precio baseado en el nombre
            precio_compra = None
            precio_venta = None

            for nombre_patron, (
                min_precio,
                max_precio,
            ) in precios_base_repuestos.items():
                if nombre_patron.lower() in repuesto.nombre.lower():
                    precio_compra = generar_precio_con_decimales(min_precio * 0.7)
                    precio_venta = generar_precio_con_decimales(
                        RND.uniform(min_precio, max_precio)
                    )
                    break

            # Si no se encontró patrón, usar precios genéricos
            if not precio_compra:
                precio_compra = generar_precio_con_decimales(RND.randint(15, 45))
                precio_venta = generar_precio_con_decimales(RND.randint(25, 85))

            if (
                hasattr(repuesto, "precio_compra")
                and repuesto.precio_compra != precio_compra
            ):
                if not dry_run:
                    repuesto.precio_compra = precio_compra
                self.stdout.write(
                    f"  💰 {repuesto.nombre}: compra ${repuesto.precio_compra} → ${precio_compra}"
                )
                repuestos_ajustados += 1

            if (
                hasattr(repuesto, "precio_venta")
                and repuesto.precio_venta != precio_venta
            ):
                if not dry_run:
                    repuesto.precio_venta = precio_venta
                self.stdout.write(
                    f"  💰 {repuesto.nombre}: venta ${repuesto.precio_venta} → ${precio_venta}"
                )
                repuestos_ajustados += 1

            if not dry_run:
                repuesto.save()

        self.stdout.write(f"✅ Repuestos ajustados: {repuestos_ajustados}")

        # ==========================================
        # 2. AJUSTAR PRECIOS DE SERVICIOS
        # ==========================================
        self.stdout.write("\n🔧 Ajustando precios de servicios con decimales...")

        # Definir precios base realistas en USD para servicios
        precios_base_servicios = {
            "Cambio de aceite": (45.99, 75.99),
            "Alineación y balanceo": (65.99, 95.99),
            "Revisión de frenos": (35.99, 55.99),
            "Diagnóstico general": (25.99, 45.99),
            "Cambio de bujías": (55.99, 85.99),
            "Limpieza de inyectores": (75.99, 115.99),
            "Cambio de batería": (25.99, 45.99),
            "Ajuste de correas": (45.99, 75.99),
            "Revisión suspensión": (35.99, 65.99),
            "Cambio de filtro de aire": (25.99, 45.99),
        }

        servicios_ajustados = 0
        for servicio in Servicio.objects.filter(empresa=empresa):
            if hasattr(servicio, "precio_base"):
                # Buscar precio baseado en el nombre
                precio_base = None
                for nombre_patron, (
                    min_precio,
                    max_precio,
                ) in precios_base_servicios.items():
                    if nombre_patron.lower() in servicio.nombre.lower():
                        precio_base = generar_precio_con_decimales(
                            RND.uniform(min_precio, max_precio)
                        )
                        break

                # Si no se encontró patrón, usar precio genérico
                if not precio_base:
                    precio_base = generar_precio_con_decimales(RND.randint(35, 85))

                if servicio.precio_base != precio_base:
                    if not dry_run:
                        servicio.precio_base = precio_base
                    self.stdout.write(
                        f"  💰 {servicio.nombre}: ${servicio.precio_base} → ${precio_base}"
                    )
                    servicios_ajustados += 1

                if not dry_run:
                    servicio.save()

        self.stdout.write(f"✅ Servicios ajustados: {servicios_ajustados}")

        # ==========================================
        # 3. AJUSTAR LÍNEAS DE REPUESTOS
        # ==========================================
        self.stdout.write("\n📋 Ajustando líneas de repuestos con decimales...")

        lineas_repuestos_ajustadas = 0
        for linea in LineaRepuesto.objects.filter(documento__empresa=empresa):
            # Obtener precio del repuesto asociado
            if linea.repuesto and hasattr(linea.repuesto, "precio_venta"):
                nuevo_precio = linea.repuesto.precio_venta
            else:
                # Precio genérico si no hay repuesto asociado
                nuevo_precio = generar_precio_con_decimales(RND.randint(25, 85))

            if linea.precio_unitario != nuevo_precio:
                if not dry_run:
                    linea.precio_unitario = nuevo_precio
                self.stdout.write(
                    f"  💰 Línea repuesto {linea.nombre}: ${linea.precio_unitario} → ${nuevo_precio}"
                )
                lineas_repuestos_ajustadas += 1

            if not dry_run:
                linea.save()

        self.stdout.write(
            f"✅ Líneas de repuestos ajustadas: {lineas_repuestos_ajustadas}"
        )

        # ==========================================
        # 4. AJUSTAR LÍNEAS DE SERVICIOS
        # ==========================================
        self.stdout.write("\n🔧 Ajustando líneas de servicios con decimales...")

        lineas_servicios_ajustadas = 0
        for linea in LineaServicio.objects.filter(documento__empresa=empresa):
            # Obtener precio del servicio asociado
            if linea.servicio and hasattr(linea.servicio, "precio_base"):
                nuevo_precio = linea.servicio.precio_base
            else:
                # Precio genérico si no hay servicio asociado
                nuevo_precio = generar_precio_con_decimales(RND.randint(35, 95))

            if linea.precio_unitario != nuevo_precio:
                if not dry_run:
                    linea.precio_unitario = nuevo_precio
                self.stdout.write(
                    f"  💰 Línea servicio {linea.nombre}: ${linea.precio_unitario} → ${nuevo_precio}"
                )
                lineas_servicios_ajustadas += 1

            if not dry_run:
                linea.save()

        self.stdout.write(
            f"✅ Líneas de servicios ajustadas: {lineas_servicios_ajustadas}"
        )

        # ==========================================
        # 5. AJUSTAR LÍNEAS DE OTROS SERVICIOS
        # ==========================================
        self.stdout.write("\n🔧 Ajustando líneas de otros servicios con decimales...")

        lineas_otros_ajustadas = 0
        for linea in LineaOtroServicio.objects.filter(documento__empresa=empresa):
            # Precios realistas para servicios externos con decimales
            nuevo_costo = generar_precio_con_decimales(RND.randint(20, 50))
            nuevo_precio = nuevo_costo + generar_precio_con_decimales(
                RND.randint(15, 40)
            )

            if linea.costo_interno != nuevo_costo:
                if not dry_run:
                    linea.costo_interno = nuevo_costo
                self.stdout.write(
                    f"  💰 {linea.nombre}: costo ${linea.costo_interno} → ${nuevo_costo}"
                )
                lineas_otros_ajustadas += 1

            if linea.precio_cliente != nuevo_precio:
                if not dry_run:
                    linea.precio_cliente = nuevo_precio
                self.stdout.write(
                    f"  💰 {linea.nombre}: precio ${linea.precio_cliente} → ${nuevo_precio}"
                )
                lineas_otros_ajustadas += 1

            if not dry_run:
                linea.save()

        self.stdout.write(
            f"✅ Líneas de otros servicios ajustadas: {lineas_otros_ajustadas}"
        )

        # ==========================================
        # RESUMEN
        # ==========================================
        total_ajustados = (
            repuestos_ajustados
            + servicios_ajustados
            + lineas_repuestos_ajustadas
            + lineas_servicios_ajustadas
            + lineas_otros_ajustadas
        )

        self.stdout.write("\n" + "=" * 50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"🔍 MODO SIMULACIÓN: Se habrían ajustado {total_ajustados} precios con decimales"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ AJUSTE COMPLETADO: {total_ajustados} precios ajustados con decimales"
                )
            )
        self.stdout.write("=" * 50)
