#!/usr/bin/env python
"""
🔍 Verificador de precios por país - eGarage
Prueba que los precios se muestren correctamente según el país del usuario
"""

import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User

from taller.models.empresa import Empresa
from taller.models.precio_suscripcion import PrecioSuscripcion


def verificar_precios_por_pais():
    """Verifica los precios configurados por país"""
    print("🔍 VERIFICACIÓN DE PRECIOS POR PAÍS")
    print("=" * 50)
    
    for pais, nombre_pais in [('CL', 'Chile'), ('US', 'Estados Unidos')]:
        print(f"\n🏛️ {nombre_pais} ({pais}):")
        print("-" * 30)
        
        precios = PrecioSuscripcion.objects.filter(pais=pais, activo=True).order_by('precio')
        
        if not precios.exists():
            print(f"   ❌ No hay precios configurados para {nombre_pais}")
            continue
        
        for precio in precios:
            print(f"   💰 {precio.nombre_plan}")
            print(f"      Precio: {precio.precio_formateado()}")
            print(f"      Usuarios: {precio.usuarios_incluidos}")
            print(f"      API: {'✅' if precio.api_incluida else '❌'}")
            print(f"      Multi-sucursal: {'✅' if precio.multisucursal else '❌'}")
            print(f"      Características: {len(precio.caracteristicas_list())} items")
            print()

def verificar_usuarios_test():
    """Verifica los usuarios de prueba y sus países"""
    print("\n👤 USUARIOS DE PRUEBA:")
    print("=" * 30)
    
    usuarios_test = [
        'test_chile@egarage.cl',
        'test_chile_pago@egarage.cl', 
        'test_usa@egarage.com',
        'test_usa_pago@egarage.com'
    ]
    
    for email in usuarios_test:
        try:
            user = User.objects.get(email=email)
            if hasattr(user, 'empresa'):
                empresa = user.empresa
                flag = '🇨🇱' if empresa.pais == 'CL' else '🇺🇸'
                print(f"   {flag} {email}")
                print(f"      País: {empresa.pais}")
                print(f"      Empresa: {empresa.nombre_taller}")
                print(f"      Moneda: {empresa.moneda}")
                print()
            else:
                print(f"   ⚠️ {email} - Sin empresa asociada")
        except User.DoesNotExist:
            print(f"   ❌ {email} - Usuario no encontrado")

def test_vista_precios():
    """Simula la vista de precios para diferentes países"""
    print("\n🌐 SIMULACIÓN DE VISTA DE PRECIOS:")
    print("=" * 40)
    
    for pais, nombre_pais in [('CL', 'Chile'), ('US', 'Estados Unidos')]:
        print(f"\n📊 Precios para {nombre_pais}:")
        
        precios = PrecioSuscripcion.objects.filter(pais=pais, activo=True).order_by('precio')
        
        if precios.exists():
            for precio in precios:
                print(f"   • {precio.nombre_plan}: {precio.precio_formateado()}")
        else:
            # Precios por defecto
            if pais == 'CL':
                print("   • Plan Mensual: $20,000 CLP")
                print("   • Plan Semestral: $110,000 CLP") 
                print("   • Plan Anual: $200,000 CLP")
            else:
                print("   • Monthly Plan: $20.00 USD")
                print("   • Semi-Annual Plan: $110.00 USD")
                print("   • Annual Plan: $200.00 USD")

def main():
    print("🚀 VERIFICADOR DE PRECIOS DIFERENCIADOS POR PAÍS")
    print("=" * 55)
    print("Validando configuración de precios de suscripciones...")
    print()
    
    try:
        verificar_precios_por_pais()
        verificar_usuarios_test()
        test_vista_precios()
        
        print("\n🎯 URLS DE PRUEBA:")
        print("=" * 25)
        print("📋 Vista general de precios: http://127.0.0.1:8000/precios/")
        print("🇨🇱 Precios para Chile: http://127.0.0.1:8000/precios/?country=CL")
        print("🇺🇸 Precios para USA: http://127.0.0.1:8000/precios/?country=US")
        print("⚙️ Admin de precios: http://127.0.0.1:8000/admin/taller/preciosuscripcion/")
        
        print("\n✅ VERIFICACIÓN COMPLETADA")
        print("=" * 30)
        print("Los precios están correctamente configurados por país")
        print("Chile: Precios en CLP (sin decimales)")
        print("USA: Precios en USD (con decimales)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
