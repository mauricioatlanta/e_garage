# -*- coding: utf-8 -*-
"""
Tests para el constraint unique_codigo_por_empresa_vehiculo_desarme en PiezaDesarme.

Cubre:
- Mismo empresa+vehiculo_desarme+codigo → IntegrityError en BD
- Mismo empresa+codigo pero distinto vehiculo_desarme → permitido (caso normal de catálogo)
- Pieza suelta con código manual → no colisiona porque cada suelta tiene vehiculo_desarme propio
"""
import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError

from taller.models.empresa import Empresa
from taller.models.pieza_desarme import PiezaDesarme
from taller.models.vehiculo_desarme import VehiculoDesarme


@pytest.fixture
def empresa_y_user(db):
    from taller.tests.factories import EmpresaFactory
    empresa = EmpresaFactory(nombre_taller="Taller Código Test", pais="CL", plan="paid")
    return empresa, empresa.user


@pytest.fixture
def vehiculo_1(empresa_y_user):
    empresa, _ = empresa_y_user
    return VehiculoDesarme.objects.create(
        empresa=empresa,
        patente="TST-001",
        anio=2019,
    )


@pytest.fixture
def vehiculo_2(empresa_y_user):
    empresa, _ = empresa_y_user
    return VehiculoDesarme.objects.create(
        empresa=empresa,
        patente="TST-002",
        anio=2020,
    )


@pytest.mark.django_db
class TestPiezaCodigoUnico:

    def test_codigo_duplicado_mismo_vehiculo_falla(self, empresa_y_user, vehiculo_1):
        """
        Mismo empresa+vehiculo_desarme+codigo → IntegrityError.
        Es el caso de entrada manual que antes causaría 500.
        """
        empresa, _ = empresa_y_user
        PiezaDesarme.objects.create(
            empresa=empresa,
            vehiculo_desarme=vehiculo_1,
            codigo="MOT-01",
            nombre="Motor original",
            cantidad=1,
        )
        with pytest.raises(IntegrityError):
            PiezaDesarme.objects.create(
                empresa=empresa,
                vehiculo_desarme=vehiculo_1,
                codigo="MOT-01",
                nombre="Motor duplicado",
                cantidad=1,
            )

    def test_codigo_igual_distinto_vehiculo_permitido(self, empresa_y_user, vehiculo_1, vehiculo_2):
        """
        Mismo empresa+codigo pero distinto vehiculo_desarme → permitido.
        Es el caso normal del catálogo: cada vehículo tiene su CAR-01, MOT-01, etc.
        """
        empresa, _ = empresa_y_user
        p1 = PiezaDesarme.objects.create(
            empresa=empresa,
            vehiculo_desarme=vehiculo_1,
            codigo="CAR-01",
            nombre="Capó vehículo 1",
            cantidad=1,
        )
        p2 = PiezaDesarme.objects.create(
            empresa=empresa,
            vehiculo_desarme=vehiculo_2,
            codigo="CAR-01",
            nombre="Capó vehículo 2",
            cantidad=1,
        )
        assert p1.pk != p2.pk
        assert PiezaDesarme.objects.filter(empresa=empresa, codigo="CAR-01").count() == 2

    def test_pieza_suelta_codigo_manual_no_colisiona(self, empresa_y_user):
        """
        Dos piezas sueltas con el mismo código manual no colisionan porque cada
        suelta tiene su propio vehiculo_desarme placeholder.
        """
        import uuid
        empresa, _ = empresa_y_user

        for i in range(2):
            veh = VehiculoDesarme.objects.create(
                empresa=empresa,
                patente=f"SLT-{uuid.uuid4().hex[:12]}",
                anio=2021,
            )
            PiezaDesarme.objects.create(
                empresa=empresa,
                vehiculo_desarme=veh,
                codigo="MI-CODIGO-123",
                nombre=f"Pieza suelta {i}",
                cantidad=1,
            )

        assert (
            PiezaDesarme.objects.filter(empresa=empresa, codigo="MI-CODIGO-123").count() == 2
        )
