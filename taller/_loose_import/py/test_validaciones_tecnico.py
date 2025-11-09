#!/usr/bin/env python
"""
Test de validaciones del modelo Tecnico refinado
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.core.exceptions import ValidationError

from taller.models.empresa import Empresa
from taller.models.tecnico import Tecnico


def test_validaciones_tecnico():
    """Prueba las validaciones multi-tenant en Tecnico.clean()"""

    print("🔒 TEST DE VALIDACIONES DEL MODELO TECNICO")
    print("=" * 60)

    # Obtener empresa de ejemplo
    empresa = Empresa.objects.first()

    if not empresa:
        print("❌ No se encontró empresa para la prueba")
        return

    # Test 1: Técnico sin empresa (debería fallar)
    print("\n1️⃣ Técnico sin empresa (debería fallar):")
    try:
        tecnico_invalido = Tecnico(
            nombre="Test Técnico",
            # Sin empresa
        )
        tecnico_invalido.clean()
        print("   ❌ Error: La validación debería haber fallado")
    except ValidationError as e:
        print(f"   ✅ Validación funcionó: {e}")

    # Test 2: Técnico válido (debería pasar)
    print("\n2️⃣ Técnico válido (debería pasar):")
    try:
        tecnico_valido = Tecnico(
            nombre="Test Técnico Válido", empresa=empresa, rol=Tecnico.Rol.TECNICO
        )
        tecnico_valido.clean()
        print("   ✅ Validación pasó correctamente")
    except ValidationError as e:
        print(f"   ❌ Error inesperado: {e}")

    # Test 3: Técnico con rol específico
    print("\n3️⃣ Técnico vendedor:")
    try:
        tecnico_vendedor = Tecnico(
            nombre="Test Vendedor", empresa=empresa, rol=Tecnico.Rol.VENDEDOR
        )
        tecnico_vendedor.clean()
        print("   ✅ Técnico vendedor válido")
        print(f"   es_vendedor: {tecnico_vendedor.es_vendedor()}")
        print(f"   es_tecnico: {tecnico_vendedor.es_tecnico()}")
    except ValidationError as e:
        print(f"   ❌ Error inesperado: {e}")


def test_manager_methods():
    """Prueba los métodos del nuevo manager"""

    print("\n🔧 TEST DE MÉTODOS DEL MANAGER")
    print("=" * 60)

    # Test activos()
    print("\n1️⃣ Método activos():")
    activos = Tecnico.objects.activos()
    print(f"   Técnicos activos: {activos.count()}")

    # Test de_empresa()
    print("\n2️⃣ Método de_empresa():")
    empresa = Empresa.objects.first()
    if empresa:
        tecnicos_empresa = Tecnico.objects.de_empresa(empresa)
        print(f"   Técnicos de {empresa}: {tecnicos_empresa.count()}")

    # Test buscar_por_nombre()
    print("\n3️⃣ Método buscar_por_nombre():")
    tecnicos_juan = Tecnico.objects.buscar_por_nombre("juan")
    print(f"   Técnicos con 'juan' en el nombre: {tecnicos_juan.count()}")

    # Test por_rol()
    print("\n4️⃣ Método por_rol():")
    for rol in Tecnico.Rol:
        tecnicos_rol = Tecnico.objects.por_rol(rol.value)
        print(f"   {rol.label}: {tecnicos_rol.count()} técnicos")


def test_unicidad_case_insensitive():
    """Prueba la unicidad case-insensitive"""

    print("\n🔐 TEST DE UNICIDAD CASE-INSENSITIVE")
    print("=" * 60)

    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ No se encontró empresa para la prueba")
        return

    # Test 1: Intentar crear técnico con nombre duplicado (case-insensitive)
    print("\n1️⃣ Intentando crear técnico con nombre duplicado:")

    # Buscar un técnico existente
    tecnico_existente = Tecnico.objects.filter(empresa=empresa).first()
    if tecnico_existente:
        nombre_existente = tecnico_existente.nombre

        try:
            # Intentar crear con el mismo nombre pero diferente capitalización
            nombre_variante = (
                nombre_existente.upper()
                if nombre_existente.islower()
                else nombre_existente.lower()
            )

            tecnico_duplicado = Tecnico.objects.create(
                nombre=nombre_variante, empresa=empresa
            )
            print(f"   ❌ Error: Se creó técnico duplicado '{nombre_variante}'")
            tecnico_duplicado.delete()  # Limpiar
        except Exception as e:
            print("   ✅ Unicidad funcionó: No se pudo crear duplicado")
            print(f"   Error: {e}")
    else:
        print("   ⚠️ No hay técnicos existentes para probar unicidad")


def test_helper_methods():
    """Prueba los métodos helper"""

    print("\n🛠️ TEST DE MÉTODOS HELPER")
    print("=" * 60)

    # Probar con técnicos existentes
    tecnicos = Tecnico.objects.all()[:3]

    for tecnico in tecnicos:
        print(f"\nTécnico: {tecnico.nombre}")
        print(f"   Rol: {tecnico.get_rol_display()}")
        print(f"   es_vendedor(): {tecnico.es_vendedor()}")
        print(f"   es_tecnico(): {tecnico.es_tecnico()}")


if __name__ == "__main__":
    test_validaciones_tecnico()
    test_manager_methods()
    test_unicidad_case_insensitive()
    test_helper_methods()
