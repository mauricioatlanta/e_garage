# -*- coding: utf-8 -*-
"""
Comando para verificar que los precios de GEORGE AUTO REPAIR están en USD realistas.
Muestra un resumen de los precios actuales para confirmar que están correctos.

Uso:
    python manage.py verificar_precios_usd --company "GEORGE AUTO REPAIR"
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Avg, Max, Min

from taller.models import (
    Empresa,
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
    Repuesto,
)
from taller.servicios.models import Servicio


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
    help = 'Verifica que los precios de GEORGE AUTO REPAIR están en USD realistas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            default="GEORGE AUTO REPAIR",
            help='Nombre de la empresa a verificar'
        )

    def handle(self, *args, **options):
        company_name = options['company']
        
        try:
            empresa = get_empresa_by_name(company_name)
        except Empresa.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'🔍 Verificando precios para: {empresa.nombre_taller}')
        )
        
        # ==========================================
        # 1. VERIFICAR PRECIOS DE REPUESTOS
        # ==========================================
        self.stdout.write('\n📦 Precios de repuestos:')
        
        repuestos = Repuesto.objects.filter(empresa=empresa)
        if repuestos.exists():
            if hasattr(repuestos.first(), 'precio_compra'):
                stats_compra = repuestos.aggregate(
                    min_compra=Min('precio_compra'),
                    max_compra=Max('precio_compra'),
                    avg_compra=Avg('precio_compra')
                )
                self.stdout.write(f'  💰 Compra: ${stats_compra["min_compra"]:.2f} - ${stats_compra["max_compra"]:.2f} (promedio: ${stats_compra["avg_compra"]:.2f})')
            
            if hasattr(repuestos.first(), 'precio_venta'):
                stats_venta = repuestos.aggregate(
                    min_venta=Min('precio_venta'),
                    max_venta=Max('precio_venta'),
                    avg_venta=Avg('precio_venta')
                )
                self.stdout.write(f'  💰 Venta: ${stats_venta["min_venta"]:.2f} - ${stats_venta["max_venta"]:.2f} (promedio: ${stats_venta["avg_venta"]:.2f})')
            
            # Mostrar algunos ejemplos
            self.stdout.write('  📋 Ejemplos:')
            for repuesto in repuestos[:5]:
                precio_venta = getattr(repuesto, 'precio_venta', 'N/A')
                self.stdout.write(f'    • {repuesto.nombre}: ${precio_venta}')
        else:
            self.stdout.write('  ⚠️  No hay repuestos registrados')
        
        # ==========================================
        # 2. VERIFICAR PRECIOS DE SERVICIOS
        # ==========================================
        self.stdout.write('\n🔧 Precios de servicios:')
        
        servicios = Servicio.objects.filter(empresa=empresa)
        if servicios.exists():
            if hasattr(servicios.first(), 'precio_base'):
                stats_servicios = servicios.aggregate(
                    min_precio=Min('precio_base'),
                    max_precio=Max('precio_base'),
                    avg_precio=Avg('precio_base')
                )
                self.stdout.write(f'  💰 Base: ${stats_servicios["min_precio"]:.2f} - ${stats_servicios["max_precio"]:.2f} (promedio: ${stats_servicios["avg_precio"]:.2f})')
            
            # Mostrar algunos ejemplos
            self.stdout.write('  📋 Ejemplos:')
            for servicio in servicios[:5]:
                precio_base = getattr(servicio, 'precio_base', 'N/A')
                self.stdout.write(f'    • {servicio.nombre}: ${precio_base}')
        else:
            self.stdout.write('  ⚠️  No hay servicios registrados')
        
        # ==========================================
        # 3. VERIFICAR LÍNEAS DE REPUESTOS
        # ==========================================
        self.stdout.write('\n📋 Líneas de repuestos en documentos:')
        
        lineas_repuestos = LineaRepuesto.objects.filter(documento__empresa=empresa)
        if lineas_repuestos.exists():
            stats_lineas_rep = lineas_repuestos.aggregate(
                min_precio=Min('precio_unitario'),
                max_precio=Max('precio_unitario'),
                avg_precio=Avg('precio_unitario')
            )
            self.stdout.write(f'  💰 Precio unitario: ${stats_lineas_rep["min_precio"]:.2f} - ${stats_lineas_rep["max_precio"]:.2f} (promedio: ${stats_lineas_rep["avg_precio"]:.2f})')
            
            # Mostrar algunos ejemplos
            self.stdout.write('  📋 Ejemplos:')
            for linea in lineas_repuestos[:5]:
                self.stdout.write(f'    • {linea.nombre}: ${linea.precio_unitario:.2f} x {linea.cantidad}')
        else:
            self.stdout.write('  ⚠️  No hay líneas de repuestos registradas')
        
        # ==========================================
        # 4. VERIFICAR LÍNEAS DE SERVICIOS
        # ==========================================
        self.stdout.write('\n🔧 Líneas de servicios en documentos:')
        
        lineas_servicios = LineaServicio.objects.filter(documento__empresa=empresa)
        if lineas_servicios.exists():
            stats_lineas_serv = lineas_servicios.aggregate(
                min_precio=Min('precio_unitario'),
                max_precio=Max('precio_unitario'),
                avg_precio=Avg('precio_unitario')
            )
            self.stdout.write(f'  💰 Precio unitario: ${stats_lineas_serv["min_precio"]:.2f} - ${stats_lineas_serv["max_precio"]:.2f} (promedio: ${stats_lineas_serv["avg_precio"]:.2f})')
            
            # Mostrar algunos ejemplos
            self.stdout.write('  📋 Ejemplos:')
            for linea in lineas_servicios[:5]:
                self.stdout.write(f'    • {linea.nombre}: ${linea.precio_unitario:.2f} x {linea.cantidad}')
        else:
            self.stdout.write('  ⚠️  No hay líneas de servicios registradas')
        
        # ==========================================
        # 5. VERIFICAR LÍNEAS DE OTROS SERVICIOS
        # ==========================================
        self.stdout.write('\n🔧 Líneas de otros servicios en documentos:')
        
        lineas_otros = LineaOtroServicio.objects.filter(documento__empresa=empresa)
        if lineas_otros.exists():
            stats_lineas_otros = lineas_otros.aggregate(
                min_costo=Min('costo_interno'),
                max_costo=Max('costo_interno'),
                avg_costo=Avg('costo_interno'),
                min_precio=Min('precio_cliente'),
                max_precio=Max('precio_cliente'),
                avg_precio=Avg('precio_cliente')
            )
            self.stdout.write(f'  💰 Costo interno: ${stats_lineas_otros["min_costo"]:.2f} - ${stats_lineas_otros["max_costo"]:.2f} (promedio: ${stats_lineas_otros["avg_costo"]:.2f})')
            self.stdout.write(f'  💰 Precio cliente: ${stats_lineas_otros["min_precio"]:.2f} - ${stats_lineas_otros["max_precio"]:.2f} (promedio: ${stats_lineas_otros["avg_precio"]:.2f})')
            
            # Mostrar algunos ejemplos
            self.stdout.write('  📋 Ejemplos:')
            for linea in lineas_otros[:5]:
                self.stdout.write(f'    • {linea.nombre}: costo ${linea.costo_interno:.2f}, precio ${linea.precio_cliente:.2f}')
        else:
            self.stdout.write('  ⚠️  No hay líneas de otros servicios registradas')
        
        # ==========================================
        # RESUMEN Y VALIDACIÓN
        # ==========================================
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📊 RESUMEN DE VALIDACIÓN')
        self.stdout.write('='*60)
        
        # Verificar que los precios están en rangos realistas para USD
        precios_ok = True
        
        # Verificar repuestos
        if repuestos.exists() and hasattr(repuestos.first(), 'precio_venta'):
            max_precio_rep = repuestos.aggregate(max_precio=Max('precio_venta'))['max_precio']
            if max_precio_rep > 500:  # Si hay precios mayores a $500, probablemente están en pesos
                self.stdout.write(self.style.WARNING(f'⚠️  Precio máximo de repuestos muy alto: ${max_precio_rep:.2f}'))
                precios_ok = False
        
        # Verificar servicios
        if lineas_servicios.exists():
            max_precio_serv = lineas_servicios.aggregate(max_precio=Max('precio_unitario'))['max_precio']
            if max_precio_serv > 200:  # Si hay precios mayores a $200, probablemente están en pesos
                self.stdout.write(self.style.WARNING(f'⚠️  Precio máximo de servicios muy alto: ${max_precio_serv:.2f}'))
                precios_ok = False
        
        if precios_ok:
            self.stdout.write(
                self.style.SUCCESS('✅ Todos los precios están en rangos realistas para USD')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Algunos precios parecen estar en pesos chilenos')
            )
        
        self.stdout.write('='*60)
