# -*- coding: utf-8 -*-
"""
Comando para corregir precios de GEORGE AUTO REPAIR a USD realistas.
Convierte todos los precios de pesos chilenos a dólares americanos apropiados.

Uso:
    python manage.py corregir_precios_usd --company "GEORGE AUTO REPAIR"
"""

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from taller.models import (Empresa, LineaOtroServicio, LineaRepuesto,
                           LineaServicio, Repuesto)
from taller.servicios.models import (CategoriaServicio, Servicio,
                                     SubcategoriaServicio)

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


class Command(BaseCommand):
    help = "Corrige precios de GEORGE AUTO REPAIR a USD realistas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company",
            type=str,
            default="GEORGE AUTO REPAIR",
            help="Nombre de la empresa a corregir",
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
            self.style.SUCCESS(f"🔧 Corrigiendo precios para: {empresa.nombre_taller}")
        )

        if empresa.pais != "US":
            self.stdout.write(
                self.style.WARNING(f"⚠️  Empresa no es de USA (país: {empresa.pais})")
            )

        # ==========================================
        # 1. CORREGIR PRECIOS DE REPUESTOS
        # ==========================================
        self.stdout.write("\n📦 Corrigiendo precios de repuestos...")

        # Definir precios realistas en USD para repuestos
        precios_repuestos = {
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

        repuestos_corregidos = 0
        for repuesto in Repuesto.objects.filter(empresa=empresa):
            # Buscar precio baseado en el nombre
            precio_compra = None
            precio_venta = None

            for nombre_patron, (min_precio, max_precio) in precios_repuestos.items():
                if nombre_patron.lower() in repuesto.nombre.lower():
                    precio_compra = Decimal(
                        str(RND.randint(int(min_precio * 0.6), int(min_precio * 0.8)))
                    )
                    precio_venta = Decimal(
                        str(RND.randint(int(min_precio), int(max_precio)))
                    )
                    break

            # Si no se encontró patrón, usar precios genéricos
            if not precio_compra:
                precio_compra = Decimal(str(RND.randint(15, 45)))
                precio_venta = Decimal(str(RND.randint(25, 85)))

            if (
                hasattr(repuesto, "precio_compra")
                and repuesto.precio_compra != precio_compra
            ):
                if not dry_run:
                    repuesto.precio_compra = precio_compra
                self.stdout.write(
                    f"  💰 {repuesto.nombre}: compra ${repuesto.precio_compra} → ${precio_compra}"
                )
                repuestos_corregidos += 1

            if (
                hasattr(repuesto, "precio_venta")
                and repuesto.precio_venta != precio_venta
            ):
                if not dry_run:
                    repuesto.precio_venta = precio_venta
                self.stdout.write(
                    f"  💰 {repuesto.nombre}: venta ${repuesto.precio_venta} → ${precio_venta}"
                )
                repuestos_corregidos += 1

            if not dry_run:
                repuesto.save()

        self.stdout.write(f"✅ Repuestos corregidos: {repuestos_corregidos}")

        # ==========================================
        # 2. CORREGIR PRECIOS DE SERVICIOS
        # ==========================================
        self.stdout.write("\n🔧 Corrigiendo precios de servicios...")

        # Definir precios realistas en USD para servicios
        precios_servicios = {
            "Cambio de aceite": (45, 75),
            "Alineación y balanceo": (65, 95),
            "Revisión de frenos": (35, 55),
            "Diagnóstico general": (25, 45),
            "Cambio de bujías": (55, 85),
            "Limpieza de inyectores": (75, 115),
            "Cambio de batería": (25, 45),
            "Ajuste de correas": (45, 75),
            "Revisión suspensión": (35, 65),
            "Cambio de filtro de aire": (25, 45),
        }

        servicios_corregidos = 0
        for servicio in Servicio.objects.filter(empresa=empresa):
            if hasattr(servicio, "precio_base"):
                # Buscar precio baseado en el nombre
                precio_base = None
                for nombre_patron, (
                    min_precio,
                    max_precio,
                ) in precios_servicios.items():
                    if nombre_patron.lower() in servicio.nombre.lower():
                        precio_base = Decimal(str(RND.randint(min_precio, max_precio)))
                        break

                # Si no se encontró patrón, usar precio genérico
                if not precio_base:
                    precio_base = Decimal(str(RND.randint(35, 85)))

                if servicio.precio_base != precio_base:
                    if not dry_run:
                        servicio.precio_base = precio_base
                    self.stdout.write(
                        f"  💰 {servicio.nombre}: ${servicio.precio_base} → ${precio_base}"
                    )
                    servicios_corregidos += 1

                if not dry_run:
                    servicio.save()

        self.stdout.write(f"✅ Servicios corregidos: {servicios_corregidos}")

        # ==========================================
        # 3. CORREGIR LÍNEAS DE REPUESTOS
        # ==========================================
        self.stdout.write("\n📋 Corrigiendo líneas de repuestos...")

        lineas_repuestos_corregidas = 0
        for linea in LineaRepuesto.objects.filter(documento__empresa=empresa):
            # Obtener precio del repuesto asociado
            if linea.repuesto and hasattr(linea.repuesto, "precio_venta"):
                nuevo_precio = linea.repuesto.precio_venta
            else:
                # Precio genérico si no hay repuesto asociado
                nuevo_precio = Decimal(str(RND.randint(25, 85)))

            if linea.precio_unitario != nuevo_precio:
                if not dry_run:
                    linea.precio_unitario = nuevo_precio
                self.stdout.write(
                    f"  💰 Línea repuesto {linea.nombre}: ${linea.precio_unitario} → ${nuevo_precio}"
                )
                lineas_repuestos_corregidas += 1

            if not dry_run:
                linea.save()

        self.stdout.write(
            f"✅ Líneas de repuestos corregidas: {lineas_repuestos_corregidas}"
        )

        # ==========================================
        # 4. CORREGIR LÍNEAS DE SERVICIOS
        # ==========================================
        self.stdout.write("\n🔧 Corrigiendo líneas de servicios...")

        lineas_servicios_corregidas = 0
        for linea in LineaServicio.objects.filter(documento__empresa=empresa):
            # Obtener precio del servicio asociado
            if linea.servicio and hasattr(linea.servicio, "precio_base"):
                nuevo_precio = linea.servicio.precio_base
            else:
                # Precio genérico si no hay servicio asociado
                nuevo_precio = Decimal(str(RND.randint(35, 95)))

            if linea.precio_unitario != nuevo_precio:
                if not dry_run:
                    linea.precio_unitario = nuevo_precio
                self.stdout.write(
                    f"  💰 Línea servicio {linea.nombre}: ${linea.precio_unitario} → ${nuevo_precio}"
                )
                lineas_servicios_corregidas += 1

            if not dry_run:
                linea.save()

        self.stdout.write(
            f"✅ Líneas de servicios corregidas: {lineas_servicios_corregidas}"
        )

        # ==========================================
        # 5. CORREGIR LÍNEAS DE OTROS SERVICIOS
        # ==========================================
        self.stdout.write("\n🔧 Corrigiendo líneas de otros servicios...")

        lineas_otros_corregidas = 0
        for linea in LineaOtroServicio.objects.filter(documento__empresa=empresa):
            # Precios realistas para servicios externos
            nuevo_costo = Decimal(str(RND.randint(20, 50)))
            nuevo_precio = nuevo_costo + Decimal(str(RND.randint(15, 40)))

            if linea.costo_interno != nuevo_costo:
                if not dry_run:
                    linea.costo_interno = nuevo_costo
                self.stdout.write(
                    f"  💰 {linea.nombre}: costo ${linea.costo_interno} → ${nuevo_costo}"
                )
                lineas_otros_corregidas += 1

            if linea.precio_cliente != nuevo_precio:
                if not dry_run:
                    linea.precio_cliente = nuevo_precio
                self.stdout.write(
                    f"  💰 {linea.nombre}: precio ${linea.precio_cliente} → ${nuevo_precio}"
                )
                lineas_otros_corregidas += 1

            if not dry_run:
                linea.save()

        self.stdout.write(
            f"✅ Líneas de otros servicios corregidas: {lineas_otros_corregidas}"
        )

        # ==========================================
        # RESUMEN
        # ==========================================
        total_corregidos = (
            repuestos_corregidos
            + servicios_corregidos
            + lineas_repuestos_corregidas
            + lineas_servicios_corregidas
            + lineas_otros_corregidas
        )

        self.stdout.write("\n" + "=" * 50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"🔍 MODO SIMULACIÓN: Se habrían corregido {total_corregidos} precios"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ CORRECCIÓN COMPLETADA: {total_corregidos} precios corregidos"
                )
            )
        self.stdout.write("=" * 50)
