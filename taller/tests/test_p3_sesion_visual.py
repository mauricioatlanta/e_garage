"""
Tests P3 — Sesión de despiece visual.

Verifica:
1. Selector sesion_despiece: zonas, colores, resumen (5 tests)
2. Acciones AJAX: confirmar NO crea PiezaDesarme, descartar, reabrir, agregar (5 tests)
3. finalizar_sesion: bulk create, evento, estado_operativo, sin duplicados (5 tests)
4. Regresión: PiezaDesarme=0 hasta finalizar (5 tests)
5. Flujo canónico sin generación directa de inventario
"""
import json
import pytest
from decimal import Decimal

from django.test import Client
from django.urls import reverse

from taller.models.vehiculo_desarme import EstadoOperativo
from taller.models.vehiculo_desarme_event import TipoEventoDesarme, VehiculoDesarmeEvent
from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
from taller.models.pieza_desarme import PiezaDesarme, ESTADO_DISPONIBLE
from taller.desarme.selectors.sesion_despiece import get_sesion_despiece, _estado_visual
from taller.tests.factories import EmpresaFactory, VehiculoDesarmeFactory


@pytest.fixture
def empresa(db):
    return EmpresaFactory(pais="CL")


@pytest.fixture
def vehiculo(empresa):
    return VehiculoDesarmeFactory(empresa=empresa, estado_operativo=EstadoOperativo.INGRESADO)


@pytest.fixture
def sug_pendiente(empresa, vehiculo):
    return SugerenciaPiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        codigo="MOT-01",
        nombre="Alternador",
        zona="Motor",
        precio_sugerido=Decimal("95000"),
        estado=SugerenciaPiezaDesarme.PENDIENTE,
    )


@pytest.fixture
def owner_user(empresa):
    return empresa.user


@pytest.fixture
def client_auth(owner_user):
    c = Client()
    c.force_login(owner_user)
    return c


def _revisar_url(empresa, vehiculo, client):
    """Resolves the revisar_vehiculo URL for this empresa's country namespace."""
    # Build path directly — the test client doesn't need namespace resolution
    from taller.templatetags.country_url import _country_ns_from_empresa
    pais = (getattr(empresa, "pais", None) or "CL").upper()
    prefix = "/cl/es" if pais == "CL" else "/us/en"
    return f"{prefix}/desarme/vehiculos/{vehiculo.pk}/revisar/"


def _post(client, empresa, vehiculo, payload):
    url = _revisar_url(empresa, vehiculo, client)
    return client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
    )


# ── 1. Selector ─────────────────────────────────────────────────────────────────

class TestSelectorSesionDespiece:
    def test_zonas_agrupadas_correctamente(self, empresa, vehiculo):
        SugerenciaPiezaDesarme.objects.create(
            empresa=empresa, vehiculo_desarme=vehiculo,
            codigo="MOT-01", nombre="Alternador", zona="Motor",
            estado=SugerenciaPiezaDesarme.PENDIENTE,
        )
        SugerenciaPiezaDesarme.objects.create(
            empresa=empresa, vehiculo_desarme=vehiculo,
            codigo="CAR-01", nombre="Capot", zona="Carrocería",
            estado=SugerenciaPiezaDesarme.PENDIENTE,
        )
        result = get_sesion_despiece(vehiculo.pk, empresa)
        zonas = [z["key"] for z in result["zonas"]]
        assert "Motor" in zonas
        assert "Carrocería" in zonas

    def test_resumen_correcto(self, empresa, vehiculo):
        SugerenciaPiezaDesarme.objects.create(
            empresa=empresa, vehiculo_desarme=vehiculo,
            codigo="MOT-01", nombre="Alt", zona="Motor",
            precio_sugerido=Decimal("80000"),
            estado=SugerenciaPiezaDesarme.CONFIRMADA,
        )
        SugerenciaPiezaDesarme.objects.create(
            empresa=empresa, vehiculo_desarme=vehiculo,
            codigo="MOT-02", nombre="Arranque", zona="Motor",
            estado=SugerenciaPiezaDesarme.DESCARTADA,
        )
        result = get_sesion_despiece(vehiculo.pk, empresa)
        r = result["resumen"]
        assert r["confirmadas"] == 1
        assert r["descartadas"] == 1
        assert r["pendientes"] == 0
        assert r["valor_estimado"] == Decimal("80000")

    def test_estado_visual_pendiente_es_gris(self, empresa, vehiculo, sug_pendiente):
        assert _estado_visual(sug_pendiente) == "gris"

    def test_estado_visual_confirmada_buena_es_verde(self, empresa, vehiculo):
        sug = SugerenciaPiezaDesarme(
            estado=SugerenciaPiezaDesarme.CONFIRMADA,
            condicion_sugerida="BUENA",
        )
        assert _estado_visual(sug) == "verde"

    def test_estado_visual_confirmada_regular_es_amarillo(self, empresa, vehiculo):
        sug = SugerenciaPiezaDesarme(
            estado=SugerenciaPiezaDesarme.CONFIRMADA,
            condicion_sugerida="REGULAR",
        )
        assert _estado_visual(sug) == "amarillo"

    def test_estado_visual_descartada_es_rojo(self):
        sug = SugerenciaPiezaDesarme(estado=SugerenciaPiezaDesarme.DESCARTADA)
        assert _estado_visual(sug) == "rojo"


# ── 2. Acciones AJAX ─────────────────────────────────────────────────────────────

class TestAccionesAjax:
    def test_confirmar_no_crea_pieza_desarme(self, empresa, vehiculo, sug_pendiente, client_auth):
        res = _post(client_auth, empresa, vehiculo, {
            "action": "confirmar",
            "sugerencia_id": sug_pendiente.pk,
            "estado_visual": "verde",
            "precio": 80000,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"]
        # No PiezaDesarme created
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 0
        # Sugerencia updated
        sug_pendiente.refresh_from_db()
        assert sug_pendiente.estado == SugerenciaPiezaDesarme.CONFIRMADA
        assert sug_pendiente.precio_sugerido == Decimal("80000")

    def test_confirmar_amarillo_guarda_condicion_regular(self, empresa, vehiculo, sug_pendiente, client_auth):
        _post(client_auth, empresa, vehiculo, {
            "action": "confirmar",
            "sugerencia_id": sug_pendiente.pk,
            "estado_visual": "amarillo",
            "precio": 50000,
        })
        sug_pendiente.refresh_from_db()
        assert sug_pendiente.condicion_sugerida == "REGULAR"

    def test_descartar_cambia_estado(self, empresa, vehiculo, sug_pendiente, client_auth):
        res = _post(client_auth, empresa, vehiculo, {
            "action": "descartar",
            "sugerencia_id": sug_pendiente.pk,
        })
        assert res.json()["success"]
        sug_pendiente.refresh_from_db()
        assert sug_pendiente.estado == SugerenciaPiezaDesarme.DESCARTADA
        assert PiezaDesarme.objects.filter(empresa=empresa).count() == 0

    def test_reabrir_reset_a_pendiente(self, empresa, vehiculo, sug_pendiente, client_auth):
        # Confirm first
        sug_pendiente.estado = SugerenciaPiezaDesarme.CONFIRMADA
        sug_pendiente.precio_sugerido = Decimal("80000")
        sug_pendiente.save()
        # Then reabrir
        res = _post(client_auth, empresa, vehiculo, {
            "action": "reabrir",
            "sugerencia_id": sug_pendiente.pk,
        })
        assert res.json()["success"]
        sug_pendiente.refresh_from_db()
        assert sug_pendiente.estado == SugerenciaPiezaDesarme.PENDIENTE
        assert sug_pendiente.precio_sugerido is None

    def test_agregar_crea_sugerencia_no_pieza(self, empresa, vehiculo, client_auth):
        res = _post(client_auth, empresa, vehiculo, {
            "action": "agregar",
            "codigo": "CUSTOM-01",
            "nombre": "Pieza rara",
            "zona": "Motor",
            "precio": 30000,
            "condicion": "BUENA",
        })
        data = res.json()
        assert data["success"]
        assert "sugerencia_id" in data
        # Sugerencia created
        assert SugerenciaPiezaDesarme.objects.filter(
            empresa=empresa, vehiculo_desarme=vehiculo, codigo="CUSTOM-01"
        ).exists()
        # NO PiezaDesarme
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 0


# ── 3. finalizar_sesion ───────────────────────────────────────────────────────────

class TestFinalizarSesion:
    def _crear_confirmadas(self, empresa, vehiculo, n=3):
        sugs = []
        for i in range(n):
            sugs.append(SugerenciaPiezaDesarme.objects.create(
                empresa=empresa,
                vehiculo_desarme=vehiculo,
                codigo=f"MOT-{i+1:02d}",
                nombre=f"Pieza {i+1}",
                zona="Motor",
                precio_sugerido=Decimal("50000"),
                condicion_sugerida="BUENA",
                estado=SugerenciaPiezaDesarme.CONFIRMADA,
            ))
        return sugs

    def test_finalizar_crea_piezas_en_bulk(self, empresa, vehiculo, client_auth):
        self._crear_confirmadas(empresa, vehiculo, 3)
        res = _post(client_auth, empresa, vehiculo, {"action": "finalizar_sesion"})
        data = res.json()
        assert data["success"]
        assert data["piezas_creadas"] == 3
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 3

    def test_finalizar_no_duplica_si_ya_tiene_pieza(self, empresa, vehiculo, client_auth):
        sugs = self._crear_confirmadas(empresa, vehiculo, 2)
        # One already has pieza_creada (legacy / previous run)
        pieza_existente = PiezaDesarme.objects.create(
            empresa=empresa, vehiculo_desarme=vehiculo,
            codigo=sugs[0].codigo, nombre=sugs[0].nombre,
            estado_pieza=ESTADO_DISPONIBLE, activo=True, cantidad=1,
        )
        sugs[0].pieza_creada = pieza_existente
        sugs[0].save()
        # finalizar_sesion only creates piezas for sugs WITHOUT pieza_creada
        res = _post(client_auth, empresa, vehiculo, {"action": "finalizar_sesion"})
        data = res.json()
        assert data["success"]
        assert data["piezas_creadas"] == 1  # only the second one
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 2

    def test_finalizar_escribe_evento(self, empresa, vehiculo, client_auth):
        self._crear_confirmadas(empresa, vehiculo, 2)
        _post(client_auth, empresa, vehiculo, {"action": "finalizar_sesion"})
        assert VehiculoDesarmeEvent.objects.filter(
            empresa=empresa,
            vehiculo=vehiculo,
            tipo=TipoEventoDesarme.SESION_DESPIECE_FINALIZADA,
        ).exists()

    def test_finalizar_avanza_estado_operativo(self, empresa, vehiculo, client_auth):
        self._crear_confirmadas(empresa, vehiculo, 1)
        _post(client_auth, empresa, vehiculo, {"action": "finalizar_sesion"})
        vehiculo.refresh_from_db()
        assert vehiculo.estado_operativo == EstadoOperativo.EN_PROCESAMIENTO

    def test_finalizar_sin_confirmadas_devuelve_error(self, empresa, vehiculo, client_auth):
        # No sugerencias CONFIRMADAS without pieza_creada
        res = _post(client_auth, empresa, vehiculo, {"action": "finalizar_sesion"})
        data = res.json()
        assert not data["success"]
        assert "error" in data


# ── 4. Regresión: PiezaDesarme=0 hasta finalizar ─────────────────────────────────

class TestRegresionPiezaDesarme:
    def test_confirmar_no_crea_pieza(self, empresa, vehiculo, sug_pendiente, client_auth):
        _post(client_auth, empresa, vehiculo, {
            "action": "confirmar", "sugerencia_id": sug_pendiente.pk,
            "estado_visual": "verde", "precio": 80000,
        })
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 0

    def test_descartar_no_crea_pieza(self, empresa, vehiculo, sug_pendiente, client_auth):
        _post(client_auth, empresa, vehiculo, {
            "action": "descartar", "sugerencia_id": sug_pendiente.pk,
        })
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 0

    def test_agregar_no_crea_pieza(self, empresa, vehiculo, client_auth):
        _post(client_auth, empresa, vehiculo, {
            "action": "agregar", "codigo": "X-01", "nombre": "Test",
            "zona": "Motor", "precio": 10000, "condicion": "BUENA",
        })
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 0

    def test_solo_finalizar_crea_piezas(self, empresa, vehiculo, sug_pendiente, client_auth):
        # Confirm
        _post(client_auth, empresa, vehiculo, {
            "action": "confirmar", "sugerencia_id": sug_pendiente.pk,
            "estado_visual": "verde", "precio": 80000,
        })
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 0
        # Finalize
        _post(client_auth, empresa, vehiculo, {"action": "finalizar_sesion"})
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 1

    def test_descartadas_no_se_crean_en_finalizar(self, empresa, vehiculo, client_auth):
        SugerenciaPiezaDesarme.objects.create(
            empresa=empresa, vehiculo_desarme=vehiculo,
            codigo="MOT-01", nombre="Pieza", zona="Motor",
            estado=SugerenciaPiezaDesarme.DESCARTADA,
        )
        SugerenciaPiezaDesarme.objects.create(
            empresa=empresa, vehiculo_desarme=vehiculo,
            codigo="MOT-02", nombre="Pieza OK", zona="Motor",
            precio_sugerido=Decimal("40000"),
            condicion_sugerida="BUENA",
            estado=SugerenciaPiezaDesarme.CONFIRMADA,
        )
        _post(client_auth, empresa, vehiculo, {"action": "finalizar_sesion"})
        assert PiezaDesarme.objects.filter(empresa=empresa, vehiculo_desarme=vehiculo).count() == 1


