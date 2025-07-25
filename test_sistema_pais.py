#!/usr/bin/env python
"""
Script de prueba para verificar el sistema de localización por país
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.utils.pais_utils import get_marcas_por_pais, get_configuracion_pais, formatear_precio

def probar_sistema_pais():
    print("🌎 PROBANDO SISTEMA DE LOCALIZACIÓN POR PAÍS\n")
    
    # Obtener o crear usuarios de prueba
    print("1. 🇨🇱 PROBANDO CONFIGURACIÓN CHILE:")
    print("-" * 40)
    
    try:
        user_cl = User.objects.filter(username='test_chile').first()
        if user_cl:
            empresa_cl = user_cl.empresa
            empresa_cl.pais = 'CL'
            empresa_cl.save()
            
            print(f"   Usuario: {user_cl.username}")
            print(f"   País: {empresa_cl.get_pais_display()}")
            print(f"   Moneda: {empresa_cl.moneda}")
            print(f"   Zona horaria: {empresa_cl.zona_horaria}")
            
            # Probar configuración
            config = get_configuracion_pais(empresa_cl)
            print(f"   Formato fecha: {config['formato_fecha']}")
            print(f"   Decimales: {config['decimales']}")
            print(f"   Impuesto: {config['impuesto_default']*100}%")
            
            # Probar formateo de precios
            precios_ejemplo = [50000, 150000, 500000]
            print("   Ejemplos de precios:")
            for precio in precios_ejemplo:
                print(f"     {formatear_precio(precio, empresa_cl)}")
                
            # Probar marcas
            marcas = get_marcas_por_pais(user_cl)
            print(f"   Marcas disponibles: {marcas.count()}")
            if marcas.exists():
                print(f"     Primeras 3: {', '.join([str(m) for m in marcas[:3]])}")
        else:
            print("   ❌ Usuario test_chile no encontrado")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. 🇺🇸 PROBANDO CONFIGURACIÓN USA:")
    print("-" * 40)
    
    try:
        user_us = User.objects.filter(username='test_usa').first()
        if user_us:
            empresa_us = user_us.empresa
            empresa_us.pais = 'US'
            empresa_us.save()
            
            print(f"   Usuario: {user_us.username}")
            print(f"   País: {empresa_us.get_pais_display()}")
            print(f"   Moneda: {empresa_us.moneda}")
            print(f"   Zona horaria: {empresa_us.zona_horaria}")
            
            # Probar configuración
            config = get_configuracion_pais(empresa_us)
            print(f"   Formato fecha: {config['formato_fecha']}")
            print(f"   Decimales: {config['decimales']}")
            print(f"   Impuesto: {config['impuesto_default']*100}%")
            
            # Probar formateo de precios
            precios_ejemplo = [50, 150, 500]  # Precios en USD
            print("   Ejemplos de precios:")
            for precio in precios_ejemplo:
                print(f"     {formatear_precio(precio, empresa_us)}")
                
            # Probar marcas
            marcas = get_marcas_por_pais(user_us)
            print(f"   Marcas disponibles: {marcas.count()}")
            if marcas.exists():
                print(f"     Primeras 3: {', '.join([str(m) for m in marcas[:3]])}")
        else:
            print("   ❌ Usuario test_usa no encontrado")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3. 📊 RESUMEN DEL SISTEMA:")
    print("-" * 40)
    
    # Estadísticas generales
    empresas_cl = Empresa.objects.filter(pais='CL').count()
    empresas_us = Empresa.objects.filter(pais='US').count()
    
    print(f"   Empresas Chile: {empresas_cl}")
    print(f"   Empresas USA: {empresas_us}")
    print(f"   Total empresas: {empresas_cl + empresas_us}")
    
    print("\n✅ PRUEBA COMPLETADA")
    print("\n📋 PRÓXIMOS PASOS:")
    print("   1. Accede a /demo-pais/ para ver la demo visual")
    print("   2. Prueba cambiar el país en el admin de Django")
    print("   3. Verifica que los precios se formatean correctamente")
    print("   4. Comprueba que las marcas se filtran por país")

if __name__ == "__main__":
    probar_sistema_pais()
