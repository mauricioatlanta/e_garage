# -*- coding: utf-8 -*-
"""
Portal de clientes - Configuracion simple

Script Django para configurar usuarios del portal de clientes
"""

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from taller.models.cliente import Cliente
from taller.models.empresa import Empresa
from taller.models.portal_cliente import (
    ClienteUsuario, 
    PortalConfiguracion,
    SolicitudPresupuesto
)

def configurar_portal():
    """Configurar portal de clientes"""
    print("CONFIGURANDO PORTAL DE CLIENTES")
    print("=" * 40)
    
    # 1. Configurar portal para empresas
    print("\nConfigurando empresas...")
    empresas = Empresa.objects.all()
    
    for empresa in empresas:
        config, created = PortalConfiguracion.objects.get_or_create(
            empresa=empresa,
            defaults={
                'portal_activo': True,
                'titulo_portal': f"Portal - {empresa.nombre_taller}",
                'mensaje_bienvenida': f"Bienvenido al portal de {empresa.nombre_taller}",
                'permitir_solicitud_presupuestos': True,
                'permitir_ver_documentos': True,
                'permitir_ver_vehiculos': True,
                'color_primario': "#007bff",
                'horario_atencion': "Lunes a Viernes: 8:00 - 18:00",
            }
        )
        
        if created:
            print(f"  OK {empresa.nombre_taller}")
        else:
            print(f"  EXISTE {empresa.nombre_taller}")
    
    # 2. Crear usuarios para clientes con email
    print("\nCreando usuarios del portal...")
    clientes_con_email = Cliente.objects.exclude(
        email_cliente__isnull=True
    ).exclude(
        email_cliente__exact=''
    )
    
    usuarios_creados = 0
    
    for cliente in clientes_con_email:
        try:
            # Verificar si ya existe
            if hasattr(cliente, 'usuario_portal'):
                print(f"  EXISTE {cliente.nombre}")
                continue
            
            # Crear usuario Django
            username = f"cliente_{cliente.id}"
            
            user = User.objects.create(
                username=username,
                email=cliente.email_cliente,
                first_name=cliente.nombre.split()[0] if cliente.nombre else '',
                password=make_password('cliente123'),
                is_active=True
            )
            
            # Crear ClienteUsuario
            ClienteUsuario.objects.create(
                cliente=cliente,
                user=user,
                activo=True
            )
            
            usuarios_creados += 1
            print(f"  CREADO {cliente.nombre} ({cliente.email_cliente})")
            
        except Exception as e:
            print(f"  ERROR {cliente.nombre}: {str(e)}")
    
    print(f"\nRESUMEN:")
    print(f"  Empresas configuradas: {PortalConfiguracion.objects.count()}")
    print(f"  Usuarios creados: {usuarios_creados}")
    print(f"  Total clientes con email: {clientes_con_email.count()}")
    print(f"  Password para todos: cliente123")
    
    # Mostrar algunos usuarios de ejemplo
    print(f"\nUSUARIOS DE PRUEBA:")
    usuarios = ClienteUsuario.objects.select_related('cliente', 'user')[:3]
    for usuario in usuarios:
        print(f"  Email: {usuario.cliente.email_cliente}")
        print(f"  Username: {usuario.user.username}")
        print(f"  Empresa: {usuario.cliente.empresa.nombre_taller}")
        print(f"  ---")
    
    print(f"\nACCESO AL PORTAL:")
    print(f"  URL: http://localhost:8000/portal/")
    print(f"  Username: (cualquiera de los mostrados arriba)")
    print(f"  Password: cliente123")

# Ejecutar configuracion
configurar_portal()
