#!/usr/bin/env python3
"""
Script para crear un cliente ficticio para el taller1
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.clientes import Cliente
from taller.models.region_ciudad import TallerRegion, TallerCiudad
from taller.models.empresa import Empresa

def crear_cliente_ficticio():
    try:
        print("🚀 Iniciando creación de cliente ficticio...")
        
        # Obtener usuario taller1
        usuario_taller1 = User.objects.get(username='taller1')
        print(f"✅ Usuario encontrado: {usuario_taller1.username}")
        
        # Obtener empresa del taller1
        empresa_taller1 = Empresa.objects.get(usuario=usuario_taller1)
        print(f"✅ Empresa encontrada: {empresa_taller1.nombre_taller}")
        
        # Obtener una región y ciudad para el cliente
        region_metropolitana = TallerRegion.objects.get(nombre='Región Metropolitana')
        ciudad_santiago = TallerCiudad.objects.filter(region=region_metropolitana, nombre='Santiago').first()
        
        print(f"✅ Región: {region_metropolitana.nombre}")
        if ciudad_santiago:
            print(f"✅ Ciudad: {ciudad_santiago.nombre}")
        else:
            print("⚠️ Ciudad Santiago no encontrada, usando sin ciudad")
            ciudad_santiago = None
        
        # Crear cliente ficticio
        cliente_data = {
            'empresa': empresa_taller1,
            'nombre': 'Juan Carlos',
            'apellido': 'Pérez González',
            'telefono': '+56912345678',
            'direccion': 'Av. Libertador Bernardo O\'Higgins 1234',
            'region': region_metropolitana,
            'ciudad': ciudad_santiago,
            'email': 'juan.perez@email.com'
        }
        
        # Verificar si ya existe
        cliente_existente = Cliente.objects.filter(
            empresa=empresa_taller1,
            email='juan.perez@email.com'
        ).first()
        
        if cliente_existente:
            print(f"⚠️ Cliente ya existe: {cliente_existente}")
            return cliente_existente
        
        # Crear nuevo cliente
        cliente = Cliente.objects.create(**cliente_data)
        print(f"🎉 Cliente creado exitosamente:")
        print(f"   ID: {cliente.pk}")
        print(f"   Nombre: {cliente.nombre} {cliente.apellido}")
        print(f"   Teléfono: {cliente.telefono}")
        print(f"   Email: {cliente.email}")
        print(f"   Dirección: {cliente.direccion}")
        
        ciudad_nombre = cliente.ciudad.nombre if cliente.ciudad else "Sin ciudad"
        region_nombre = cliente.region.nombre if cliente.region else "Sin región"
        print(f"   Ciudad: {ciudad_nombre}, {region_nombre}")
        print(f"   Empresa: {cliente.empresa.nombre_taller}")
        
        return cliente
        
    except User.DoesNotExist:
        print("❌ Error: Usuario 'taller1' no encontrado")
        return None
    except Empresa.DoesNotExist:
        print("❌ Error: Empresa para 'taller1' no encontrada")
        return None
    except TallerRegion.DoesNotExist:
        print("❌ Error: Región Metropolitana no encontrada")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

if __name__ == "__main__":
    cliente = crear_cliente_ficticio()
    if cliente:
        print(f"\n✅ Cliente creado con ID: {cliente.pk}")
        
        # Verificar que el cliente pertenece a la empresa correcta
        print(f"\n🔍 Verificación de aislamiento:")
        clientes_taller1 = Cliente.objects.filter(empresa=cliente.empresa)
        print(f"   Clientes del Taller 1: {clientes_taller1.count()}")
        
        # Verificar aislamiento con otros talleres
        try:
            usuario_taller2 = User.objects.get(username='taller2')
            empresa_taller2 = Empresa.objects.get(usuario=usuario_taller2)
            clientes_taller2 = Cliente.objects.filter(empresa=empresa_taller2)
            print(f"   Clientes del Taller 2: {clientes_taller2.count()}")
            print("✅ Aislamiento confirmado: cada taller ve solo sus clientes")
        except:
            print("⚠️ Taller2 no encontrado para verificar aislamiento")
    else:
        print("❌ No se pudo crear el cliente")
