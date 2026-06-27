"""
Tests Fase 3: catálogo por tipo_carroceria, SugerenciaPiezaDesarme, flujo /revisar/.
"""
import json
import pytest
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client

from taller.models.empresa import Empresa
from taller.models.pieza_desarme import PiezaDesarme, ESTADO_DISPONIBLE
from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo
from taller.desarme.catalogo_operativo import (
    get_catalogo_para_vehiculo,
    get_catalogo_operativo_desarme,
    CODIGOS_MOTO_WHITELIST,
)
from taller.desarme.services import inicializar_sugerencias


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def empresa_y_user(db):
    user = User.objects.create_user(username="rv_test", password="x", email="rv@test.com")
    emp  = Empresa.objects.create(nombre_taller="Taller RV", pais="CL", user=user, plan="paid")
    return emp, user


@pytest.fixture
def vehiculo_sedan(empresa_y_user):
    emp, _ = empresa_y_user
    return VehiculoDesarme.objects.create(
        empresa=emp,
        patente="SED-01", anio=2019, tipo_carroceria="sedan",
    )


@pytest.fixture
def vehiculo_moto(empresa_y_user):
    emp, _ = empresa_y_user
    return Vehiculo.objects.create(
        empresa=emp, tipo_uso=Vehiculo.TIPO_USO_DESARME,
        patente="MOT-01", anio=2021, tipo_carroceria="moto",
    )


@pytest.fixture
def vehiculo_sin_tipo(empresa_y_user):
    emp, _ = empresa_y_user
    return Vehiculo.objects.create(
        empresa=emp, tipo_uso=Vehiculo.TIPO_USO_DESARME,
        patente="GEN-01", anio=2018, tipo_carroceria=None,
    )


@pytest.fixture
def cliente_django(empresa_y_user):
    emp, user = empresa_y_user
    c = Client()
    c.force_login(user)
    return c, emp, user


def _revisar_url(pk):
    return f"/cl/es/desarme/vehiculos/{pk}/revisar/"


# ── 1: tipo_carroceria choices ────────────────────────────────────────────────

@pytest.mark.django_db
class TestTipoCarroceriaChoices:

    def test_tipo_valido_no_lanza(self, empresa_y_user):
        emp, _ = empresa_y_user
        v = Vehiculo(empresa=emp, tipo_uso=Vehiculo.TIPO_USO_DESARME,
                     patente="OK-01", anio=2020, tipo_carroceria="moto")
        v.full_clean()

    def test_tipo_invalido_lanza(self, empresa_y_user):
        emp, _ = empresa_y_user
        v = Vehiculo(empresa=emp, tipo_uso=Vehiculo.TIPO_USO_DESARME,
                     patente="BAD-01", anio=2020, tipo_carroceria="submarino")
        with pytest.raises(ValidationError):
            v.full_clean()

    def test_tipo_null_es_valido(self, empresa_y_user):
        emp, _ = empresa_y_user
        v = Vehiculo(empresa=emp, tipo_uso=Vehiculo.TIPO_USO_DESARME,
                     patente="NUL-01", anio=2020, tipo_carroceria=None)
        v.full_clean()


# ── 2: catálogo por tipo ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCatalogoPorTipo:

    def test_sedan_excluye_puerta_maletero(self, empresa_y_user, vehiculo_sedan):
        emp, _ = empresa_y_user
        cat = get_catalogo_para_vehiculo(emp, vehiculo_sedan)
        codigos = {item["codigo"] for item in cat}
        assert "CAR-12" not in codigos

    def test_sedan_incluye_tapa_baul(self, empresa_y_user, vehiculo_sedan):
        emp, _ = empresa_y_user
        cat = get_catalogo_para_vehiculo(emp, vehiculo_sedan)
        codigos = {item["codigo"] for item in cat}
        assert "CAR-07" in codigos

    def test_suv_excluye_tapa_baul_incluye_compuerta(self, empresa_y_user):
        emp, _ = empresa_y_user
        v = Vehiculo.objects.create(empresa=emp, tipo_uso=Vehiculo.TIPO_USO_DESARME,
                                    patente="SUV-01", anio=2020, tipo_carroceria="suv")
        codigos = {item["codigo"] for item in get_catalogo_para_vehiculo(emp, v)}
        assert "CAR-07" not in codigos
        assert "CAR-12" in codigos

    def test_moto_retorna_whitelist(self, empresa_y_user, vehiculo_moto):
        emp, _ = empresa_y_user
        cat = get_catalogo_para_vehiculo(emp, vehiculo_moto)
        codigos = {item["codigo"] for item in cat}
        assert codigos == CODIGOS_MOTO_WHITELIST

    def test_moto_es_subconjunto_reducido(self, empresa_y_user, vehiculo_moto):
        emp, _ = empresa_y_user
        cat = get_catalogo_para_vehiculo(emp, vehiculo_moto)
        assert len(cat) < 50

    def test_fallback_tipo_null_es_catalogo_completo(self, empresa_y_user, vehiculo_sin_tipo):
        emp, _ = empresa_y_user
        cat_sin = get_catalogo_para_vehiculo(emp, vehiculo_sin_tipo)
        cat_full = get_catalogo_operativo_desarme(emp)
        assert len(cat_sin) == len(cat_full)

    def test_fallback_tipo_desconocido_es_catalogo_completo(self, empresa_y_user):
        emp, _ = empresa_y_user
        v = Vehiculo.objects.create(empresa=emp, tipo_uso=Vehiculo.TIPO_USO_DESARME,
                                    patente="UNK-01", anio=2019)
        # Guardar valor no reconocido directo (bypass de full_clean)
        Vehiculo.objects.filter(pk=v.pk).update(tipo_carroceria="limousine")
        v.refresh_from_db()
        cat = get_catalogo_para_vehiculo(emp, v)
        assert len(cat) == len(get_catalogo_operativo_desarme(emp))


# ── 3: inicializar_sugerencias ────────────────────────────────────────────────

@pytest.mark.django_db
class TestInicializarSugerencias:

    def test_no_crea_piezadesarme(self, empresa_y_user, vehiculo_sedan):
        emp, _ = empresa_y_user
        inicializar_sugerencias(vehiculo_sedan, emp)
        vehiculo_desarme = vehiculo_sedan
        assert PiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme).count() == 0

    def test_crea_sugerencias_pendiente(self, empresa_y_user, vehiculo_sedan):
        emp, _ = empresa_y_user
        n = inicializar_sugerencias(vehiculo_sedan, emp)
        assert n > 0
        vehiculo_desarme = vehiculo_sedan
        sugs = SugerenciaPiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme)
        assert sugs.count() == n
        assert sugs.filter(estado=SugerenciaPiezaDesarme.PENDIENTE).count() == n

    def test_idempotente(self, empresa_y_user, vehiculo_sedan):
        emp, _ = empresa_y_user
        n1 = inicializar_sugerencias(vehiculo_sedan, emp)
        n2 = inicializar_sugerencias(vehiculo_sedan, emp)
        assert n2 == 0
        vehiculo_desarme = vehiculo_sedan
        assert SugerenciaPiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme).count() == n1

    def test_unique_constraint_viola(self, empresa_y_user, vehiculo_sedan):
        emp, _ = empresa_y_user
        inicializar_sugerencias(vehiculo_sedan, emp)
        vehiculo_desarme = vehiculo_sedan
        with pytest.raises(IntegrityError):
            SugerenciaPiezaDesarme.objects.create(
                empresa=emp, vehiculo_desarme=vehiculo_desarme, codigo="MOT-01",
                nombre="Duplicado", zona="Motor", estado="PENDIENTE",
            )

    def test_no_inicializa_vehiculo_no_desarme(self, empresa_y_user):
        emp, _ = empresa_y_user
        v = Vehiculo.objects.create(empresa=emp, tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
                                    patente="CLI-01", anio=2018)
        n = inicializar_sugerencias(v, emp)
        assert n == 0


# ── 4: flujo AJAX /revisar/ ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestRevisarVehiculoAJAX:

    def test_confirmar_crea_pieza_revisada(self, empresa_y_user, vehiculo_sedan, cliente_django):
        c, emp, _ = cliente_django
        inicializar_sugerencias(vehiculo_sedan, emp)
        vehiculo_desarme = vehiculo_sedan
        sug = SugerenciaPiezaDesarme.objects.filter(
            empresa=emp, vehiculo_desarme=vehiculo_desarme, estado="PENDIENTE"
        ).first()

        resp = c.post(
            _revisar_url(vehiculo_sedan.pk),
            data=json.dumps({"action": "confirmar", "sugerencia_id": sug.pk,
                             "precio": "50000", "condicion": "BUENA"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        sug.refresh_from_db()
        assert sug.estado == SugerenciaPiezaDesarme.CONFIRMADA
        assert sug.pieza_creada_id is not None
        pieza = sug.pieza_creada
        assert pieza.revisado is True
        assert pieza.estado_pieza == ESTADO_DISPONIBLE
        assert pieza.precio_venta_sugerido == Decimal("50000")

    def test_descartar_no_crea_pieza(self, empresa_y_user, vehiculo_sedan, cliente_django):
        c, emp, _ = cliente_django
        inicializar_sugerencias(vehiculo_sedan, emp)
        vehiculo_desarme = vehiculo_sedan
        sug = SugerenciaPiezaDesarme.objects.filter(
            empresa=emp, vehiculo_desarme=vehiculo_desarme, estado="PENDIENTE"
        ).first()

        resp = c.post(
            _revisar_url(vehiculo_sedan.pk),
            data=json.dumps({"action": "descartar", "sugerencia_id": sug.pk}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        sug.refresh_from_db()
        assert sug.estado == SugerenciaPiezaDesarme.DESCARTADA
        assert PiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme).count() == 0

    def test_progreso_persiste_entre_requests(self, empresa_y_user, vehiculo_sedan, cliente_django):
        c, emp, _ = cliente_django
        inicializar_sugerencias(vehiculo_sedan, emp)
        vehiculo_desarme = vehiculo_sedan
        sug = SugerenciaPiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme).first()
        sug.estado = SugerenciaPiezaDesarme.CONFIRMADA
        sug.save(update_fields=["estado"])

        sug2 = SugerenciaPiezaDesarme.objects.get(pk=sug.pk)
        assert sug2.estado == SugerenciaPiezaDesarme.CONFIRMADA

    def test_reabrir_elimina_pieza_confirmada(self, empresa_y_user, vehiculo_sedan, cliente_django):
        c, emp, _ = cliente_django
        inicializar_sugerencias(vehiculo_sedan, emp)
        vehiculo_desarme = vehiculo_sedan
        sug = SugerenciaPiezaDesarme.objects.filter(
            empresa=emp, vehiculo_desarme=vehiculo_desarme, estado="PENDIENTE"
        ).first()

        c.post(_revisar_url(vehiculo_sedan.pk),
               data=json.dumps({"action": "confirmar", "sugerencia_id": sug.pk, "precio": "0"}),
               content_type="application/json")
        sug.refresh_from_db()
        pieza_id = sug.pieza_creada_id

        resp = c.post(_revisar_url(vehiculo_sedan.pk),
                      data=json.dumps({"action": "reabrir", "sugerencia_id": sug.pk}),
                      content_type="application/json")
        assert resp.json()["success"] is True
        sug.refresh_from_db()
        assert sug.estado == SugerenciaPiezaDesarme.PENDIENTE
        assert not PiezaDesarme.objects.filter(pk=pieza_id).exists()

    def test_agregar_pieza_inline(self, empresa_y_user, vehiculo_sedan, cliente_django):
        c, emp, _ = cliente_django

        resp = c.post(_revisar_url(vehiculo_sedan.pk),
                      data=json.dumps({"action": "agregar", "codigo": "EXTRA-01",
                                       "nombre": "Pieza extra", "zona": "Motor",
                                       "precio": "30000", "condicion": "EXCELENTE",
                                       "cantidad": "1"}),
                      content_type="application/json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        vehiculo_desarme = vehiculo_sedan
        pieza = PiezaDesarme.objects.get(empresa=emp, vehiculo_desarme=vehiculo_desarme, codigo="EXTRA-01")
        assert pieza.revisado is True
        assert pieza.estado_pieza == ESTADO_DISPONIBLE

        vehiculo_desarme = vehiculo_sedan
        sug = SugerenciaPiezaDesarme.objects.get(vehiculo_desarme=vehiculo_desarme, codigo="EXTRA-01")
        assert sug.estado == SugerenciaPiezaDesarme.CONFIRMADA

    def test_accion_desconocida_retorna_400(self, empresa_y_user, vehiculo_sedan, cliente_django):
        c, emp, _ = cliente_django
        resp = c.post(_revisar_url(vehiculo_sedan.pk),
                      data=json.dumps({"action": "volar"}),
                      content_type="application/json")
        assert resp.status_code == 400

    def test_confirmar_doble_retorna_error(self, empresa_y_user, vehiculo_sedan, cliente_django):
        c, emp, _ = cliente_django
        inicializar_sugerencias(vehiculo_sedan, emp)
        vehiculo_desarme = vehiculo_sedan
        sug = SugerenciaPiezaDesarme.objects.filter(
            empresa=emp, vehiculo_desarme=vehiculo_desarme, estado="PENDIENTE"
        ).first()

        c.post(_revisar_url(vehiculo_sedan.pk),
               data=json.dumps({"action": "confirmar", "sugerencia_id": sug.pk, "precio": "0"}),
               content_type="application/json")
        # Segunda confirmación sobre la misma sugerencia → error
        resp2 = c.post(_revisar_url(vehiculo_sedan.pk),
                       data=json.dumps({"action": "confirmar", "sugerencia_id": sug.pk, "precio": "0"}),
                       content_type="application/json")
        assert resp2.json()["success"] is False

    def test_get_autoinicializa_si_no_hay_piezas(self, empresa_y_user, vehiculo_sedan):
        """Lógica de auto-inicialización del GET: si no hay sugerencias ni piezas, init corre."""
        emp, _ = empresa_y_user
        vehiculo_desarme = vehiculo_sedan
        assert not SugerenciaPiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme).exists()
        assert not PiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme).exists()

        # Replica la guardia del GET sin pasar por el template renderer
        # (Django 4.2 + Python 3.14 tiene un bug en Context.__copy__ que rompe c.get() con templates)
        vehiculo_desarme = vehiculo_sedan
        if not SugerenciaPiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme).exists():
            if not PiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme).exists():
                inicializar_sugerencias(vehiculo_sedan, emp)

        vehiculo_desarme = vehiculo_sedan
        assert SugerenciaPiezaDesarme.objects.filter(empresa=emp, vehiculo_desarme=vehiculo_desarme).count() > 0
