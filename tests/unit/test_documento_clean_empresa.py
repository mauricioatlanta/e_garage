"""
Test unitario clave: consistencia de empresa (regla eGarage).
Verifica que todos los objetos relacionados pertenezcan a la misma empresa.
"""

import pytest

from django.core.exceptions import ValidationError
from django.utils import timezone

from taller.models import Cliente, Documento, Empresa, Tecnico, Vehiculo


@pytest.mark.django_db
def test_documento_clean_empresa_consistente():
    """Test que verifica la consistencia de empresa en documentos."""

    # Crear empresas de prueba
    cl = Empresa.objects.create(nombre_taller="Empresa CL", pais="CL", moneda="CLP")
    us = Empresa.objects.create(nombre_taller="Empresa US", pais="US", moneda="USD")

    # Crear objetos para CL
    cli_cl = Cliente.objects.create(
        empresa=cl, nombre="Juan CL", rut_ein="12.345.678-9"
    )
    veh_cl = Vehiculo.objects.create(
        empresa=cl,
        cliente=cli_cl,
        patente="AAA111",
        marca="Ford",
        modelo="Fiesta",
        vin="VIN123456789",
    )
    tec_cl = Tecnico.objects.create(empresa=cl, nombre="Mecánico CL")

    # Crear objetos para US
    cli_us = Cliente.objects.create(empresa=us, nombre="John US", rut_ein="12-3456789")
    veh_us = Vehiculo.objects.create(
        empresa=us,
        cliente=cli_us,
        patente="BBB222",
        marca="Toyota",
        modelo="Corolla",
        vin="VIN987654321",
    )
    tec_us = Tecnico.objects.create(empresa=us, nombre="Mechanic US")

    # ✅ OK: Todo en CL - debe pasar
    d_ok = Documento(
        empresa=cl,
        cliente=cli_cl,
        vehiculo=veh_cl,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
        tecnico_responsable=tec_cl,
    )
    d_ok.full_clean()  # No debe lanzar excepción

    # ✅ OK: Todo en US - debe pasar
    d_ok_us = Documento(
        empresa=us,
        cliente=cli_us,
        vehiculo=veh_us,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
        tecnico_responsable=tec_us,
    )
    d_ok_us.full_clean()  # No debe lanzar excepción

    # ❌ ERROR: Empresa del documento ≠ empresa del cliente
    d_bad_cliente = Documento(
        empresa=us,  # Empresa US
        cliente=cli_cl,  # Cliente CL
        vehiculo=veh_cl,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
        tecnico_responsable=tec_cl,
    )
    with pytest.raises(ValidationError):
        d_bad_cliente.full_clean()

    # ❌ ERROR: Empresa del documento ≠ empresa del vehículo
    d_bad_vehiculo = Documento(
        empresa=cl,  # Empresa CL
        cliente=cli_cl,
        vehiculo=veh_us,  # Vehículo US
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
        tecnico_responsable=tec_cl,
    )
    with pytest.raises(ValidationError):
        d_bad_vehiculo.full_clean()

    # ❌ ERROR: Empresa del documento ≠ empresa del técnico
    d_bad_tecnico = Documento(
        empresa=cl,  # Empresa CL
        cliente=cli_cl,
        vehiculo=veh_cl,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
        tecnico_responsable=tec_us,  # Técnico US
    )
    with pytest.raises(ValidationError):
        d_bad_tecnico.full_clean()


@pytest.mark.django_db
def test_documento_clean_empresa_multiples_errores():
    """Test que verifica múltiples errores de consistencia de empresa."""

    # Crear empresas
    cl = Empresa.objects.create(nombre_taller="Empresa CL", pais="CL", moneda="CLP")
    us = Empresa.objects.create(nombre_taller="Empresa US", pais="US", moneda="USD")

    # Crear objetos para CL
    cli_cl = Cliente.objects.create(
        empresa=cl, nombre="Juan CL", rut_ein="12.345.678-9"
    )
    veh_cl = Vehiculo.objects.create(
        empresa=cl,
        cliente=cli_cl,
        patente="AAA111",
        marca="Ford",
        modelo="Fiesta",
        vin="VIN123456789",
    )
    tec_cl = Tecnico.objects.create(empresa=cl, nombre="Mecánico CL")

    # Crear objetos para US
    cli_us = Cliente.objects.create(empresa=us, nombre="John US", rut_ein="12-3456789")
    veh_us = Vehiculo.objects.create(
        empresa=us,
        cliente=cli_us,
        patente="BBB222",
        marca="Toyota",
        modelo="Corolla",
        vin="VIN987654321",
    )
    tec_us = Tecnico.objects.create(empresa=us, nombre="Mechanic US")

    # ❌ ERROR: Múltiples inconsistencias
    d_bad_multiple = Documento(
        empresa=cl,  # Empresa CL
        cliente=cli_us,  # Cliente US
        vehiculo=veh_us,  # Vehículo US
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
        tecnico_responsable=tec_us,  # Técnico US
    )

    with pytest.raises(ValidationError) as exc_info:
        d_bad_multiple.full_clean()

    # Verificar que el error contiene información sobre las inconsistencias
    error_message = str(exc_info.value)
    assert "empresa" in error_message.lower() or "consistencia" in error_message.lower()


@pytest.mark.django_db
def test_documento_clean_empresa_campos_opcionales():
    """Test que verifica consistencia con campos opcionales."""

    # Crear empresa
    cl = Empresa.objects.create(nombre_taller="Empresa CL", pais="CL", moneda="CLP")

    # Crear objetos
    cli_cl = Cliente.objects.create(
        empresa=cl, nombre="Juan CL", rut_ein="12.345.678-9"
    )
    veh_cl = Vehiculo.objects.create(
        empresa=cl,
        cliente=cli_cl,
        patente="AAA111",
        marca="Ford",
        modelo="Fiesta",
        vin="VIN123456789",
    )

    # ✅ OK: Documento sin técnico responsable (campo opcional)
    d_sin_tecnico = Documento(
        empresa=cl,
        cliente=cli_cl,
        vehiculo=veh_cl,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
        tecnico_responsable=None,  # Campo opcional
    )
    d_sin_tecnico.full_clean()  # No debe lanzar excepción


if __name__ == "__main__":
    # Para ejecutar manualmente
    import os
    import sys

    import django

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings.dev")
    django.setup()

    print("🧪 Ejecutando tests de consistencia de empresa...")

    try:
        test_documento_clean_empresa_consistente()
        print("✅ test_documento_clean_empresa_consistente: PASSED")
    except Exception as e:
        print(f"❌ test_documento_clean_empresa_consistente: FAILED - {e}")

    try:
        test_documento_clean_empresa_multiples_errores()
        print("✅ test_documento_clean_empresa_multiples_errores: PASSED")
    except Exception as e:
        print(f"❌ test_documento_clean_empresa_multiples_errores: FAILED - {e}")

    try:
        test_documento_clean_empresa_campos_opcionales()
        print("✅ test_documento_clean_empresa_campos_opcionales: PASSED")
    except Exception as e:
        print(f"❌ test_documento_clean_empresa_campos_opcionales: FAILED - {e}")

    print("🎯 Tests de consistencia de empresa completados!")
