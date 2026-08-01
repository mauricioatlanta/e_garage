"""Fixtures comunes para los tests de Commerce Engine."""
import pytest
from taller.tests.factories import EmpresaFactory, RepuestoFactory
from commerce.models import CommerceCategory, CommerceProduct
from django.utils.text import slugify


@pytest.fixture
def empresa(db):
    return EmpresaFactory(nombre_taller="MonteAzul", pais="CL")


@pytest.fixture
def empresa_b(db):
    return EmpresaFactory(nombre_taller="Otro Taller", pais="CL")


def make_category(empresa, name="Categoría Test", slug=None):
    n = CommerceCategory.objects.count()
    return CommerceCategory.objects.create(
        empresa=empresa,
        name=name,
        slug=slug or f"{slugify(name)}-{n}",
        is_active=True,
    )


def make_product(empresa, repuesto=None, category=None, publishable=True):
    if repuesto is None:
        repuesto = RepuestoFactory(empresa=empresa)
    return CommerceProduct.objects.create(
        empresa=empresa,
        repuesto=repuesto,
        category=category,
        slug=slugify(repuesto.nombre),
        is_publishable=publishable,
        meta_title=repuesto.nombre[:70],
        meta_description="",
    )
