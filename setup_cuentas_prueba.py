#!/usr/bin/env python
"""
Script para limpiar completamente la base de datos y crear cuentas de prueba limpias
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.documento import Documento
from taller.models.repuesto import Repuesto
from taller.models.tienda import Tienda

def limpiar_datos():
    print("🧹 Limpiando base de datos...")
    
    # Eliminar todos los datos en orden para evitar errores de foreign key
    print("   - Eliminando documentos...")
    Documento.objects.all().delete()
    
    print("   - Eliminando vehículos...")
    Vehiculo.objects.all().delete()
    
    print("   - Eliminando clientes...")
    Cliente.objects.all().delete()
    
    print("   - Eliminando repuestos...")
    Repuesto.objects.all().delete()
    
    print("   - Eliminando tiendas...")
    Tienda.objects.all().delete()
    
    print("   - Eliminando empresas...")
    Empresa.objects.all().delete()
    
    print("   - Eliminando usuarios...")
    User.objects.all().delete()
    
    print("✅ Base de datos limpiada completamente")

def crear_cuentas_prueba():
    print("\n👥 Creando cuentas de prueba...")
    
    # Deshabilitar temporalmente el signal
    from django.db.models.signals import post_save
    from taller.signals import crear_empresa_al_crear_usuario
    from django.contrib.auth.models import User
    
    post_save.disconnect(crear_empresa_al_crear_usuario, sender=User)
    
    try:
        # 1. Usuario administrador de la aplicación
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@egarage.com',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        
        # Crear empresa para el admin
        admin_empresa = Empresa.objects.create(
            usuario=admin_user,
            nombre_taller="Administración E-Garage",
            empresa="E-Garage Admin"
        )
        
        print(f"✅ Administrador creado:")
        print(f"   Usuario: admin")
        print(f"   Email: admin@egarage.com")
        print(f"   Password: admin123")
        print(f"   Empresa: {admin_empresa.nombre_taller}")
        
        # 2. Taller de prueba 1
        taller1_user = User.objects.create_user(
            username='taller1',
            email='taller1@test.com',
            password='taller123',
            first_name='Juan',
            last_name='Pérez'
        )
        
        taller1_empresa = Empresa.objects.create(
            usuario=taller1_user,
            nombre_taller="Taller AutoFix",
            empresa="AutoFix SpA",
            direccion="Av. Principal 123",
            telefono="+56912345678"
        )
        
        print(f"\n✅ Taller 1 creado:")
        print(f"   Usuario: taller1")
        print(f"   Email: taller1@test.com")
        print(f"   Password: taller123")
        print(f"   Empresa: {taller1_empresa.nombre_taller}")
        
        # 3. Taller de prueba 2
        taller2_user = User.objects.create_user(
            username='taller2',
            email='taller2@test.com',
            password='taller123',
            first_name='María',
            last_name='González'
        )
        
        taller2_empresa = Empresa.objects.create(
            usuario=taller2_user,
            nombre_taller="Mecánica Express",
            empresa="Express Motors Ltda",
            direccion="Calle Secundaria 456",
            telefono="+56987654321"
        )
        
        print(f"\n✅ Taller 2 creado:")
        print(f"   Usuario: taller2")
        print(f"   Email: taller2@test.com")
        print(f"   Password: taller123")
        print(f"   Empresa: {taller2_empresa.nombre_taller}")
        
        # Crear algunas tiendas de ejemplo para cada taller
        print(f"\n🏪 Creando tiendas de ejemplo...")
        
        # Tiendas para taller 1
        tienda1_1 = Tienda.objects.create(
            empresa=taller1_empresa,
            nombre="Repuestos Central",
            direccion="Av. Comercio 789",
            telefono="+56911111111"
        )
        
        tienda1_2 = Tienda.objects.create(
            empresa=taller1_empresa,
            nombre="AutoPartes Norte",
            direccion="Calle Norte 321",
            telefono="+56922222222"
        )
        
        # Tiendas para taller 2
        tienda2_1 = Tienda.objects.create(
            empresa=taller2_empresa,
            nombre="Distribuidora Sur",
            direccion="Av. Sur 654",
            telefono="+56933333333"
        )
        
        print(f"   - {tienda1_1.nombre} (Taller 1)")
        print(f"   - {tienda1_2.nombre} (Taller 1)")
        print(f"   - {tienda2_1.nombre} (Taller 2)")
        
    finally:
        # Rehabilitar el signal
        post_save.connect(crear_empresa_al_crear_usuario, sender=User)

def mostrar_resumen():
    print(f"\n📊 Resumen final:")
    print(f"   Total usuarios: {User.objects.count()}")
    print(f"   Total empresas: {Empresa.objects.count()}")
    print(f"   Total tiendas: {Tienda.objects.count()}")
    
    print(f"\n🔐 Credenciales de acceso:")
    print(f"   Admin:   usuario='admin'   password='admin123'")
    print(f"   Taller1: usuario='taller1' password='taller123'")
    print(f"   Taller2: usuario='taller2' password='taller123'")
    
    print(f"\n🌐 Puedes acceder en: http://127.0.0.1:8000/")

if __name__ == "__main__":
    limpiar_datos()
    crear_cuentas_prueba()
    mostrar_resumen()
    print(f"\n🎉 Base de datos preparada para pruebas!")
