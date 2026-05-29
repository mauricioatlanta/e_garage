#!/usr/bin/env python
"""
Test de validaciones del modelo Cliente refinado
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.core.exceptions import ValidationError

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa


def test_validaciones_cliente():
    """Prueba las validaciones de país en Cliente.clean()"""

    print("🔒 TEST DE VALIDACIONES DEL MODELO CLIENTE")
    print("=" * 60)

    # Obtener empresas de ejemplo
    empresa_chile = Empresa.objects.filter(pais="CL").first()
    empresa_usa = Empresa.objects.filter(pais="US").first()

    if not empresa_chile or not empresa_usa:
        print("❌ No se encontraron empresas de ejemplo")
        return

    # Test 1: Cliente Chile con campos USA (debería fallar)
    print("\n1️⃣ Cliente Chile con campos USA (debería fallar):")
    try:
        cliente_chile_invalido = Cliente(
            nombre="Juan",
            apellido="Pérez",
            empresa=empresa_chile,
            # Campos de Chile (correctos)
            region_id=1,
            ciudad_id=1,
            # Campos de USA (incorrectos para Chile)
            estado_usa_id=1,
            ciudad_usa_id=1,
            zipcode="12345",
        )
        cliente_chile_invalido.clean()
        print("   ❌ Error: La validación debería haber fallado")
    except ValidationError as e:
        print(f"   ✅ Validación funcionó: {e}")

    # Test 2: Cliente USA con campos Chile (debería fallar)
    print("\n2️⃣ Cliente USA con campos Chile (debería fallar):")
    try:
        cliente_usa_invalido = Cliente(
            nombre="John",
            apellido="Doe",
            empresa=empresa_usa,
            # Campos de USA (correctos)
            estado_usa_id=1,
            ciudad_usa_id=1,
            zipcode="12345",
            # Campos de Chile (incorrectos para USA)
            region_id=1,
            ciudad_id=1,
        )
        cliente_usa_invalido.clean()
        print("   ❌ Error: La validación debería haber fallado")
    except ValidationError as e:
        print(f"   ✅ Validación funcionó: {e}")

    # Test 3: Cliente Chile válido
    print("\n3️⃣ Cliente Chile válido (debería pasar):")
    try:
        cliente_chile_valido = Cliente(
            nombre="Pedro",
            apellido="González",
            empresa=empresa_chile,
            region_id=1,
            ciudad_id=1,
            telefono="+56912345678",
        )
        cliente_chile_valido.clean()
        print("   ✅ Validación pasó correctamente")
    except ValidationError as e:
        print(f"   ❌ Error inesperado: {e}")

    # Test 4: Cliente USA válido
    print("\n4️⃣ Cliente USA válido (debería pasar):")
    try:
        cliente_usa_valido = Cliente(
            nombre="Jane",
            apellido="Smith",
            empresa=empresa_usa,
            estado_usa_id=1,
            ciudad_usa_id=1,
            zipcode="12345",
            telefono="+15551234567",
        )
        cliente_usa_valido.clean()
        print("   ✅ Validación pasó correctamente")
    except ValidationError as e:
        print(f"   ❌ Error inesperado: {e}")

    # Test 5: Cliente sin empresa (debería pasar, no valida nada)
    print("\n5️⃣ Cliente sin empresa (debería pasar sin validar):")
    try:
        cliente_sin_empresa = Cliente(
            nombre="Test",
            apellido="User",
            region_id=1,
            ciudad_id=1,
            estado_usa_id=1,
            ciudad_usa_id=1,
            zipcode="12345",
        )
        cliente_sin_empresa.clean()
        print("   ✅ Validación pasó (sin empresa, no valida)")
    except ValidationError as e:
        print(f"   ❌ Error inesperado: {e}")

    print("\n" + "=" * 60)
    print("✅ TEST DE VALIDACIONES COMPLETADO")


def mostrar_clientes_actuales():
    """Muestra los clientes actuales y sus campos"""

    print("\n📊 CLIENTES ACTUALES Y SUS CAMPOS")
    print("=" * 60)

    for cliente in Cliente.objects.select_related("empresa").all():
        print(f"\n👤 {cliente.nombre} {cliente.apellido} (ID: {cliente.id})")
        print(f"   Empresa: {cliente.empresa} ({cliente.empresa.pais})")

        # Campos Chile
        campos_chile = []
        if cliente.region_id:
            campos_chile.append(f"region_id={cliente.region_id}")
        if cliente.ciudad_id:
            campos_chile.append(f"ciudad_id={cliente.ciudad_id}")

        # Campos USA
        campos_usa = []
        if cliente.estado_usa_id:
            campos_usa.append(f"estado_usa_id={cliente.estado_usa_id}")
        if cliente.ciudad_usa_id:
            campos_usa.append(f"ciudad_usa_id={cliente.ciudad_usa_id}")
        if cliente.zipcode:
            campos_usa.append(f"zipcode={cliente.zipcode}")

        if campos_chile:
            print(f"   🇨🇱 Campos Chile: {', '.join(campos_chile)}")
        if campos_usa:
            print(f"   🇺🇸 Campos USA: {', '.join(campos_usa)}")

        # Verificar consistencia
        if cliente.empresa.pais == "CL" and campos_usa:
            print("   ⚠️ INCONSISTENCIA: Cliente Chile con campos USA")
        elif cliente.empresa.pais == "US" and campos_chile:
            print("   ⚠️ INCONSISTENCIA: Cliente USA con campos Chile")


if __name__ == "__main__":
    test_validaciones_cliente()
    mostrar_clientes_actuales()
