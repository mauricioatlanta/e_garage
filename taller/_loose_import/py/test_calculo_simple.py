#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings.dev')
django.setup()

from decimal import Decimal
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.tecnico import Tecnico
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from django.contrib.auth.models import User

def test_calculo_simple():
    print("🧪 Test de cálculo simple de IVA/Sales Tax")
    
    # Crear usuario y empresa
    user = User.objects.create_user(
        username="testuser_simple",
        email="test@example.com",
        password="testpass123"
    )
    
    empresa_cl = Empresa.objects.create(
        nombre_taller="Taller Chile Test",
        pais="CL",
        user=user
    )
    
    # Crear cliente
    cliente = Cliente.objects.create(
        nombre="Juan Pérez Test",
        email="juan@example.com",
        empresa=empresa_cl
    )
    
    # Crear marca y modelo
    marca = Marca.objects.create(nombre="Toyota Test", country="CL")
    modelo = Modelo.objects.create(nombre="Corolla Test", marca=marca, country="CL")
    
    # Crear vehículo
    vehiculo = Vehiculo.objects.create(
        marca=marca,
        modelo=modelo,
        anio=2020,
        cliente=cliente,
        empresa=empresa_cl
    )
    
    # Crear técnico
    tecnico = Tecnico.objects.create(
        nombre="Carlos Técnico Test",
        empresa=empresa_cl
    )
    
    print("✅ Objetos creados correctamente")
    
    # Crear documento
    doc = Documento.objects.create(
        empresa=empresa_cl,
        tipo="OT",
        cliente=cliente,
        vehiculo=vehiculo,
        tecnico_responsable=tecnico
    )
    
    print("✅ Documento creado correctamente")
    print(f"   - País: {doc.empresa.pais}")
    print(f"   - Tasa aplicada: {doc.tax_rate_applied}")
    print(f"   - Neto repuestos: {doc.neto_repuestos}")
    print(f"   - Neto servicios: {doc.neto_servicios}")
    print(f"   - Neto otros servicios: {doc.neto_otros_servicios}")
    print(f"   - Tax amount: {doc.tax_amount}")
    print(f"   - Total: {doc.total}")
    
    # Test de métodos helper
    print("\n🔧 Test de métodos helper:")
    print(f"   - Decimales: {doc._decimals()}")
    print(f"   - Tasa resuelta: {doc._resolve_tax_rate()}")
    
    # Test de redondeo
    value = Decimal("123.456789")
    rounded_cl = doc._q(value)
    print(f"   - Redondeo CL: {value} -> {rounded_cl}")
    
    print("\n✅ Test completado exitosamente!")

if __name__ == "__main__":
    test_calculo_simple()
