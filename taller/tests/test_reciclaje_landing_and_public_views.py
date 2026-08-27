"""
Tests para el storefront público de tenants RECYCLING sobre su dominio propio.

Contexto (Fase 355-356): landing_home() enrutaba TODO dominio personalizado a
catalog_home() (tema Commerce de MonteAzul), incluso para tenants sin Commerce
configurado (Atlanta Reciclajes) — mostrando una tienda vacía en vez de la
landing real del negocio. Se corrigió agregando una rama por rubro
(ConfiguracionEmpresa.rubro_principal == "RECYCLING") antes de caer a
catalog_home, y se agregó taller/reciclaje/ con las vistas públicas de
consulta de catalíticos y catálogo de chatarra (sobre los modelos
TenantScoped ya existentes en taller/models/reciclaje.py).

Cubre:
    - landing_home: dominio RECYCLING -> bienvenida_atlanta.html.
    - landing_home: dominio no-RECYCLING -> sigue cayendo a catalog_home
      (comportamiento sin cambios, ej. MonteAzul).
    - Aislamiento multi-tenant de las vistas públicas nuevas
      (consulta_catalitico, api_consulta_sugerencias, detalle_catalitico,
      catalogo_chatarra): una empresa nunca ve datos de otra.
"""

from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client

from taller.models.empresa_dominio import EmpresaDominio
from taller.models.reciclaje import PrecioMetal
from taller.tests.factories import (
    CataliticoFactory,
    ConfiguracionEmpresaFactory,
    EmpresaFactory,
    ProductoChatarraFactory,
)


@pytest.fixture(autouse=True)
def _clear_domain_cache():
    cache.clear()
    yield
    cache.clear()


def _empresa_con_dominio(*, username, dominio, rubro_principal="WORKSHOP"):
    user = User.objects.create_user(username, f"{username}@example.com", "pass")
    empresa = EmpresaFactory(user=user, nombre_taller=username, pais="CL")
    ConfiguracionEmpresaFactory(empresa=empresa, rubro_principal=rubro_principal)
    EmpresaDominio.objects.create(
        empresa=empresa,
        dominio=dominio,
        estado=EmpresaDominio.Estado.ACTIVO,
    )
    return empresa


@pytest.fixture
def empresa_recycling(db):
    return _empresa_con_dominio(
        username="reciclaje_landing_owner",
        dominio="landing-recycling.example.cl",
        rubro_principal="RECYCLING",
    )


@pytest.fixture
def empresa_workshop(db):
    return _empresa_con_dominio(
        username="reciclaje_landing_otro",
        dominio="landing-workshop.example.cl",
        rubro_principal="WORKSHOP",
    )


# ── landing_home ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_landing_home_dominio_recycling_muestra_bienvenida_atlanta(empresa_recycling):
    client = Client(HTTP_HOST="landing-recycling.example.cl")
    response = client.get("/")

    assert response.status_code == 200
    assert [t.name for t in response.templates if t.name] == [
        "taller/reciclaje/bienvenida_atlanta.html"
    ]
    content = response.content.decode()
    assert "Bienvenido a Atlanta Reciclajes" in content
    assert "/reciclaje/cataliticos/" in content
    assert "/reciclaje/chatarra/" in content


@pytest.mark.django_db
def test_landing_home_dominio_no_recycling_sigue_usando_catalog_home(empresa_workshop):
    """Regresión: un tenant que no es RECYCLING (ej. MonteAzul) debe seguir
    cayendo en el flujo de Commerce sin cambios."""
    client = Client(HTTP_HOST="landing-workshop.example.cl")
    response = client.get("/")

    assert response.status_code == 200
    assert "Bienvenido a Atlanta Reciclajes" not in response.content.decode()
    assert "commerce/themes/monteazul/home.html" in [
        t.name for t in response.templates if t.name
    ]


# ── landing_cataliticos ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_landing_cataliticos_responde_200_con_contenido_y_cta(empresa_recycling):
    """La 'sección Catalíticos' es una bienvenida propia con contenido real
    (qué es un catalítico, cómo funciona la compra, cómo se recuperan los
    metales) y un CTA hacia la consulta de precio — no debe saltar directo
    a la búsqueda ni quedar pobre en contenido."""
    client = Client(HTTP_HOST="landing-recycling.example.cl")
    response = client.get("/reciclaje/cataliticos/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Catalíticos" in content
    assert "Pago al Contado" in content
    assert "¿Qué es un catalítico" in content
    assert "¿Cómo funciona la compra?" in content
    assert "¿Cómo se recuperan los metales?" in content
    assert "/reciclaje/consulta-catalitico/" in content
    assert "/accounts/login/" in content


@pytest.mark.django_db
def test_landing_cataliticos_sin_precios_metal_no_muestra_seccion(empresa_recycling):
    client = Client(HTTP_HOST="landing-recycling.example.cl")
    response = client.get("/reciclaje/cataliticos/")

    assert response.status_code == 200
    assert "Valor Referencial de Metales Preciosos" not in response.content.decode()


@pytest.mark.django_db
def test_landing_cataliticos_con_precios_metal_los_muestra(empresa_recycling):
    PrecioMetal.objects.create(
        empresa=empresa_recycling,
        platino=Decimal("30000.00"),
        paladio=Decimal("25000.00"),
        rodio=Decimal("120000.00"),
    )
    client = Client(HTTP_HOST="landing-recycling.example.cl")
    response = client.get("/reciclaje/cataliticos/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Valor Referencial de Metales Preciosos" in content
    assert "Platino" in content
    assert "30.000" in content or "30000" in content
    # Rodio es el mayor (120000) -> su barra debe ir al 100%; platino
    # (30000/120000) -> 25%.
    assert 'class="metal-bar rodio" style="width: 100%;"' in content
    assert 'class="metal-bar" style="width: 25%;"' in content


@pytest.mark.django_db
def test_landing_cataliticos_precios_metal_de_otra_empresa_no_se_filtran(empresa_recycling):
    """Aislamiento multi-tenant: los precios de metales de otra empresa
    RECYCLING nunca deben aparecer en la landing de esta."""
    otra_empresa = _empresa_con_dominio(
        username="reciclaje_otro_precio_metal",
        dominio="otro-precio-metal.example.cl",
        rubro_principal="RECYCLING",
    )
    PrecioMetal.objects.create(empresa=otra_empresa, platino=Decimal("99999.00"))

    client = Client(HTTP_HOST="landing-recycling.example.cl")
    response = client.get("/reciclaje/cataliticos/")

    assert response.status_code == 200
    assert "99.999" not in response.content.decode() and "99999" not in response.content.decode()


@pytest.mark.django_db
def test_landing_cataliticos_muestra_panel_si_esta_autenticado(empresa_recycling):
    client = Client(HTTP_HOST="landing-recycling.example.cl")
    client.force_login(empresa_recycling.user)
    response = client.get("/reciclaje/cataliticos/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "/cl/es/reciclaje/" in content
    assert "/accounts/login/" not in content


@pytest.mark.django_db
def test_landing_cataliticos_404_sin_tenant_resuelto(db):
    client = Client(HTTP_HOST="sin-tenant.example.cl")
    response = client.get("/reciclaje/cataliticos/")
    assert response.status_code == 404


# ── vistas públicas: aislamiento multi-tenant ────────────────────────────────


@pytest.fixture
def empresa_a(db):
    return _empresa_con_dominio(
        username="reciclaje_pub_a",
        dominio="pub-a.example.cl",
        rubro_principal="RECYCLING",
    )


@pytest.fixture
def empresa_b(db):
    return _empresa_con_dominio(
        username="reciclaje_pub_b",
        dominio="pub-b.example.cl",
        rubro_principal="RECYCLING",
    )


@pytest.mark.django_db
def test_consulta_catalitico_no_muestra_resultados_de_otra_empresa(empresa_a, empresa_b):
    CataliticoFactory(empresa=empresa_a, codigo="COMPARTIDO-1", nombre="Toyota Corolla")
    CataliticoFactory(empresa=empresa_b, codigo="COMPARTIDO-1", nombre="Toyota Corolla")

    client = Client(HTTP_HOST="pub-a.example.cl")
    response = client.get("/reciclaje/consulta-catalitico/", {"codigo": "COMPARTIDO-1"})

    assert response.status_code == 200
    assert response.context["resultado"].empresa_id == empresa_a.pk


@pytest.mark.django_db
def test_api_consulta_sugerencias_aislada_por_empresa(empresa_a, empresa_b):
    CataliticoFactory(empresa=empresa_a, codigo="SUG-A")
    CataliticoFactory(empresa=empresa_b, codigo="SUG-A-OTRO")

    client = Client(HTTP_HOST="pub-a.example.cl")
    response = client.get(
        "/reciclaje/api/consulta-sugerencias/", {"term": "SUG-A"}
    )

    assert response.status_code == 200
    codigos = [r["codigo"] for r in response.json()["results"]]
    assert codigos == ["SUG-A"]


@pytest.mark.django_db
def test_api_consulta_sugerencias_no_expone_precio_compra(empresa_a):
    from decimal import Decimal

    CataliticoFactory(
        empresa=empresa_a,
        codigo="PRIV-1",
        precio_compra=Decimal("10000.00"),
        precio_venta=Decimal("30000.00"),
    )

    client = Client(HTTP_HOST="pub-a.example.cl")
    response = client.get(
        "/reciclaje/api/consulta-sugerencias/", {"term": "PRIV-1"}
    )

    body = response.content.decode()
    assert "10000" not in body
    assert response.json()["results"][0]["precio_referencia"] == 30000.0


@pytest.mark.django_db
def test_detalle_catalitico_404_para_catalitico_de_otra_empresa(empresa_a, empresa_b):
    otro = CataliticoFactory(empresa=empresa_b)

    client = Client(HTTP_HOST="pub-a.example.cl")
    response = client.get(f"/reciclaje/catalitico/{otro.pk}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_catalogo_chatarra_no_muestra_productos_de_otra_empresa(empresa_a, empresa_b):
    ProductoChatarraFactory(empresa=empresa_a, nombre="Cobre A")
    ProductoChatarraFactory(empresa=empresa_b, nombre="Cobre B")

    client = Client(HTTP_HOST="pub-a.example.cl")
    response = client.get("/reciclaje/chatarra/")

    nombres = [p.nombre for p in response.context["page_obj"].object_list]
    assert nombres == ["Cobre A"]
