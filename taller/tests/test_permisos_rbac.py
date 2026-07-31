"""
Tests RBAC — Fase A: bloqueo de vistas por rol.

Estrategia:
  - Tests de bloqueo (Vendedor → 403): Client HTTP sobre vistas reales.
  - Tests de acceso (Owner/Admin → no 403):
      * Tests unitarios sobre los helpers RBAC (evitan renderizado de templates).
      * Tests de integración sobre endpoints JSON/redirect (sin template, sin bug Py3.14).
"""
import json
import pytest
from django.contrib.auth.models import User, Group
from django.test import Client

from taller.models import Empresa
from taller.models.team_member import TeamMember

# ---------------------------------------------------------------------------
# URLs bajo prueba
# ---------------------------------------------------------------------------
URL_CREAR_PIEZA = "/cl/es/desarme/piezas/crear/"
URL_CREAR_PIEZA_SUELTA = "/cl/es/desarme/piezas/nueva-suelta/"
URL_EDITAR_PIEZA = "/cl/es/desarme/piezas/9999/editar/"  # pk ficticio: 403 llega antes del 404
URL_API_BULK_ESTADO = "/cl/es/desarme/api/piezas/bulk-estado/"
URL_API_BULK_PRECIO = "/cl/es/desarme/api/piezas/bulk-precio/"
URL_CREAR_DOCUMENTO = "/cl/documentos/form/"
URL_EDITAR_DOCUMENTO = "/cl/documentos/form/9999/"  # pk ficticio: 403 llega antes del 404


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empresa_test(db):
    """Empresa base con su Owner."""
    from taller.tests.factories import EmpresaFactory
    owner = User.objects.create_user("owner_rbac", "owner@rbac.com", "pass1234")
    empresa = EmpresaFactory(user=owner, nombre_taller="Taller RBAC", pais="CL")
    grupo_owner, _ = Group.objects.get_or_create(name="Owner")
    owner.groups.add(grupo_owner)
    return empresa, owner


@pytest.fixture
def vendedor_user(db, empresa_test):
    """Usuario con rol Vendedor. TeamMember.save() agrega el grupo Django 'Vendedor'."""
    empresa, _ = empresa_test
    user = User.objects.create_user("vendedor_rbac", "vendedor@rbac.com", "pass1234")
    TeamMember.objects.create(user=user, empresa=empresa, rol="Vendedor")
    return user


@pytest.fixture
def admin_user(db, empresa_test):
    """Usuario con rol Admin. TeamMember.save() agrega el grupo Django 'Admin'."""
    empresa, _ = empresa_test
    user = User.objects.create_user("admin_rbac", "admin@rbac.com", "pass1234")
    TeamMember.objects.create(user=user, empresa=empresa, rol="Admin")
    return user


@pytest.fixture
def owner_user(db, empresa_test):
    """Owner de la empresa (tiene grupo 'Owner' y Empresa.user = él)."""
    _, owner = empresa_test
    return owner


@pytest.fixture
def client_vendedor(vendedor_user):
    c = Client()
    c.login(username="vendedor_rbac", password="pass1234")
    return c


@pytest.fixture
def client_owner(owner_user):
    c = Client()
    c.login(username="owner_rbac", password="pass1234")
    return c


@pytest.fixture
def client_admin(admin_user):
    c = Client()
    c.login(username="admin_rbac", password="pass1234")
    return c


# ---------------------------------------------------------------------------
# BLOQUE 1: Vendedor bloqueado con 403
# ---------------------------------------------------------------------------

def test_vendedor_no_puede_crear_pieza(client_vendedor):
    """Vendedor GET /crear/ → 403 Forbidden."""
    response = client_vendedor.get(URL_CREAR_PIEZA)
    assert response.status_code == 403


def test_vendedor_no_puede_crear_pieza_suelta(client_vendedor):
    """Vendedor GET /nueva-suelta/ → 403."""
    response = client_vendedor.get(URL_CREAR_PIEZA_SUELTA)
    assert response.status_code == 403


def test_vendedor_no_puede_editar_pieza(client_vendedor):
    """Vendedor GET /piezas/9999/editar/ → 403 (RBAC antes de buscar pk)."""
    response = client_vendedor.get(URL_EDITAR_PIEZA)
    assert response.status_code == 403


def test_vendedor_no_puede_api_bulk_estado(client_vendedor):
    """Vendedor POST al API bulk-estado → 403."""
    payload = json.dumps({"ids": [1, 2], "estado": "DISPONIBLE"})
    response = client_vendedor.post(
        URL_API_BULK_ESTADO, data=payload, content_type="application/json"
    )
    assert response.status_code == 403


def test_vendedor_no_puede_api_bulk_precio(client_vendedor):
    """Vendedor POST al API bulk-precio → 403."""
    payload = json.dumps({"ids": [1], "factor": 1.1})
    response = client_vendedor.post(
        URL_API_BULK_PRECIO, data=payload, content_type="application/json"
    )
    assert response.status_code == 403


def test_vendedor_no_puede_crear_documento(client_vendedor):
    """Vendedor GET /documentos/form/ → 403."""
    response = client_vendedor.get(URL_CREAR_DOCUMENTO)
    assert response.status_code == 403


def test_vendedor_no_puede_editar_documento(client_vendedor):
    """Vendedor GET /documentos/form/9999/ → 403 (RBAC antes de buscar pk)."""
    response = client_vendedor.get(URL_EDITAR_DOCUMENTO)
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# BLOQUE 2: Owner y Admin — tests unitarios del helper RBAC
# (Evitan renderizado de HTML para sortear bug Py3.14/Django4.2 en test client)
# ---------------------------------------------------------------------------

def test_owner_pasa_is_admin_or_owner(owner_user, empresa_test):
    """is_admin_or_owner() retorna True para Owner (grupo + Empresa directa)."""
    from taller.auth.decorators_role import is_admin_or_owner
    assert is_admin_or_owner(owner_user) is True


def test_admin_pasa_is_admin_or_owner(admin_user, empresa_test):
    """is_admin_or_owner() retorna True para Admin (grupo 'Admin' vía TeamMember)."""
    from taller.auth.decorators_role import is_admin_or_owner
    assert is_admin_or_owner(admin_user) is True


def test_vendedor_falla_is_admin_or_owner(vendedor_user, empresa_test):
    """is_admin_or_owner() retorna False para Vendedor."""
    from taller.auth.decorators_role import is_admin_or_owner
    assert is_admin_or_owner(vendedor_user) is False


# ---------------------------------------------------------------------------
# BLOQUE 3: Owner y Admin — integración con endpoint JSON (sin template HTML)
# Los endpoints API devuelven JSON → no hay template context copy → no bug Py3.14
# ---------------------------------------------------------------------------

def test_owner_pasa_rbac_api_bulk_estado(client_owner, empresa_test):
    """Owner POST al API bulk-estado → pasa RBAC (no 403). JSON endpoint."""
    payload = json.dumps({"ids": [9999], "estado": "DISPONIBLE"})
    response = client_owner.post(
        URL_API_BULK_ESTADO, data=payload, content_type="application/json"
    )
    assert response.status_code != 403, (
        f"Owner no debería recibir 403, obtuvo {response.status_code}"
    )


def test_admin_pasa_rbac_api_bulk_estado(client_admin, empresa_test):
    """Admin POST al API bulk-estado → RBAC pasa.
    La vista puede devolver 403 JSON si Admin no tiene Empresa directa
    (request.user.empresa es OneToOne del Owner), pero ese 403 viene del
    cuerpo de la vista, NO del decorador @role_required.
    Distinguimos: RBAC 403 devuelve HTML; view-body 403 devuelve JSON."""
    payload = json.dumps({"ids": [9999], "estado": "DISPONIBLE"})
    response = client_admin.post(
        URL_API_BULK_ESTADO, data=payload, content_type="application/json"
    )
    if response.status_code == 403:
        content_type = response.get("Content-Type", "")
        assert "application/json" in content_type, (
            f"Admin recibió 403 del RBAC (HTML), pero debería haber pasado el check. "
            f"Content-Type: {content_type!r}"
        )


# ---------------------------------------------------------------------------
# BLOQUE 4: Anónimo → redirect al login (no 403)
# ---------------------------------------------------------------------------

def test_anonimo_redirige_a_login_en_crear_pieza(db):
    """Anónimo recibe 302 → login (no 403). @login_required va antes de @role_required."""
    c = Client()
    response = c.get(URL_CREAR_PIEZA)
    assert response.status_code == 302


def test_anonimo_redirige_a_login_en_crear_documento(db):
    """Anónimo recibe 302 → login en DocumentoCreateView."""
    c = Client()
    response = c.get(URL_CREAR_DOCUMENTO)
    assert response.status_code == 302
