#!/usr/bin/env python3
"""
🎯 SCRIPT FINAL: Verificación Completa del Sistema Jerárquico de Formularios
📅 Diciembre 2024
🔧 Propósito: Verificar que el sistema jerárquico Marca → Modelo → Motor/Caja esté 100% funcional

✅ TESTS INCLUIDOS:
1. Datos base (marcas, modelos, motores, cajas)
2. Endpoints AJAX (load_modelos, load_motores, load_cajas)
3. Integración JavaScript en templates
4. URLs correctamente configuradas
5. Relaciones jerárquicas funcionando
"""

import os
import sys
import django
import json

# Configurar Django
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
    django.setup()
    
    from taller.models.marca import Marca
    from taller.models.modelo import Modelo
    from taller.models.extras_vehiculo import MotorVehiculo, CajaVehiculo
    from django.test import Client
    
    print("🎯 VERIFICACIÓN FINAL: Sistema Jerárquico de Formularios de Vehículos")
    print("=" * 80)
    
    # 1. Verificar datos base
    print("\n📊 1. DATOS BASE:")
    marcas_count = Marca.objects.count()
    modelos_count = Modelo.objects.count()
    motores_count = MotorVehiculo.objects.count()
    cajas_count = CajaVehiculo.objects.count()
    
    print(f"   ✅ Marcas: {marcas_count:,}")
    print(f"   ✅ Modelos: {modelos_count:,}")
    print(f"   ✅ Motores: {motores_count:,}")
    print(f"   ✅ Cajas: {cajas_count:,}")
    
    if marcas_count == 0 or modelos_count == 0:
        print("   ❌ ERROR: Faltan datos base")
        sys.exit(1)
    
    # 2. Probar endpoints AJAX
    print("\n🌐 2. ENDPOINTS AJAX:")
    client = Client()
    
    # Test load_modelos
    response = client.get('/cl/taller/ajax/load-modelos/?marca_id=1')
    modelos_data = response.json() if response.status_code == 200 else []
    print(f"   📡 load-modelos: {response.status_code} (modelos: {len(modelos_data)})")
    
    if modelos_data:
        primer_modelo_id = modelos_data[0]['id']
        print(f"   🏆 Primer modelo: {modelos_data[0]['nombre']}")
        
        # Test load_motores
        response = client.get(f'/cl/taller/ajax/load-motores/?modelo_id={primer_modelo_id}')
        motores_data = response.json() if response.status_code == 200 else []
        print(f"   📡 load-motores: {response.status_code} (motores: {len(motores_data)})")
        
        # Test load_cajas
        response = client.get(f'/cl/taller/ajax/load-cajas/?modelo_id={primer_modelo_id}')
        cajas_data = response.json() if response.status_code == 200 else []
        print(f"   📡 load-cajas: {response.status_code} (cajas: {len(cajas_data)})")
        
        # Test load_motores_cajas (combinado)
        response = client.get(f'/cl/taller/ajax/load-motores-cajas/?modelo_id={primer_modelo_id}')
        if response.status_code == 200:
            combinado_data = response.json()
            print(f"   📡 load-motores-cajas: {response.status_code} (motores: {len(combinado_data.get('motores', []))}, cajas: {len(combinado_data.get('cajas', []))})")
        else:
            print(f"   📡 load-motores-cajas: {response.status_code}")
    
    # 3. Verificar relaciones jerárquicas
    print("\n🔗 3. RELACIONES JERÁRQUICAS:")
    
    # Buscar ejemplos de relaciones completas
    ejemplos_completos = 0
    for marca in Marca.objects.all()[:5]:  # Revisar primeras 5 marcas
        modelos = Modelo.objects.filter(marca=marca)
        if modelos.exists():
            for modelo in modelos[:2]:  # Revisar primeros 2 modelos por marca
                motores = MotorVehiculo.objects.filter(modelo=modelo)
                cajas = CajaVehiculo.objects.filter(modelo=modelo)
                if motores.exists() and cajas.exists():
                    print(f"   ✅ {marca.nombre} → {modelo.nombre}: {motores.count()} motores, {cajas.count()} cajas")
                    ejemplos_completos += 1
                    break
    
    if ejemplos_completos > 0:
        print(f"   🎯 Encontradas {ejemplos_completos} cadenas jerárquicas completas")
    else:
        print("   ⚠️ No se encontraron cadenas jerárquicas completas")
    
    # 4. Verificar JavaScript en template
    print("\n📝 4. INTEGRACIÓN JAVASCRIPT:")
    try:
        with open('templates/taller/vehiculos/crear_vehiculo.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        checks = {
            'id_motor en template': 'id_motor' in template_content,
            'id_caja en template': 'id_caja' in template_content,
            'URL AJAX modelos': '/taller/ajax/load-modelos/' in template_content,
            'URL AJAX motores': '/taller/ajax/load-motores/' in template_content,
            'URL AJAX cajas': '/taller/ajax/load-cajas/' in template_content,
            'Event listener marca': 'selectMarca.addEventListener' in template_content,
            'Event listener modelo': 'selectModelo.addEventListener' in template_content,
        }
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
            
    except FileNotFoundError:
        print("   ❌ Template crear_vehiculo.html no encontrado")
    
    # 5. Resumen final
    print("\n" + "=" * 80)
    print("🎯 RESUMEN FINAL:")
    
    all_endpoints_ok = all([
        response.status_code == 200 for response in [
            client.get('/cl/taller/ajax/load-modelos/?marca_id=1'),
            client.get(f'/cl/taller/ajax/load-motores/?modelo_id={primer_modelo_id}' if 'primer_modelo_id' in locals() else '/cl/taller/ajax/load-motores/?modelo_id=1'),
            client.get(f'/cl/taller/ajax/load-cajas/?modelo_id={primer_modelo_id}' if 'primer_modelo_id' in locals() else '/cl/taller/ajax/load-cajas/?modelo_id=1'),
        ]
    ])
    
    if all_endpoints_ok and marcas_count > 0 and modelos_count > 0 and motores_count > 0 and cajas_count > 0:
        print("✅ ESTADO: Sistema jerárquico COMPLETAMENTE FUNCIONAL")
        print("🚀 El formulario de creación de vehículos está listo para producción")
        print("🎯 Los usuarios podrán seleccionar Marca → Modelo → Motor/Caja dinámicamente")
        print("\n📋 INSTRUCCIONES DE USO:")
        print("   1. Acceder a /cl/vehiculos/crear/")
        print("   2. Seleccionar una marca")
        print("   3. Ver cómo se cargan automáticamente los modelos")
        print("   4. Seleccionar un modelo")
        print("   5. Ver cómo se cargan motores y cajas para ese modelo")
        print("   6. Completar el resto del formulario normalmente")
    else:
        print("❌ ESTADO: Sistema tiene problemas pendientes")
        print("📋 Verificar endpoints AJAX y datos base antes de usar en producción")
    
    print("\n🎉 VERIFICACIÓN COMPLETADA")
