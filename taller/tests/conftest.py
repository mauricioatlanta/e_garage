# -*- coding: utf-8 -*-
"""
Configuración de pytest y fixtures comunes

Este archivo contiene fixtures que pueden ser usados
por todos los tests del proyecto.
"""
import pytest
from django.contrib.auth.models import User
from taller.models import Empresa, Estado, Ciudad, TaxPolicy
from ubicacion.models import Address
from decimal import Decimal


@pytest.fixture
def test_user(db):
    """Fixture: crear usuario de prueba"""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def empresa_chile(db, test_user):
    """Fixture: crear empresa de Chile"""
    return Empresa.objects.create(user=test_user, nombre_taller="Taller Chile Test", pais="CL")


@pytest.fixture
def empresa_peru(db):
    """Fixture: crear empresa de Perú"""
    user = User.objects.create_user("peru_user", "peru@test.com", "password")
    return Empresa.objects.create(user=user, nombre_taller="Taller Perú Test", pais="PE")


@pytest.fixture
def empresa_usa(db):
    """Fixture: crear empresa de USA"""
    user = User.objects.create_user("usa_user", "usa@test.com", "password")
    return Empresa.objects.create(user=user, nombre_taller="Taller USA Test", pais="US")


@pytest.fixture
def estado_lima(db):
    """Fixture: crear estado Lima (Perú)"""
    return Estado.objects.create(nombre="Lima", codigo="LIM", pais="PE", sales_tax=18.00)


@pytest.fixture
def ciudad_lima(db, estado_lima):
    """Fixture: crear ciudad Lima"""
    return Ciudad.objects.create(nombre="Lima", estado=estado_lima, sales_tax_local=0.00)


@pytest.fixture
def estado_california(db):
    """Fixture: crear estado California (USA)"""
    return Estado.objects.create(nombre="California", codigo="CA", pais="US", sales_tax=7.25)


@pytest.fixture
def ciudad_los_angeles(db, estado_california):
    """Fixture: crear ciudad Los Angeles"""
    return Ciudad.objects.create(
        nombre="Los Angeles", estado=estado_california, sales_tax_local=0.00
    )


@pytest.fixture
def tax_policy_chile_parts(db):
    """Fixture: política de impuestos Chile repuestos"""
    return TaxPolicy.objects.create(
        country="CL",
        state_code="",
        city_name="",
        applies_to="parts",
        rate=Decimal("0.19"),
        inclusive=False,
        active=True,
    )


@pytest.fixture
def tax_policy_peru_both(db):
    """Fixture: política de impuestos Perú ambos"""
    return TaxPolicy.objects.create(
        country="PE",
        state_code="",
        city_name="",
        applies_to="both",
        rate=Decimal("0.18"),
        inclusive=False,
        active=True,
    )


@pytest.fixture
def tax_policy_usa_california(db):
    """Fixture: política de impuestos USA California"""
    return TaxPolicy.objects.create(
        country="US",
        state_code="CA",
        city_name="",
        applies_to="both",
        rate=Decimal("0.0725"),
        inclusive=False,
        active=True,
    )


@pytest.fixture
def all_tax_policies(db):
    """Fixture: crear todas las políticas de impuestos base"""
    policies = []

    # Chile: IVA 19% solo repuestos
    policies.append(
        TaxPolicy.objects.create(
            country="CL", applies_to="parts", rate=Decimal("0.19"), inclusive=False, active=True
        )
    )

    # USA: varios estados
    usa_states = [
        ("CA", "0.0725"),
        ("TX", "0.0625"),
        ("NY", "0.04"),
        ("FL", "0.06"),
        ("GA", "0.04"),
    ]

    for state_code, rate in usa_states:
        policies.append(
            TaxPolicy.objects.create(
                country="US",
                state_code=state_code,
                applies_to="both",
                rate=Decimal(rate),
                inclusive=False,
                active=True,
            )
        )

    # Brasil: ICMS 18% repuestos
    policies.append(
        TaxPolicy.objects.create(
            country="BR", applies_to="parts", rate=Decimal("0.18"), inclusive=False, active=True
        )
    )

    # Perú: IGV 18% ambos
    policies.append(
        TaxPolicy.objects.create(
            country="PE", applies_to="both", rate=Decimal("0.18"), inclusive=False, active=True
        )
    )

    # Venezuela: IVA 16% ambos
    policies.append(
        TaxPolicy.objects.create(
            country="VE", applies_to="both", rate=Decimal("0.16"), inclusive=False, active=True
        )
    )

    return policies


@pytest.fixture
def all_sample_locations(db):
    """Fixture: crear ubicaciones de muestra para todos los países"""
    locations = {}

    # Perú
    lima = Estado.objects.create(nombre="Lima", codigo="LIM", pais="PE", sales_tax=18.00)
    locations["peru_lima"] = {
        "estado": lima,
        "ciudades": [
            Ciudad.objects.create(nombre="Lima", estado=lima),
            Ciudad.objects.create(nombre="Callao", estado=lima),
        ],
    }

    # Chile
    rm = Estado.objects.create(
        nombre="Región Metropolitana", codigo="RM", pais="CL", sales_tax=19.00
    )
    locations["chile_rm"] = {
        "estado": rm,
        "ciudades": [
            Ciudad.objects.create(nombre="Santiago", estado=rm),
            Ciudad.objects.create(nombre="Maipú", estado=rm),
        ],
    }

    # USA California
    ca = Estado.objects.create(nombre="California", codigo="CA", pais="US", sales_tax=7.25)
    locations["usa_california"] = {
        "estado": ca,
        "ciudades": [
            Ciudad.objects.create(nombre="Los Angeles", estado=ca),
            Ciudad.objects.create(nombre="San Francisco", estado=ca),
        ],
    }

    # Brasil São Paulo
    sp = Estado.objects.create(nombre="São Paulo", codigo="SP", pais="BR", sales_tax=18.00)
    locations["brasil_sao_paulo"] = {
        "estado": sp,
        "ciudades": [
            Ciudad.objects.create(nombre="São Paulo", estado=sp),
        ],
    }

    # Venezuela Distrito Capital
    dc = Estado.objects.create(nombre="Distrito Capital", codigo="DC", pais="VE", sales_tax=16.00)
    locations["venezuela_dc"] = {
        "estado": dc,
        "ciudades": [
            Ciudad.objects.create(nombre="Caracas", estado=dc),
        ],
    }

    return locations
