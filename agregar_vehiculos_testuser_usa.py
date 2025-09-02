#!/usr/bin/env python
"""
Script para agregar vehículos a los clientes de testuser_usa
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.empresa import Empresa
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.extras_vehiculo import ColorVehiculo

def main():
    print("🚗 Agregando vehículos para testuser_usa\n")
    
    try:
        user_usa = User.objects.get(username='testuser_usa')
        empresa_usa = user_usa.empresa
        print(f"Usuario: {user_usa.username}")
        print(f"Empresa: {empresa_usa.nombre_taller} (ID: {empresa_usa.id})")
        
        # Obtener clientes de esta empresa
        clientes = Cliente.objects.filter(empresa=empresa_usa)
        print(f"Clientes encontrados: {clientes.count()}")
        
        for cliente in clientes:
            print(f"\nCliente: {cliente.nombre} {cliente.apellido}")
            
            # Verificar si ya tiene vehículos
            vehiculos_existentes = Vehiculo.objects.filter(cliente=cliente)
            print(f"Vehículos existentes: {vehiculos_existentes.count()}")
            
            if vehiculos_existentes.count() == 0:
                # Obtener una marca disponible
                try:
                    marca_ford = Marca.objects.filter(nombre__icontains='Ford').first()
                    if not marca_ford:
                        marca_ford = Marca.objects.first()  # Tomar cualquier marca disponible
                    
                    # Obtener un modelo disponible para esa marca
                    modelo_obj = Modelo.objects.filter(marca=marca_ford).first()
                    if not modelo_obj:
                        print(f"❌ No hay modelos disponibles para la marca {marca_ford}")
                        continue
                    
                    # Obtener un color disponible
                    color_obj = ColorVehiculo.objects.first()
                    
                    # Crear un vehículo para este cliente
                    vehiculo = Vehiculo.objects.create(
                        empresa=empresa_usa,  # Asignar la empresa
                        cliente=cliente,
                        patente=f"US{cliente.pk}123",
                        marca=marca_ford,
                        modelo=modelo_obj,
                        anio=2020,
                        color=color_obj
                    )
                    print(f"✅ Vehículo creado: {vehiculo.patente} ({vehiculo.marca} {vehiculo.modelo})")
                    
                except Exception as e:
                    print(f"❌ Error creando vehículo: {e}")
            else:
                for vehiculo in vehiculos_existentes:
                    print(f"  - {vehiculo.patente} ({vehiculo.marca} {vehiculo.modelo})")
        
        print("\n🔍 VERIFICANDO RESULTADO:")
        print("=" * 50)
        
        # Verificar el formulario ahora
        from taller.documentos.forms import DocumentoForm
        form = DocumentoForm(empresa=empresa_usa)
        
        vehiculo_qs = form.fields['vehiculo'].queryset
        print(f"Vehículos en formulario: {vehiculo_qs.count()}")
        
        if vehiculo_qs.count() > 0:
            print("✅ Vehículos disponibles en el formulario:")
            for vehiculo in vehiculo_qs:
                print(f"  - {vehiculo.patente} ({vehiculo.marca} {vehiculo.modelo}) - Cliente: {vehiculo.cliente.nombre}")
        else:
            print("❌ Aún no hay vehículos en el formulario")
            
    except User.DoesNotExist:
        print("❌ Usuario testuser_usa no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
