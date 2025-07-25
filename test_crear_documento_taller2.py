#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.contrib.auth import get_user_model
from taller.models import Empresa, Cliente, Vehiculo, Documento
from taller.documentos.views import crear_documento
import json

def test_crear_documento_taller2():
    print("=== TEST: Crear documento con taller2 ===")
    
    # Obtener usuario taller2
    User = get_user_model()
    try:
        user_taller2 = User.objects.get(username='taller2')
        print(f"Usuario encontrado: {user_taller2.username}")
        print(f"Empresa: {user_taller2.empresa_usuario.nombre_taller}")
    except User.DoesNotExist:
        print("Usuario taller2 no encontrado")
        return
    
    # Obtener cliente y vehiculo de Mecanica Express
    empresa_mecanica = user_taller2.empresa_usuario
    clientes = Cliente.objects.filter(empresa=empresa_mecanica)
    print(f"Clientes disponibles en {empresa_mecanica.nombre_taller}: {clientes.count()}")
    
    if not clientes.exists():
        print("No hay clientes en Mecanica Express")
        return
    
    cliente = clientes.first()
    vehiculos = Vehiculo.objects.filter(cliente=cliente)
    print(f"Vehiculos del cliente {cliente.nombre}: {vehiculos.count()}")
    
    if not vehiculos.exists():
        print("No hay vehiculos para este cliente")
        return
    
    vehiculo = vehiculos.first()
    
    # Simular datos del formulario con repuestos y servicios
    post_data = {
        'tipo': 'factura',
        'numero': 'F-TEST-001',
        'cliente': str(cliente.id),
        'vehiculo': str(vehiculo.id),
        'descripcion_trabajo': 'Test de creacion de documento',
        'lleva_iva': 'on',
        'json_items': json.dumps([
            {
                'tipo': 'repuesto',
                'partnumber': 'TEST-001',
                'nombre': 'Repuesto de Prueba',
                'cantidad': 2,
                'precio': 15000
            },
            {
                'tipo': 'servicio',
                'nombre': 'Servicio de Prueba',
                'precio': 25000
            }
        ])
    }
    
    print(f"Datos del formulario preparados:")
    print(f"   - Cliente: {cliente.nombre}")
    print(f"   - Vehiculo: {vehiculo.marca} {vehiculo.modelo}")
    print(f"   - JSON items: {post_data['json_items']}")
    
    # Crear request simulado
    factory = RequestFactory()
    request = factory.post('/documentos/crear/', post_data)
    request.user = user_taller2
    
    # Agregar middleware necesario
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    msg_middleware = MessageMiddleware(lambda x: None)
    msg_middleware.process_request(request)
    
    try:
        print("\n=== EJECUTANDO VISTA crear_documento ===")
        response = crear_documento(request)
        print(f"Vista ejecutada, status code: {response.status_code}")
        
        # Verificar si se creo el documento
        documentos_nuevos = Documento.objects.filter(
            empresa=empresa_mecanica,
            numero='F-TEST-001'
        )
        
        if documentos_nuevos.exists():
            doc = documentos_nuevos.first()
            print(f"Documento creado: ID {doc.id}")
            
            # Verificar repuestos
            repuestos = doc.repuestodocumento_set.all()
            print(f"Repuestos asociados: {repuestos.count()}")
            for rep in repuestos:
                print(f"   - {rep.nombre}: {rep.cantidad} x ${rep.precio}")
            
            # Verificar servicios
            servicios = doc.serviciodocumento_set.all()
            print(f"Servicios asociados: {servicios.count()}")
            for serv in servicios:
                print(f"   - {serv.nombre}: ${serv.precio}")
            
            if repuestos.count() > 0 or servicios.count() > 0:
                print("EXITO! El documento se creo con datos")
            else:
                print("PROBLEMA: El documento se creo pero SIN datos")
                
        else:
            print("No se encontro el documento creado")
            
    except Exception as e:
        print(f"Error ejecutando vista: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crear_documento_taller2()
