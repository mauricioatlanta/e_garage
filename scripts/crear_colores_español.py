#!/usr/bin/env python
"""
Script para crear colores en español para Chile
"""

import os
import sys
from pathlib import Path

import django

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

def main():
    print("🎨 CREANDO COLORES EN ESPAÑOL PARA CHILE")
    print("=" * 50)
    
    try:
        from taller.models.extras_vehiculo import ColorVehiculo

        # Colores básicos en español para Chile
        colores_español = [
            'Blanco', 'Negro', 'Rojo', 'Azul', 'Verde', 'Amarillo', 
            'Gris', 'Plateado', 'Dorado', 'Café', 'Morado', 'Naranja',
            'Rosa', 'Celeste', 'Turquesa', 'Beige', 'Crema'
        ]
        
        print("📝 Creando colores en español:")
        colores_creados = 0
        colores_existentes = 0
        
        for color_nombre in colores_español:
            color, created = ColorVehiculo.objects.get_or_create(
                nombre=color_nombre,
                defaults={'country': 'CL'}
            )
            if created:
                print(f"  ✅ Creado: {color_nombre}")
                colores_creados += 1
            else:
                print(f"  📋 Ya existe: {color_nombre}")
                colores_existentes += 1
                # Actualizar country si no lo tiene
                if not hasattr(color, 'country') or not color.country:
                    color.country = 'CL'
                    color.save()
                    print(f"     → Actualizado país a CL")
        
        print(f"\n📊 RESUMEN:")
        print(f"  Colores creados: {colores_creados}")
        print(f"  Colores existentes: {colores_existentes}")
        print(f"  Total colores CL: {ColorVehiculo.objects.filter(country='CL').count()}")
        
        # Verificar algunos colores en inglés que podríamos marcar como US
        colores_inglés = ['Red', 'Blue', 'Green', 'Black', 'White', 'Yellow', 'Gray', 'Silver', 'Gold', 'Brown']
        print(f"\n🇺🇸 Actualizando colores en inglés para USA:")
        for color_ingles in colores_inglés:
            try:
                color = ColorVehiculo.objects.get(nombre__iexact=color_ingles)
                if not hasattr(color, 'country') or not color.country:
                    color.country = 'US'
                    color.save()
                    print(f"  ✅ {color_ingles} → USA")
            except ColorVehiculo.DoesNotExist:
                pass
                
        print(f"\n🏁 COMPLETADO: Colores configurados por país")
                
    except Exception as e:
        print(f"❌ Error durante creación: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
