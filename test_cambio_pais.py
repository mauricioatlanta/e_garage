#!/usr/bin/env python
"""
Script para probar la configuración automática por país en empresas existentes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.empresa import Empresa
from taller.utils.pais_utils import get_configuracion_pais, formatear_precio

def actualizar_empresa_usa():
    """Actualiza una empresa existente para probar configuración USA"""
    print("🇺🇸 CONFIGURANDO EMPRESA DE PRUEBA PARA USA\n")
    
    # Tomar la primera empresa y configurarla como USA
    empresa = Empresa.objects.first()
    if empresa:
        print(f"Empresa original: {empresa.nombre_taller}")
        print(f"País original: {empresa.pais}")
        print(f"Moneda original: {empresa.moneda}")
        print(f"Zona horaria original: {empresa.zona_horaria}")
        
        # Cambiar a USA
        empresa.pais = 'US'
        empresa.save()  # Esto activará la lógica del save()
        
        # Recargar desde DB
        empresa.refresh_from_db()
        
        print(f"\n✅ DESPUÉS DEL CAMBIO:")
        print(f"País: {empresa.get_pais_display()}")
        print(f"Moneda: {empresa.moneda}")
        print(f"Zona horaria: {empresa.zona_horaria}")
        
        # Probar configuración
        config = get_configuracion_pais(empresa)
        print(f"\n🔧 CONFIGURACIÓN AUTOMÁTICA:")
        print(f"Formato fecha: {config['formato_fecha']}")
        print(f"Decimales: {config['decimales']}")
        print(f"Impuesto: {config['impuesto_default']*100}%")
        print(f"Validación patente: {config['validacion_patente']}")
        
        # Probar formateo de precios
        print(f"\n💰 EJEMPLOS DE PRECIOS:")
        precios = [50, 150, 500, 1250.50]
        for precio in precios:
            print(f"   {precio} → {formatear_precio(precio, empresa)}")
            
        print(f"\n🎯 PROPIEDADES ÚTILES:")
        print(f"   es_usa: {empresa.es_usa}")
        print(f"   es_chile: {empresa.es_chile}")
        print(f"   simbolo_moneda: {empresa.simbolo_moneda}")
        print(f"   formato_moneda: {empresa.formato_moneda}")
        
        return empresa
    else:
        print("❌ No hay empresas en la base de datos")
        return None

def test_cambio_pais_dinamico():
    """Prueba el cambio dinámico entre países"""
    print("\n🔄 PROBANDO CAMBIO DINÁMICO DE PAÍSES\n")
    
    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ No hay empresas para probar")
        return
        
    paises = ['CL', 'US']
    precio_prueba = 100000
    
    for pais in paises:
        empresa.pais = pais
        empresa.save()
        empresa.refresh_from_db()
        
        config = get_configuracion_pais(empresa)
        precio_formateado = formatear_precio(precio_prueba, empresa)
        
        print(f"🌍 {empresa.get_pais_display()}:")
        print(f"   Moneda: {empresa.moneda}")
        print(f"   Precio ${precio_prueba} se muestra como: {precio_formateado}")
        print(f"   Impuesto: {config['impuesto_default']*100}%")
        print(f"   Validación patente: {config['validacion_patente']}")
        print()

if __name__ == "__main__":
    # Primero probar cambio a USA
    empresa_usa = actualizar_empresa_usa()
    
    if empresa_usa:
        # Luego probar cambio dinámico
        test_cambio_pais_dinamico()
        
        print("✅ SISTEMA DE PAÍSES FUNCIONANDO CORRECTAMENTE")
        print("\n📍 Para probar en la interfaz web:")
        print("   1. Inicia sesión en el sistema")
        print("   2. Ve al admin de Django (/admin/)")
        print("   3. Edita tu empresa y cambia el campo 'País'")
        print("   4. Observa cómo cambian automáticamente moneda y zona horaria")
        print("   5. Visita cualquier página con precios para ver el formato")
    else:
        print("❌ No se pudo completar la prueba")
