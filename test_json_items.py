#!/usr/bin/env python3
"""
Script de prueba para verificar el procesamiento de json_items
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.cliente import Cliente
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
import json

def test_json_items_processing():
    """Simular el procesamiento de json_items"""
    print("🧪 === TEST JSON_ITEMS PROCESSING ===")
    
    # Datos de prueba
    test_json_items = json.dumps([
        {
            "tipo": "repuesto",
            "partnumber": "FLT-001",
            "nombre": "Filtro de aceite",
            "cantidad": 1,
            "precio": 15000
        },
        {
            "tipo": "servicio",
            "nombre": "Cambio de aceite",
            "precio": 25000
        }
    ])
    
    print(f"📄 JSON de prueba: {test_json_items}")
    
    try:
        # Obtener usuario
        user = User.objects.first()
        if not user:
            print("❌ No hay usuarios en la BD")
            return
            
        print(f"👤 Usuario: {user.username}")
        
        # Obtener empresa
        try:
            empresa = user.empresa_usuario
        except:
            empresa, created = Empresa.objects.get_or_create(
                usuario=user,
                defaults={'nombre_taller': f'Taller de {user.username}'}
            )
        
        print(f"🏢 Empresa: {empresa.nombre_taller}")
        
        # Obtener cliente
        cliente = Cliente.objects.filter(empresa=empresa).first()
        if not cliente:
            cliente = Cliente.objects.create(
                empresa=empresa,
                nombre="Cliente Prueba",
                apellido="Test",
                rut="12345678-9"
            )
        
        print(f"👥 Cliente: {cliente.nombre}")
        
        # Crear documento
        documento = Documento.objects.create(
            empresa=empresa,
            tipo_documento="Orden de trabajo",
            numero_documento="TEST-001",
            cliente=cliente,
            fecha="2025-01-22"
        )
        
        print(f"📋 Documento creado: {documento.numero_documento}")
        
        # Procesar JSON items (simular la lógica de views.py)
        if test_json_items:
            items = json.loads(test_json_items)
            print(f"📦 Items a procesar: {len(items)}")
            
            items_procesados = 0
            repuestos_creados = 0
            servicios_creados = 0
            
            for item in items:
                print(f"   Procesando: {item}")
                
                nombre = item.get('nombre', '').strip()
                precio = float(item.get('precio', 0))
                
                if not nombre or precio <= 0:
                    print(f"   ❌ Item rechazado")
                    continue
                
                items_procesados += 1
                
                if item.get('tipo') == 'repuesto':
                    repuesto_doc = RepuestoDocumento.objects.create(
                        documento=documento,
                        codigo=item.get('partnumber', f'AUTO-{items_procesados}'),
                        nombre=nombre,
                        cantidad=int(item.get('cantidad', 1)),
                        precio=precio
                    )
                    repuestos_creados += 1
                    print(f"   ✅ Repuesto creado: {nombre} (${precio})")
                    
                elif item.get('tipo') == 'servicio':
                    servicio_doc = ServicioDocumento.objects.create(
                        empresa=empresa,
                        documento=documento,
                        nombre=nombre,
                        precio=precio
                    )
                    servicios_creados += 1
                    print(f"   ✅ Servicio creado: {nombre} (${precio})")
            
            print(f"\n📊 RESUMEN:")
            print(f"   Items procesados: {items_procesados}")
            print(f"   Repuestos creados: {repuestos_creados}")
            print(f"   Servicios creados: {servicios_creados}")
            
            # Verificar en BD
            repuestos_bd = RepuestoDocumento.objects.filter(documento=documento)
            servicios_bd = ServicioDocumento.objects.filter(documento=documento)
            
            print(f"\n🔍 VERIFICACIÓN EN BD:")
            print(f"   Repuestos en BD: {repuestos_bd.count()}")
            for r in repuestos_bd:
                print(f"     - {r.nombre}: ${r.precio} x {r.cantidad}")
                
            print(f"   Servicios en BD: {servicios_bd.count()}")
            for s in servicios_bd:
                print(f"     - {s.nombre}: ${s.precio}")
                
            if repuestos_creados == repuestos_bd.count() and servicios_creados == servicios_bd.count():
                print("\n✅ TEST EXITOSO: Todo procesado correctamente")
            else:
                print("\n❌ TEST FALLIDO: Discrepancia en BD")
                
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_items_processing()
