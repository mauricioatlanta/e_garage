#!/usr/bin/env python
"""
Verificación final del sistema de colores
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

print("🔍 VERIFICACIÓN FINAL DEL SISTEMA DE COLORES")
print("=" * 50)

try:
    from taller.models.extras_vehiculo import ColorVehiculo
    from django.contrib.auth.models import User
    
    # Verificar colores para Chile
    print("\n🇨🇱 COLORES PARA CHILE:")
    colores_cl = ColorVehiculo.get_colores_para_pais('CL')
    for i, color in enumerate(colores_cl, 1):
        print(f"  {i}. {color.nombre}")
    print(f"Total: {len(colores_cl)} colores")
    
    # Verificar colores para USA
    print("\n🇺🇸 COLORES PARA USA:")
    colores_us = ColorVehiculo.get_colores_para_pais('US')
    for i, color in enumerate(colores_us, 1):
        print(f"  {i}. {color.nombre}")
    print(f"Total: {len(colores_us)} colores")
    
    # Verificar que tenemos colores en español
    colores_español = ['Blanco', 'Negro', 'Rojo', 'Azul', 'Verde', 'Amarillo', 'Gris', 'Plateado']
    print("\n🎨 VERIFICACIÓN DE COLORES EN ESPAÑOL:")
    for color_esp in colores_español:
        existe = ColorVehiculo.objects.filter(nombre=color_esp).exists()
        status = "✅" if existe else "❌"
        print(f"  {status} {color_esp}")
    
    # Verificar total general
    total_colores = ColorVehiculo.objects.count()
    print(f"\n📊 TOTAL COLORES EN BASE DE DATOS: {total_colores}")
    
    # Test de usuario con empresa Chile
    print("\n👤 TEST DE USUARIO CHILE:")
    try:
        user_cl = User.objects.filter(empresa__pais='CL').first()
        if user_cl:
            print(f"Usuario encontrado: {user_cl.username}")
            print(f"País de empresa: {user_cl.empresa.pais}")
            
            # Simular formulario de vehículo
            from taller.vehiculos.forms import VehiculoForm
            form = VehiculoForm(user=user_cl)
            print("✅ Formulario VehiculoForm creado exitosamente")
        else:
            print("❌ No se encontró usuario con empresa en Chile")
    except Exception as e:
        print(f"⚠️  Error en test de usuario: {e}")
    
    print("\n🏁 VERIFICACIÓN COMPLETADA")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
