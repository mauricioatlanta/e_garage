#!/usr/bin/env python
import os

import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User

from taller.models.clientes import Cliente


def verificar_clientes():
    """Verificar clientes en la base de datos para el usuario testuser_cl"""
    
    try:
        # Obtener el usuario testuser_cl
        user = User.objects.get(username='testuser_cl')
        empresa = user.empresa
        
        print("🔍 VERIFICACIÓN DE CLIENTES")
        print("=" * 50)
        print(f"👤 Usuario: {user.username}")
        print(f"🏢 Empresa: {empresa.nombre_taller} (ID: {empresa.id})")
        print(f"🌍 País: {empresa.pais}")
        print("")
        
        # Contar clientes totales
        total_clientes = Cliente.objects.count()
        print(f"📊 Total clientes en DB: {total_clientes}")
        
        # Contar clientes de esta empresa
        clientes_empresa = Cliente.objects.filter(empresa=empresa)
        count_empresa = clientes_empresa.count()
        print(f"🏢 Clientes de empresa '{empresa.nombre_taller}': {count_empresa}")
        print("")
        
        if count_empresa > 0:
            print("📋 ÚLTIMOS 10 CLIENTES:")
            ultimos_clientes = clientes_empresa.order_by('-id')[:10]
            for i, cliente in enumerate(ultimos_clientes, 1):
                print(f"  {i:2}. {cliente.nombre} {cliente.apellido} (ID: {cliente.id}) - {cliente.email}")
        else:
            print("❌ NO HAY CLIENTES REGISTRADOS PARA ESTA EMPRESA")
            
        print("")
        
        # Verificar si hay clientes de otras empresas
        otras_empresas = Cliente.objects.exclude(empresa=empresa).count()
        if otras_empresas > 0:
            print(f"ℹ️  Hay {otras_empresas} clientes de otras empresas en la DB")
            
    except User.DoesNotExist:
        print("❌ Usuario testuser_cl no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    verificar_clientes()
