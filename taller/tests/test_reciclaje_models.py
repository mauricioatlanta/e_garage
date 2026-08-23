"""
Tests para el dominio de reciclaje (Atlanta Reciclajes — Fase 1):
CategoriaChatarra, ProductoChatarra, Catalitico.

Cubre:
  - Rubro RECYCLING presente en la fuente canónica y con perfil de producto.
  - empresa obligatoria (TenantScoped, FK NOT NULL).
  - UniqueConstraint(empresa, codigo) por modelo, y aislamiento entre empresas.
"""
from decimal import Decimal

import pytest
from django.db import IntegrityError

from taller.constants.product_profiles import PRODUCT_PROFILES, RUBRO_TO_PRODUCT
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.reciclaje import Catalitico, CategoriaChatarra, ProductoChatarra
from taller.tests.factories import (
    CataliticoFactory,
    CategoriaChatarraFactory,
    EmpresaFactory,
    ProductoChatarraFactory,
)

# ---------------------------------------------------------------------------
# Rubro RECYCLING
# ---------------------------------------------------------------------------

def test_recycling_esta_en_rubro_choices():
    values = [value for value, _ in ConfiguracionEmpresa.RUBRO_CHOICES]
    assert "RECYCLING" in values


def test_recycling_tiene_perfil_de_producto():
    product_key = RUBRO_TO_PRODUCT.get("RECYCLING")
    assert product_key is not None
    assert product_key in PRODUCT_PROFILES


# ---------------------------------------------------------------------------
# CategoriaChatarra
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCategoriaChatarra:
    def test_requiere_empresa(self):
        with pytest.raises(IntegrityError):
            CategoriaChatarra.objects.create(nombre="Cobre")

    def test_nombre_unico_por_empresa(self):
        empresa = EmpresaFactory()
        CategoriaChatarraFactory(empresa=empresa, nombre="Cobre")
        with pytest.raises(IntegrityError):
            CategoriaChatarraFactory(empresa=empresa, nombre="Cobre")

    def test_mismo_nombre_permitido_entre_empresas_distintas(self):
        empresa_a = EmpresaFactory()
        empresa_b = EmpresaFactory()
        CategoriaChatarraFactory(empresa=empresa_a, nombre="Cobre")
        # No debe lanzar — el constraint está scoped por empresa.
        CategoriaChatarraFactory(empresa=empresa_b, nombre="Cobre")
        assert CategoriaChatarra.objects.filter(nombre="Cobre").count() == 2


# ---------------------------------------------------------------------------
# ProductoChatarra
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProductoChatarra:
    def test_requiere_empresa(self):
        with pytest.raises(IntegrityError):
            ProductoChatarra.objects.create(codigo="CU-01", nombre="Cable de cobre")

    def test_codigo_unico_por_empresa(self):
        empresa = EmpresaFactory()
        ProductoChatarraFactory(empresa=empresa, codigo="CU-01")
        with pytest.raises(IntegrityError):
            ProductoChatarraFactory(empresa=empresa, codigo="CU-01")

    def test_mismo_codigo_permitido_entre_empresas_distintas(self):
        empresa_a = EmpresaFactory()
        empresa_b = EmpresaFactory()
        ProductoChatarraFactory(empresa=empresa_a, codigo="CU-01")
        ProductoChatarraFactory(empresa=empresa_b, codigo="CU-01")
        assert ProductoChatarra.objects.filter(codigo="CU-01").count() == 2

    def test_categoria_es_de_la_misma_empresa_o_se_deja_sin_categorizar(self):
        empresa = EmpresaFactory()
        categoria = CategoriaChatarraFactory(empresa=empresa, nombre="Aluminio")
        producto = ProductoChatarraFactory(
            empresa=empresa,
            categoria=categoria,
            unidad_medida=ProductoChatarra.UNIDAD_KG,
            cantidad_stock=Decimal("25.500"),
        )
        assert producto.categoria_id == categoria.id
        assert producto.cantidad_stock == Decimal("25.500")


# ---------------------------------------------------------------------------
# Catalitico
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCatalitico:
    def test_requiere_empresa(self):
        with pytest.raises(IntegrityError):
            Catalitico.objects.create(codigo="CAT-01")

    def test_codigo_unico_por_empresa(self):
        empresa = EmpresaFactory()
        CataliticoFactory(empresa=empresa, codigo="CAT-01")
        with pytest.raises(IntegrityError):
            CataliticoFactory(empresa=empresa, codigo="CAT-01")

    def test_mismo_codigo_permitido_entre_empresas_distintas(self):
        empresa_a = EmpresaFactory()
        empresa_b = EmpresaFactory()
        CataliticoFactory(empresa=empresa_a, codigo="CAT-01")
        CataliticoFactory(empresa=empresa_b, codigo="CAT-01")
        assert Catalitico.objects.filter(codigo="CAT-01").count() == 2

    def test_estado_por_defecto_disponible(self):
        catalitico = CataliticoFactory()
        assert catalitico.estado == Catalitico.ESTADO_DISPONIBLE

    def test_no_tiene_imagen_por_defecto(self):
        """Fase 1: no se importan las 146 imágenes huérfanas todavía."""
        catalitico = CataliticoFactory()
        assert not catalitico.imagen
