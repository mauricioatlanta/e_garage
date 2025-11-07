#!/usr/bin/env python
"""
Test de validaciones del modelo Vehiculo refinado
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.core.exceptions import ValidationError
from taller.models.vehiculos import Vehiculo
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente


def test_validaciones_vehiculo():
    """Prueba las validaciones de coherencia en Vehiculo.clean()"""
    
    print("🔒 TEST DE VALIDACIONES DEL MODELO VEHICULO")
    print("=" * 60)
    
    # Obtener empresas de ejemplo
    empresa_chile = Empresa.objects.filter(pais="CL").first()
    empresa_usa = Empresa.objects.filter(pais="US").first()
    
    cliente_chile = Cliente.objects.filter(empresa=empresa_chile).first()
    cliente_usa = Cliente.objects.filter(empresa=empresa_usa).first()
    
    if not all([empresa_chile, empresa_usa, cliente_chile, cliente_usa]):
        print("❌ No se encontraron datos suficientes para la prueba")
        return
    
    # Test 1: Vehículo sin VIN ni patente (debería fallar)
    print("\n1️⃣ Vehículo sin VIN ni patente (debería fallar):")
    try:
        vehiculo_invalido = Vehiculo(
            cliente=cliente_chile,
            empresa=empresa_chile,
            anio=2022
            # Sin VIN ni patente
        )
        vehiculo_invalido.clean()
        print("   ❌ Error: La validación debería haber fallado")
    except ValidationError as e:
        print(f"   ✅ Validación funcionó: {e}")
    
    # Test 2: Cliente de diferente empresa (debería fallar)
    print("\n2️⃣ Cliente de diferente empresa (debería fallar):")
    try:
        vehiculo_invalido = Vehiculo(
            cliente=cliente_usa,  # Cliente USA
            empresa=empresa_chile,  # Empresa Chile
            patente="TEST123",
            anio=2022
        )
        vehiculo_invalido.clean()
        print("   ❌ Error: La validación debería haber fallado")
    except ValidationError as e:
        print(f"   ✅ Validación funcionó: {e}")
    
    # Test 3: Vehículo Chile con marca_texto (debería fallar)
    print("\n3️⃣ Vehículo Chile con marca_texto (debería fallar):")
    try:
        vehiculo_invalido = Vehiculo(
            cliente=cliente_chile,
            empresa=empresa_chile,
            patente="TEST456",
            anio=2022,
            marca_texto="Toyota"  # Incorrecto para Chile
        )
        vehiculo_invalido.clean()
        print("   ❌ Error: La validación debería haber fallado")
    except ValidationError as e:
        print(f"   ✅ Validación funcionó: {e}")
    
    # Test 4: Vehículo USA válido (debería pasar)
    print("\n4️⃣ Vehículo USA válido (debería pasar):")
    try:
        vehiculo_valido = Vehiculo(
            cliente=cliente_usa,
            empresa=empresa_usa,
            vin="1HGBH41JXMN109186",
            anio=2022,
            marca_texto="Ford",
            modelo_texto="Mustang"
        )
        vehiculo_valido.clean()
        print("   ✅ Validación pasó correctamente")
    except ValidationError as e:
        print(f"   ❌ Error inesperado: {e}")
    
    # Test 5: Vehículo Chile válido (debería pasar)
    print("\n5️⃣ Vehículo Chile válido (debería pasar):")
    try:
        vehiculo_valido = Vehiculo(
            cliente=cliente_chile,
            empresa=empresa_chile,
            patente="CHI123",
            anio=2022
            # Sin marca_texto (correcto para Chile)
        )
        vehiculo_valido.clean()
        print("   ✅ Validación pasó correctamente")
    except ValidationError as e:
        print(f"   ❌ Error inesperado: {e}")


def test_manager_methods():
    """Prueba los métodos del nuevo manager"""
    
    print("\n🔧 TEST DE MÉTODOS DEL MANAGER")
    print("=" * 60)
    
    # Obtener datos de prueba
    empresa_usa = Empresa.objects.filter(pais="US").first()
    cliente_usa = Cliente.objects.filter(empresa=empresa_usa).first()
    
    if not empresa_usa or not cliente_usa:
        print("❌ No se encontraron datos USA para la prueba")
        return
    
    # Test de_empresa
    print("\n1️⃣ Método de_empresa():")
    vehiculos_empresa = Vehiculo.objects.de_empresa(empresa_usa)
    print(f"   Vehículos de empresa USA: {vehiculos_empresa.count()}")
    
    # Test de_cliente
    print("\n2️⃣ Método de_cliente():")
    vehiculos_cliente = Vehiculo.objects.de_cliente(cliente_usa.id)
    print(f"   Vehículos del cliente {cliente_usa}: {vehiculos_cliente.count()}")
    
    # Test combinado
    print("\n3️⃣ Métodos combinados:")
    vehiculos_combinado = Vehiculo.objects.de_empresa(empresa_usa).de_cliente(cliente_usa.id)
    print(f"   Vehículos de empresa USA y cliente {cliente_usa}: {vehiculos_combinado.count()}")
    
    # Test con_vin
    print("\n4️⃣ Método con_vin():")
    vehiculos_con_vin = Vehiculo.objects.con_vin()
    print(f"   Vehículos con VIN: {vehiculos_con_vin.count()}")


def test_display_label():
    """Prueba el método display_label()"""
    
    print("\n🏷️ TEST DE DISPLAY_LABEL")
    print("=" * 60)
    
    # Probar con vehículos existentes
    vehiculos = Vehiculo.objects.all()[:5]
    
    for v in vehiculos:
        print(f"   Vehículo {v.id}: {v.display_label()}")


if __name__ == "__main__":
    test_validaciones_vehiculo()
    test_manager_methods()
    test_display_label()
