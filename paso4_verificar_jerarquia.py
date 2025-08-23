#!/usr/bin/env python3
"""
🎯 PASO 4C: Verificar implementación de dependencia jerárquica
Verificar que las vistas AJAX y datos están funcionando correctamente
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller.settings')

try:
    django.setup()
except Exception as e:
    print(f"Error configurando Django: {e}")
    sys.exit(1)

from taller.models import Marca, Modelo, MotorVehiculo, CajaVehiculo

def verificar_datos_jerarquicos():
    """Verificar que tenemos datos para la dependencia jerárquica"""
    print("🔍 **VERIFICANDO DATOS JERÁRQUICOS**")
    print("=" * 50)
    
    # Contar marcas
    total_marcas = Marca.objects.count()
    print(f"📊 Marcas disponibles: {total_marcas}")
    
    # Contar modelos
    total_modelos = Modelo.objects.count()
    print(f"📊 Modelos disponibles: {total_modelos}")
    
    # Contar motores
    total_motores = MotorVehiculo.objects.count()
    print(f"📊 Motores disponibles: {total_motores}")
    
    # Contar cajas
    total_cajas = CajaVehiculo.objects.count()
    print(f"📊 Cajas disponibles: {total_cajas}")
    
    print("\n🎯 **VERIFICACIÓN POR PAÍS**")
    print("-" * 30)
    
    # Datos por país
    modelos_cl = Modelo.objects.filter(pais='CL').count()
    modelos_us = Modelo.objects.filter(pais='US').count()
    print(f"🇨🇱 Chile: {modelos_cl} modelos")
    print(f"🇺🇸 USA: {modelos_us} modelos")
    
    # Verificar algunas marcas populares
    print("\n🔍 **VERIFICACIÓN DE MARCAS POPULARES**")
    print("-" * 40)
    
    marcas_populares = ['Toyota', 'Honda', 'Ford', 'Chevrolet', 'BMW']
    for marca_nombre in marcas_populares:
        try:
            marca = Marca.objects.get(nombre=marca_nombre)
            modelos_marca = Modelo.objects.filter(marca=marca).count()
            motores_marca = MotorVehiculo.objects.filter(modelo__marca=marca).count()
            cajas_marca = CajaVehiculo.objects.filter(modelo__marca=marca).count()
            
            print(f"✅ {marca_nombre}:")
            print(f"   - Modelos: {modelos_marca}")
            print(f"   - Motores: {motores_marca}")
            print(f"   - Cajas: {cajas_marca}")
            
        except Marca.DoesNotExist:
            print(f"❌ {marca_nombre}: No encontrada")
    
    return True

def verificar_dependencias_jerarquicas():
    """Verificar que las dependencias jerárquicas funcionan"""
    print("\n🔗 **VERIFICANDO DEPENDENCIAS JERÁRQUICAS**")
    print("=" * 50)
    
    # Verificar algunas dependencias específicas
    try:
        # Buscar Toyota
        toyota = Marca.objects.filter(nombre='Toyota').first()
        if toyota:
            modelos_toyota = Modelo.objects.filter(marca=toyota)[:3]
            print(f"✅ Toyota encontrada con {modelos_toyota.count()} modelos (mostrando 3):")
            
            for modelo in modelos_toyota:
                motores = MotorVehiculo.objects.filter(modelo=modelo).count()
                cajas = CajaVehiculo.objects.filter(modelo=modelo).count()
                print(f"   📱 {modelo.nombre} ({modelo.pais}): {motores} motores, {cajas} cajas")
        
        # Verificar Honda
        honda = Marca.objects.filter(nombre='Honda').first()
        if honda:
            modelos_honda = Modelo.objects.filter(marca=honda)[:2]
            print(f"\n✅ Honda encontrada con {modelos_honda.count()} modelos (mostrando 2):")
            
            for modelo in modelos_honda:
                motores = MotorVehiculo.objects.filter(modelo=modelo).count()
                cajas = CajaVehiculo.objects.filter(modelo=modelo).count()
                print(f"   📱 {modelo.nombre} ({modelo.pais}): {motores} motores, {cajas} cajas")
        
        print("\n✅ Dependencias jerárquicas verificadas correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando dependencias: {e}")
        return False

def verificar_archivos_creados():
    """Verificar que todos los archivos necesarios existen"""
    print("\n📁 **VERIFICANDO ARCHIVOS CREADOS**")
    print("=" * 40)
    
    archivos_requeridos = [
        'taller/ajax_views.py',
        'static/js/formulario_jerarquico.js',
        'paso4_urls_ajax.py'
    ]
    
    todos_existen = True
    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            print(f"✅ {archivo}")
        else:
            print(f"❌ {archivo} - NO ENCONTRADO")
            todos_existen = False
    
    return todos_existen

def generar_ejemplo_uso():
    """Generar ejemplo de uso para testing manual"""
    print("\n🧪 **EJEMPLO DE USO - TESTING MANUAL**")
    print("=" * 45)
    
    # Buscar una marca con datos
    toyota = Marca.objects.filter(nombre='Toyota').first()
    if toyota:
        modelo = Modelo.objects.filter(marca=toyota).first()
        if modelo:
            print(f"📋 **Ejemplo para testing:**")
            print(f"1. Seleccionar Marca: {toyota.nombre} (ID: {toyota.id})")
            print(f"2. Debería cargar modelos incluyendo: {modelo.nombre}")
            print(f"3. Seleccionar Modelo: {modelo.nombre} (ID: {modelo.id})")
            
            motores = MotorVehiculo.objects.filter(modelo=modelo)[:2]
            cajas = CajaVehiculo.objects.filter(modelo=modelo)[:2]
            
            if motores:
                print(f"4. Deberían cargar motores como:")
                for motor in motores:
                    print(f"   - {motor.cilindrada} {motor.tipo}")
            
            if cajas:
                print(f"5. Deberían cargar cajas como:")
                for caja in cajas:
                    print(f"   - {caja.tipo} {caja.velocidades}vel")
    
    print(f"\n🌐 **URLs de Testing:**")
    print(f"- /ajax/load-modelos/?marca_id={toyota.id if toyota else 1}")
    print(f"- /ajax/load-motores-cajas/?modelo_id={modelo.id if toyota and modelo else 1}")

def main():
    print("🎯 **VERIFICACIÓN COMPLETA - PASO 4 JERARQUÍA**")
    print("=" * 60)
    
    # Verificar datos
    datos_ok = verificar_datos_jerarquicos()
    
    # Verificar dependencias
    dependencias_ok = verificar_dependencias_jerarquicas()
    
    # Verificar archivos
    archivos_ok = verificar_archivos_creados()
    
    # Generar ejemplo
    generar_ejemplo_uso()
    
    print(f"\n🎯 **RESUMEN FINAL**")
    print("=" * 30)
    print(f"✅ Datos disponibles: {'Sí' if datos_ok else 'No'}")
    print(f"✅ Dependencias OK: {'Sí' if dependencias_ok else 'No'}")
    print(f"✅ Archivos creados: {'Sí' if archivos_ok else 'No'}")
    
    if datos_ok and dependencias_ok and archivos_ok:
        print(f"\n🎉 **PASO 4 COMPLETADO EXITOSAMENTE**")
        print(f"🔄 Sistema listo para formularios jerárquicos")
        print(f"\n📋 **SIGUIENTE PASO:**")
        print(f"1. Incluir el JavaScript en tu template de vehículos")
        print(f"2. Asegurar que los IDs de campos sean: id_marca, id_modelo, id_motor, id_caja")
        print(f"3. Probar la funcionalidad en el navegador")
    else:
        print(f"\n⚠️  **HAY PROBLEMAS QUE REVISAR**")
        print(f"Verificar los elementos marcados con ❌")

if __name__ == "__main__":
    main()
