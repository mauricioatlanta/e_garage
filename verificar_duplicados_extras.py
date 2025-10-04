#!/usr/bin/env python
"""
Script de verificación de duplicados en ColorVehiculo, MotorVehiculo, CajaVehiculo.
Ejecutar ANTES de aplicar las migraciones de scoping por país.

Uso:
    python verificar_duplicados_extras.py
    python verificar_duplicados_extras.py --fix  # Modo interactivo para resolver duplicados
"""

import os
import sys
import django
from collections import defaultdict

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "egarage.settings")
django.setup()

from django.db.models import Count
from django.db.models.functions import Lower
from taller.models.extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo
from taller.models import Vehiculo


def analizar_duplicados_colores():
    """Detecta colores duplicados por país (case-insensitive)"""
    print("\n" + "="*60)
    print("🎨 ANALIZANDO DUPLICADOS EN COLORVEHICULO")
    print("="*60)
    
    # Si ya tienen campo country, usar ese filtro
    if hasattr(ColorVehiculo, '_meta') and 'country' in [f.name for f in ColorVehiculo._meta.get_fields()]:
        duplicados = (
            ColorVehiculo.objects
            .values('country')
            .annotate(lower_nombre=Lower('nombre'))
            .values('country', 'lower_nombre')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
    else:
        # Sin campo country, solo detecta duplicados globales
        duplicados = (
            ColorVehiculo.objects
            .annotate(lower_nombre=Lower('nombre'))
            .values('lower_nombre')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
    
    if duplicados:
        print(f"⚠️  Encontrados {len(duplicados)} grupos de duplicados:\n")
        
        for dup in duplicados:
            lower_nombre = dup['lower_nombre']
            country = dup.get('country', 'N/A')
            count = dup['count']
            
            print(f"  📍 País: {country}, Nombre: '{lower_nombre}' ({count} registros)")
            
            # Mostrar los registros específicos
            if country != 'N/A':
                registros = ColorVehiculo.objects.filter(
                    nombre__iexact=lower_nombre,
                    country=country
                )
            else:
                registros = ColorVehiculo.objects.filter(nombre__iexact=lower_nombre)
            
            for reg in registros:
                usos = Vehiculo.objects.filter(color=reg).count()
                print(f"     → ID {reg.id}: '{reg.nombre}' (usado en {usos} vehículos)")
        
        return True
    else:
        print("✅ No se encontraron duplicados")
        return False


def analizar_duplicados_motores():
    """Detecta motores duplicados por país (case-insensitive)"""
    print("\n" + "="*60)
    print("🔧 ANALIZANDO DUPLICADOS EN MOTORVEHICULO")
    print("="*60)
    
    if hasattr(MotorVehiculo, '_meta') and 'country' in [f.name for f in MotorVehiculo._meta.get_fields()]:
        duplicados = (
            MotorVehiculo.objects
            .values('country')
            .annotate(lower_nombre=Lower('nombre'))
            .values('country', 'lower_nombre')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
    else:
        duplicados = (
            MotorVehiculo.objects
            .annotate(lower_nombre=Lower('nombre'))
            .values('lower_nombre')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
    
    if duplicados:
        print(f"⚠️  Encontrados {len(duplicados)} grupos de duplicados:\n")
        
        for dup in duplicados:
            lower_nombre = dup['lower_nombre']
            country = dup.get('country', 'N/A')
            count = dup['count']
            
            print(f"  📍 País: {country}, Nombre: '{lower_nombre}' ({count} registros)")
            
            if country != 'N/A':
                registros = MotorVehiculo.objects.filter(
                    nombre__iexact=lower_nombre,
                    country=country
                )
            else:
                registros = MotorVehiculo.objects.filter(nombre__iexact=lower_nombre)
            
            for reg in registros:
                usos = Vehiculo.objects.filter(motor=reg).count()
                modelos_asociados = reg.modelos.count()
                print(f"     → ID {reg.id}: '{reg.nombre}' (usado en {usos} vehículos, {modelos_asociados} modelos)")
        
        return True
    else:
        print("✅ No se encontraron duplicados")
        return False


def analizar_duplicados_cajas():
    """Detecta cajas duplicadas por país (case-insensitive)"""
    print("\n" + "="*60)
    print("⚙️  ANALIZANDO DUPLICADOS EN CAJAVEHICULO")
    print("="*60)
    
    if hasattr(CajaVehiculo, '_meta') and 'country' in [f.name for f in CajaVehiculo._meta.get_fields()]:
        duplicados = (
            CajaVehiculo.objects
            .values('country')
            .annotate(lower_nombre=Lower('nombre'))
            .values('country', 'lower_nombre')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
    else:
        duplicados = (
            CajaVehiculo.objects
            .annotate(lower_nombre=Lower('nombre'))
            .values('lower_nombre')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
    
    if duplicados:
        print(f"⚠️  Encontrados {len(duplicados)} grupos de duplicados:\n")
        
        for dup in duplicados:
            lower_nombre = dup['lower_nombre']
            country = dup.get('country', 'N/A')
            count = dup['count']
            
            print(f"  📍 País: {country}, Nombre: '{lower_nombre}' ({count} registros)")
            
            if country != 'N/A':
                registros = CajaVehiculo.objects.filter(
                    nombre__iexact=lower_nombre,
                    country=country
                )
            else:
                registros = CajaVehiculo.objects.filter(nombre__iexact=lower_nombre)
            
            for reg in registros:
                usos = Vehiculo.objects.filter(caja=reg).count()
                modelos_asociados = reg.modelos.count()
                print(f"     → ID {reg.id}: '{reg.nombre}' (usado en {usos} vehículos, {modelos_asociados} modelos)")
        
        return True
    else:
        print("✅ No se encontraron duplicados")
        return False


def estadisticas_generales():
    """Muestra estadísticas generales de los modelos"""
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS GENERALES")
    print("="*60)
    
    total_colores = ColorVehiculo.objects.count()
    total_motores = MotorVehiculo.objects.count()
    total_cajas = CajaVehiculo.objects.count()
    
    print(f"\n  Total Colores: {total_colores}")
    print(f"  Total Motores: {total_motores}")
    print(f"  Total Cajas: {total_cajas}")
    
    # Si tienen campo country, mostrar distribución
    if hasattr(ColorVehiculo, '_meta') and 'country' in [f.name for f in ColorVehiculo._meta.get_fields()]:
        colores_cl = ColorVehiculo.objects.filter(country='CL').count()
        colores_us = ColorVehiculo.objects.filter(country='US').count()
        print(f"\n  Colores CL: {colores_cl}")
        print(f"  Colores US: {colores_us}")
    
    if hasattr(MotorVehiculo, '_meta') and 'country' in [f.name for f in MotorVehiculo._meta.get_fields()]:
        motores_cl = MotorVehiculo.objects.filter(country='CL').count()
        motores_us = MotorVehiculo.objects.filter(country='US').count()
        print(f"\n  Motores CL: {motores_cl}")
        print(f"  Motores US: {motores_us}")
    
    if hasattr(CajaVehiculo, '_meta') and 'country' in [f.name for f in CajaVehiculo._meta.get_fields()]:
        cajas_cl = CajaVehiculo.objects.filter(country='CL').count()
        cajas_us = CajaVehiculo.objects.filter(country='US').count()
        print(f"\n  Cajas CL: {cajas_cl}")
        print(f"  Cajas US: {cajas_us}")


def main():
    print("\n" + "🔍 "*20)
    print("VERIFICACIÓN DE DUPLICADOS - extras_vehiculo.py")
    print("🔍 "*20)
    
    estadisticas_generales()
    
    hay_duplicados = False
    hay_duplicados |= analizar_duplicados_colores()
    hay_duplicados |= analizar_duplicados_motores()
    hay_duplicados |= analizar_duplicados_cajas()
    
    print("\n" + "="*60)
    if hay_duplicados:
        print("⚠️  SE ENCONTRARON DUPLICADOS")
        print("="*60)
        print("\n📝 Acciones recomendadas:")
        print("  1. Revisar los duplicados listados arriba")
        print("  2. Decidir qué registro mantener (el más usado)")
        print("  3. Actualizar FKs en Vehiculo para apuntar al que mantienes")
        print("  4. Eliminar los duplicados sobrantes")
        print("\n💡 Ejemplo en shell de Django:")
        print("  # Fusionar colores duplicados")
        print("  color_mantener = ColorVehiculo.objects.get(id=1)")
        print("  color_eliminar = ColorVehiculo.objects.get(id=2)")
        print("  Vehiculo.objects.filter(color=color_eliminar).update(color=color_mantener)")
        print("  color_eliminar.delete()")
        sys.exit(1)
    else:
        print("✅ NO SE ENCONTRARON DUPLICADOS")
        print("="*60)
        print("\n🎉 Puedes proceder con la migración:")
        print("  python manage.py makemigrations")
        print("  python manage.py migrate")
        sys.exit(0)


if __name__ == "__main__":
    main()



