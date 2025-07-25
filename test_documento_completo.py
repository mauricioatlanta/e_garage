#!/usr/bin/env python3
"""
Script para probar la creación y edición completa de documentos
Detectar dónde está el error al guardar repuestos y servicios
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.models.perfilusuario import PerfilUsuario
import json

def crear_documento_ficticio():
    """Crear un documento con múltiples repuestos y servicios"""
    print("🧪 === CREAR DOCUMENTO FICTICIO ===")
    
    try:
        # Obtener usuario y perfil
        user = User.objects.first()
        if not user:
            print("❌ No hay usuarios en la BD")
            return None
            
        # Obtener o crear perfil
        try:
            perfil = PerfilUsuario.objects.get(user=user)
        except PerfilUsuario.DoesNotExist:
            # Crear empresa primero
            empresa, created = Empresa.objects.get_or_create(
                usuario=user,
                defaults={'nombre_taller': f'Taller de {user.username}'}
            )
            # Crear perfil
            perfil = PerfilUsuario.objects.create(
                user=user,
                empresa=empresa,
                rol='admin'  # Usar rol admin en lugar de es_superadmin
            )
            
        print(f"👤 Usuario: {user.username}")
        print(f"🏢 Empresa: {perfil.empresa.nombre_taller}")
        
        # Obtener o crear cliente
        cliente, created = Cliente.objects.get_or_create(
            empresa=perfil.empresa,
            nombre="Cliente Prueba",
            defaults={
                'apellido': "Test",
                'telefono': "987654321",
                'email': "cliente@test.com"
            }
        )
        
        print(f"👥 Cliente: {cliente.nombre} {cliente.apellido}")
        
        # Crear documento
        documento = Documento.objects.create(
            empresa=perfil.empresa,
            tipo_documento="Orden de trabajo",
            numero_documento="TEST-DOC-001",
            cliente=cliente,
            observaciones="Documento de prueba para detectar errores"
        )
        
        print(f"📋 Documento creado: {documento.numero_documento}")
        
        # Simular json_items con múltiples repuestos y servicios
        json_items_data = [
            {
                "tipo": "repuesto",
                "partnumber": "FLT-001",
                "nombre": "Filtro de aceite",
                "cantidad": 1,
                "precio": 15000
            },
            {
                "tipo": "repuesto", 
                "partnumber": "OIL-001",
                "nombre": "Aceite motor 5W30",
                "cantidad": 4,
                "precio": 8000
            },
            {
                "tipo": "repuesto",
                "partnumber": "BRK-001", 
                "nombre": "Pastillas de freno",
                "cantidad": 1,
                "precio": 45000
            },
            {
                "tipo": "servicio",
                "nombre": "Cambio de aceite",
                "precio": 25000
            },
            {
                "tipo": "servicio",
                "nombre": "Revisión de frenos",
                "precio": 35000
            },
            {
                "tipo": "servicio",
                "nombre": "Diagnóstico general",
                "precio": 20000
            }
        ]
        
        json_items = json.dumps(json_items_data)
        print(f"📄 JSON items: {json_items}")
        
        # Procesar repuestos y servicios (simular lógica de views.py)
        print("\n🔄 Procesando items...")
        data = json.loads(json_items)
        print(f"Items a procesar: {len(data)}")
        
        repuestos_creados = 0
        servicios_creados = 0
        
        for index, item in enumerate(data):
            print(f"Procesando item {index+1}: {item}")
            
            if item['tipo'] == 'repuesto':
                try:
                    repuesto = RepuestoDocumento.objects.create(
                        documento=documento,
                        codigo=item['partnumber'],
                        nombre=item['nombre'],
                        cantidad=item['cantidad'],
                        precio=item['precio'],
                    )
                    repuestos_creados += 1
                    print(f"   ✅ Repuesto creado: {item['nombre']} (ID: {repuesto.id})")
                except Exception as e:
                    print(f"   ❌ Error creando repuesto: {e}")
                    
            elif item['tipo'] == 'servicio':
                try:
                    servicio = ServicioDocumento.objects.create(
                        empresa=perfil.empresa,
                        documento=documento,
                        nombre=item['nombre'],
                        precio=item['precio'],
                    )
                    servicios_creados += 1
                    print(f"   ✅ Servicio creado: {item['nombre']} (ID: {servicio.id})")
                except Exception as e:
                    print(f"   ❌ Error creando servicio: {e}")
        
        # Verificar que se guardaron en BD
        repuestos_bd = RepuestoDocumento.objects.filter(documento=documento)
        servicios_bd = ServicioDocumento.objects.filter(documento=documento)
        
        print(f"\n📊 RESUMEN CREACIÓN:")
        print(f"   Repuestos creados: {repuestos_creados}")
        print(f"   Servicios creados: {servicios_creados}")
        print(f"   Repuestos en BD: {repuestos_bd.count()}")
        print(f"   Servicios en BD: {servicios_bd.count()}")
        
        # Mostrar detalles
        print(f"\n🔍 REPUESTOS EN BD:")
        for r in repuestos_bd:
            print(f"   - ID:{r.id} | {r.codigo} | {r.nombre} | ${r.precio} x {r.cantidad}")
            
        print(f"\n🔍 SERVICIOS EN BD:")
        for s in servicios_bd:
            print(f"   - ID:{s.id} | {s.nombre} | ${s.precio}")
        
        if repuestos_creados == repuestos_bd.count() and servicios_creados == servicios_bd.count():
            print("\n✅ CREACIÓN EXITOSA")
            return documento
        else:
            print("\n❌ PROBLEMA EN CREACIÓN")
            return None
            
    except Exception as e:
        print(f"❌ Error en creación: {e}")
        import traceback
        traceback.print_exc()
        return None

def editar_documento_ficticio(documento):
    """Simular edición eliminando items"""
    print("\n🧪 === EDITAR DOCUMENTO FICTICIO ===")
    
    try:
        # Obtener estado actual
        repuestos_actual = RepuestoDocumento.objects.filter(documento=documento)
        servicios_actual = ServicioDocumento.objects.filter(documento=documento)
        
        print(f"📋 Editando documento: {documento.numero_documento}")
        print(f"   Repuestos actuales: {repuestos_actual.count()}")
        print(f"   Servicios actuales: {servicios_actual.count()}")
        
        # Simular eliminación de algunos items (manteniendo algunos)
        # Eliminar el primer repuesto y primer servicio
        json_items_editado = [
            # Mantener 2 repuestos (eliminar el tercero)
            {
                "tipo": "repuesto",
                "partnumber": "FLT-001", 
                "nombre": "Filtro de aceite",
                "cantidad": 1,
                "precio": 15000
            },
            {
                "tipo": "repuesto",
                "partnumber": "OIL-001",
                "nombre": "Aceite motor 5W30", 
                "cantidad": 4,
                "precio": 8000
            },
            # Mantener 2 servicios (eliminar el tercero)
            {
                "tipo": "servicio",
                "nombre": "Cambio de aceite",
                "precio": 25000
            },
            {
                "tipo": "servicio", 
                "nombre": "Revisión de frenos",
                "precio": 35000
            }
        ]
        
        json_items = json.dumps(json_items_editado)
        print(f"📄 JSON items editado: {json_items}")
        
        # Procesar edición (simular lógica de views.py editar_documento)
        print("\n🔄 Procesando edición...")
        data = json.loads(json_items)
        print(f"Items a procesar en edición: {len(data)}")
        
        # Eliminar ítems anteriores (como en views.py)
        print("   🗑️ Eliminando items anteriores...")
        repuestos_eliminados = RepuestoDocumento.objects.filter(documento=documento).count()
        servicios_eliminados = ServicioDocumento.objects.filter(documento=documento).count()
        
        RepuestoDocumento.objects.filter(documento=documento).delete()
        ServicioDocumento.objects.filter(documento=documento).delete()
        
        print(f"   Repuestos eliminados: {repuestos_eliminados}")
        print(f"   Servicios eliminados: {servicios_eliminados}")
        
        # Crear nuevos items
        print("   ➕ Creando nuevos items...")
        repuestos_creados = 0
        servicios_creados = 0
        
        # Obtener perfil para empresa
        user = User.objects.first()
        perfil = PerfilUsuario.objects.get(user=user)
        
        for index, item in enumerate(data):
            print(f"   Procesando item editado {index+1}: {item}")
            
            if item['tipo'] == 'repuesto':
                try:
                    repuesto = RepuestoDocumento.objects.create(
                        documento=documento,
                        codigo=item['partnumber'],
                        nombre=item['nombre'],
                        cantidad=item['cantidad'],
                        precio=item['precio'],
                    )
                    repuestos_creados += 1
                    print(f"     ✅ Repuesto recreado: {item['nombre']} (ID: {repuesto.id})")
                except Exception as e:
                    print(f"     ❌ Error recreando repuesto: {e}")
                    
            elif item['tipo'] == 'servicio':
                try:
                    servicio = ServicioDocumento.objects.create(
                        empresa=perfil.empresa,
                        documento=documento,
                        nombre=item['nombre'],
                        precio=item['precio'],
                    )
                    servicios_creados += 1
                    print(f"     ✅ Servicio recreado: {item['nombre']} (ID: {servicio.id})")
                except Exception as e:
                    print(f"     ❌ Error recreando servicio: {e}")
        
        # Verificar estado final
        repuestos_final = RepuestoDocumento.objects.filter(documento=documento)
        servicios_final = ServicioDocumento.objects.filter(documento=documento)
        
        print(f"\n📊 RESUMEN EDICIÓN:")
        print(f"   Items esperados: {len(data)}")
        print(f"   Repuestos esperados: {len([i for i in data if i['tipo'] == 'repuesto'])}")
        print(f"   Servicios esperados: {len([i for i in data if i['tipo'] == 'servicio'])}")
        print(f"   Repuestos creados: {repuestos_creados}")
        print(f"   Servicios creados: {servicios_creados}")
        print(f"   Repuestos en BD: {repuestos_final.count()}")
        print(f"   Servicios en BD: {servicios_final.count()}")
        
        # Mostrar estado final
        print(f"\n🔍 ESTADO FINAL - REPUESTOS:")
        for r in repuestos_final:
            print(f"   - ID:{r.id} | {r.codigo} | {r.nombre} | ${r.precio} x {r.cantidad}")
            
        print(f"\n🔍 ESTADO FINAL - SERVICIOS:")
        for s in servicios_final:
            print(f"   - ID:{s.id} | {s.nombre} | ${s.precio}")
        
        # Verificar si todo salió bien
        repuestos_esperados = len([i for i in data if i['tipo'] == 'repuesto'])
        servicios_esperados = len([i for i in data if i['tipo'] == 'servicio'])
        
        if (repuestos_final.count() == repuestos_esperados and 
            servicios_final.count() == servicios_esperados):
            print("\n✅ EDICIÓN EXITOSA")
            return True
        else:
            print("\n❌ PROBLEMA EN EDICIÓN")
            return False
            
    except Exception as e:
        print(f"❌ Error en edición: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 === TEST COMPLETO DOCUMENTO ===")
    print("Objetivo: Detectar dónde está el error al guardar repuestos y servicios")
    print("=" * 60)
    
    # Paso 1: Crear documento
    documento = crear_documento_ficticio()
    if not documento:
        print("\n❌ ERROR: No se pudo crear el documento inicial")
        return
    
    # Paso 2: Editar documento
    exito_edicion = editar_documento_ficticio(documento)
    
    # Conclusión
    print("\n" + "=" * 60)
    print("🏁 === CONCLUSIONES ===")
    if exito_edicion:
        print("✅ TODO FUNCIONA CORRECTAMENTE")
        print("   El problema debe estar en otro lado (frontend, formulario, etc.)")
    else:
        print("❌ SE DETECTÓ EL PROBLEMA")
        print("   Revisar los logs de error arriba para ver dónde falla")
    
    print(f"\n📋 Documento de prueba creado: {documento.numero_documento} (ID: {documento.id})")
    print("   Puedes revisar este documento en la interfaz web para comparar")

if __name__ == "__main__":
    main()
