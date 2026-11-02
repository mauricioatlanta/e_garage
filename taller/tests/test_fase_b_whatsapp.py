"""
Tests FASE B — Flujo WhatsApp Vendedor → Owner.

Cubre la vista avisar_owner_pieza:
  GET /cl/es/desarme/piezas/<pk>/avisar-owner/
  → 302 redirect a https://wa.me/<phone>?text=...

Estrategia: Client HTTP sobre vistas reales (mismo patrón que test_permisos_rbac.py).
"""
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, User
from django.test import Client

from taller.models import Empresa
from taller.models.pieza_desarme import PiezaDesarme
from taller.models.team_member import TeamMember
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empresa_cl(db):
    """Empresa Chile con owner y teléfono."""
    from taller.tests.factories import EmpresaFactory
    owner = User.objects.create_user("owner_wb", "owner@wb.com", "pass1234")
    owner.first_name = "Carlos"
    owner.last_name = "Dueño"
    owner.save()
    grupo_owner, _ = Group.objects.get_or_create(name="Owner")
    owner.groups.add(grupo_owner)
    empresa = EmpresaFactory(user=owner, nombre_taller="Taller WB", pais="CL", telefono="+56912345678")
    return empresa, owner


@pytest.fixture
def empresa_usa(db):
    """Empresa USA con owner y teléfono (para test de formato precio)."""
    from taller.tests.factories import EmpresaFactory
    owner = User.objects.create_user("owner_usa", "owner@usa.com", "pass1234")
    grupo_owner, _ = Group.objects.get_or_create(name="Owner")
    owner.groups.add(grupo_owner)
    empresa = EmpresaFactory(user=owner, nombre_taller="Garage USA", pais="US", moneda="USD", telefono="+12025551234")
    return empresa, owner


@pytest.fixture
def empresa_sin_telefono(db):
    """Empresa Chile SIN teléfono (para test de error)."""
    from taller.tests.factories import EmpresaFactory
    owner = User.objects.create_user("owner_noph", "owner_noph@wb.com", "pass1234")
    grupo_owner, _ = Group.objects.get_or_create(name="Owner")
    owner.groups.add(grupo_owner)
    empresa = EmpresaFactory(user=owner, nombre_taller="Taller Sin Tel", pais="CL", telefono="")
    return empresa, owner


@pytest.fixture
def vendedor_user(db, empresa_cl):
    """Usuario Vendedor (TeamMember) de empresa_cl."""
    empresa, _ = empresa_cl
    user = User.objects.create_user("vendedor_wb", "vendedor@wb.com", "pass1234")
    user.first_name = "Juan"
    user.last_name = "Vendedor"
    user.save()
    TeamMember.objects.create(user=user, empresa=empresa, rol="Vendedor")
    return user


@pytest.fixture
def admin_user(db, empresa_cl):
    """Usuario Admin (TeamMember) de empresa_cl."""
    empresa, _ = empresa_cl
    user = User.objects.create_user("admin_wb", "admin@wb.com", "pass1234")
    TeamMember.objects.create(user=user, empresa=empresa, rol="Admin")
    return user


@pytest.fixture
def vehiculo_cl(db, empresa_cl):
    """Vehículo de desarme perteneciente a empresa_cl."""
    empresa, _ = empresa_cl
    return VehiculoDesarme.objects.create(
        empresa=empresa,
        patente="ABCD12",
    )


@pytest.fixture
def pieza_cl(db, empresa_cl, vehiculo_cl):
    """PiezaDesarme con precio en empresa CL."""
    empresa, _ = empresa_cl
    return PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo_cl,
        codigo="MOT-01",
        nombre="Motor V8",
        precio_venta_sugerido=Decimal("150000"),
    )


@pytest.fixture
def pieza_sin_precio(db, empresa_cl, vehiculo_cl):
    """PiezaDesarme sin precio sugerido."""
    empresa, _ = empresa_cl
    return PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo_cl,
        codigo="RUE-01",
        nombre="Rueda delantera",
        precio_venta_sugerido=None,
    )


@pytest.fixture
def pieza_usa(db, empresa_usa):
    """PiezaDesarme en empresa USA para test de formato precio."""
    empresa, _ = empresa_usa
    vehiculo = VehiculoDesarme.objects.create(
        empresa=empresa,
        patente="USA001",
    )
    return PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        codigo="ENG-01",
        nombre="Engine V8",
        precio_venta_sugerido=Decimal("150000"),
    )


@pytest.fixture
def pieza_otra_empresa(db):
    """PiezaDesarme de otra empresa (para test de tenant isolation)."""
    from taller.tests.factories import EmpresaFactory
    otra_empresa = EmpresaFactory(nombre_taller="Otro Taller", pais="CL", telefono="+56900000000")
    vehiculo = VehiculoDesarme.objects.create(
        empresa=otra_empresa,
        patente="OTR001",
    )
    return PiezaDesarme.objects.create(
        empresa=otra_empresa,
        vehiculo_desarme=vehiculo,
        codigo="OTR-01",
        nombre="Pieza ajena",
    )


def _url(pk):
    return f"/cl/es/desarme/piezas/{pk}/avisar-owner/"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_vendedor_puede_avisar_owner(db, vendedor_user, pieza_cl):
    """Vendedor GET → 302 redirect cuya Location comienza con wa.me."""
    c = Client()
    c.login(username="vendedor_wb", password="pass1234")
    response = c.get(_url(pieza_cl.pk))
    assert response.status_code == 302
    location = response["Location"]
    assert "wa.me/" in location


def test_admin_puede_avisar_owner(db, admin_user, pieza_cl):
    """Admin también puede avisar al owner."""
    c = Client()
    c.login(username="admin_wb", password="pass1234")
    response = c.get(_url(pieza_cl.pk))
    assert response.status_code == 302
    assert "wa.me/" in response["Location"]


def test_owner_puede_avisar(db, empresa_cl, pieza_cl):
    """Owner puede usar la vista (por si quiere avisar desde otro dispositivo)."""
    _, owner = empresa_cl
    c = Client()
    c.login(username="owner_wb", password="pass1234")
    response = c.get(_url(pieza_cl.pk))
    assert response.status_code == 302
    assert "wa.me/" in response["Location"]


def test_url_whatsapp_contiene_datos_pieza(db, vendedor_user, pieza_cl):
    """URL de WhatsApp incluye código y nombre de la pieza."""
    c = Client()
    c.login(username="vendedor_wb", password="pass1234")
    response = c.get(_url(pieza_cl.pk))
    location = response["Location"]
    assert "MOT-01" in location
    assert "Motor" in location


def test_url_whatsapp_contiene_phone_owner(db, vendedor_user, pieza_cl):
    """URL wa.me usa el teléfono de la empresa (solo dígitos)."""
    c = Client()
    c.login(username="vendedor_wb", password="pass1234")
    response = c.get(_url(pieza_cl.pk))
    location = response["Location"]
    # +56912345678 → 56912345678
    assert "wa.me/56912345678" in location


def test_url_whatsapp_contiene_contacto_vendedor(db, vendedor_user, pieza_cl):
    """URL incluye nombre y email del Vendedor en el mensaje."""
    c = Client()
    c.login(username="vendedor_wb", password="pass1234")
    response = c.get(_url(pieza_cl.pk))
    location = response["Location"]
    assert "vendedor%40wb.com" in location or "vendedor@wb.com" in location


def test_formato_precio_cl(db, vendedor_user, pieza_cl):
    """Precio CL: punto como separador de miles → $150.000."""
    c = Client()
    c.login(username="vendedor_wb", password="pass1234")
    response = c.get(_url(pieza_cl.pk))
    location = response["Location"]
    # $150.000 aparece URL-encoded: %24150.000 o $150.000
    assert "150.000" in location


def test_formato_precio_usa(db, empresa_usa, pieza_usa):
    """Precio USA: coma como separador de miles → $150,000.00."""
    _, owner = empresa_usa
    c = Client()
    c.login(username="owner_usa", password="pass1234")
    response = c.get(_url(pieza_usa.pk))
    location = response["Location"]
    # $150,000.00 URL-encoded: coma → %2C
    assert "150%2C000.00" in location or "150,000.00" in location


def test_pieza_sin_precio_muestra_no_especificado(db, vendedor_user, pieza_sin_precio):
    """Pieza sin precio → mensaje incluye 'No especificado'."""
    c = Client()
    c.login(username="vendedor_wb", password="pass1234")
    response = c.get(_url(pieza_sin_precio.pk))
    assert response.status_code == 302
    assert "No+especificado" in response["Location"] or "No%20especificado" in response["Location"] or "No especificado" in response["Location"]


def test_owner_sin_telefono_muestra_error(db, empresa_sin_telefono, vehiculo_cl=None):
    """Owner sin teléfono → 302 a lista_piezas con mensaje de error."""
    empresa, owner = empresa_sin_telefono
    vehiculo = VehiculoDesarme.objects.create(
        empresa=empresa,
        patente="NOPH01",
    )
    pieza = PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        codigo="NOPH-01",
        nombre="Pieza sin tel",
    )
    c = Client()
    c.login(username="owner_noph", password="pass1234")
    response = c.get(f"/cl/es/desarme/piezas/{pieza.pk}/avisar-owner/")
    assert response.status_code == 302
    # No redirige a wa.me
    assert "wa.me" not in response["Location"]


def test_usuario_diferente_empresa_bloqueado(db, vendedor_user, pieza_otra_empresa):
    """Vendedor de empresa A no puede avisar sobre pieza de empresa B (tenant isolation)."""
    c = Client()
    c.login(username="vendedor_wb", password="pass1234")
    response = c.get(_url(pieza_otra_empresa.pk))
    assert response.status_code == 302
    assert "wa.me" not in response["Location"]


def test_anonimo_redirigido_a_login(db, pieza_cl):
    """Sin sesión → 302 hacia /login o /accounts/login."""
    c = Client()
    response = c.get(_url(pieza_cl.pk))
    assert response.status_code == 302
    location = response["Location"]
    assert "login" in location.lower()
