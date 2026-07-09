"""
Fase 6.2, punto 5: confirma que _ensure_vehiculo_desarme() sigue siendo
necesaria y correcta SOLO para el fallback legacy de revisar_vehiculo
(vehículos migrados por las tandas 0078/0141, accedidos por su pk viejo de
Vehiculo), y que el flujo de alta nueva (VehiculoDesarmeForm ya corta a
VehiculoDesarme) ya no pasa por la rama de bridging en absoluto.
"""

import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from taller.desarme.services import _ensure_vehiculo_desarme
from taller.desarme.views import revisar_vehiculo
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo


@pytest.fixture
def user_logueado(empresa_chile):
    empresa_chile.user.empresa = empresa_chile
    return empresa_chile.user


def _get_request(rf, path, user):
    request = rf.get(path)
    request.user = user
    request.session = SessionStore()
    request.session.create()
    request._messages = FallbackStorage(request)
    return request


def test_ensure_vehiculo_desarme_shortcircuit_para_alta_nueva(db, empresa_chile):
    """El camino que usa crear_vehiculo hoy: ya es VehiculoDesarme, no toca
    ninguna lógica de bridging ni consulta vehiculo_origen_id."""
    vd = VehiculoDesarme.objects.create(empresa=empresa_chile, patente="NUEVOALTA1")
    assert _ensure_vehiculo_desarme(vd, empresa_chile) is vd


def test_ensure_vehiculo_desarme_fallback_legacy_resuelve_bien(db, empresa_chile):
    """Vehiculo legacy con su VehiculoDesarme correspondiente ya migrado (0078/0141)."""
    legacy = Vehiculo.objects.create(
        empresa=empresa_chile, tipo_uso=Vehiculo.TIPO_USO_DESARME, patente="LEGACY1"
    )
    vd = VehiculoDesarme.objects.create(
        empresa=empresa_chile, vehiculo_origen_id=legacy.id, patente="LEGACY1"
    )
    resuelto = _ensure_vehiculo_desarme(legacy, empresa_chile)
    assert resuelto == vd
    assert resuelto.pk == vd.pk


def test_ensure_vehiculo_desarme_legacy_sin_par_falla_explicito(db, empresa_chile):
    """Vehiculo legacy sin VehiculoDesarme correspondiente: sigue fallando fuerte,
    no en silencio (comportamiento preexistente, sin cambios)."""
    legacy = Vehiculo.objects.create(
        empresa=empresa_chile, tipo_uso=Vehiculo.TIPO_USO_DESARME, patente="LEGACYHUERFANO"
    )
    with pytest.raises(ValueError, match="No existe VehiculoDesarme"):
        _ensure_vehiculo_desarme(legacy, empresa_chile)


def test_revisar_vehiculo_resuelve_directo_para_alta_nueva_sin_pasar_por_bridging(
    db, empresa_chile, user_logueado
):
    """pk de un VehiculoDesarme creado directo (alta nueva): revisar_vehiculo lo
    encuentra en el primer filter() y nunca entra a la rama de fallback legacy."""
    vd = VehiculoDesarme.objects.create(empresa=empresa_chile, patente="ALTA-DIRECTA")

    rf = RequestFactory()
    request = _get_request(rf, f"/desarme/vehiculos/{vd.pk}/revisar/", user_logueado)
    response = revisar_vehiculo(request, pk=vd.pk)
    assert response.status_code == 200


def test_revisar_vehiculo_fallback_legacy_sigue_resolviendo_bien(db, empresa_chile, user_logueado):
    """pk de un Vehiculo legacy (tanda 0078/0141) cuyo VehiculoDesarme tiene un pk
    DISTINTO (caso 0078, sin id explícito): revisar_vehiculo debe encontrarlo
    igual vía _ensure_vehiculo_desarme, sin romper."""
    legacy = Vehiculo.objects.create(
        empresa=empresa_chile, tipo_uso=Vehiculo.TIPO_USO_DESARME, patente="LEGACY-REVISAR"
    )
    VehiculoDesarme.objects.create(
        empresa=empresa_chile, vehiculo_origen_id=legacy.id, patente="LEGACY-REVISAR"
    )

    rf = RequestFactory()
    # Se pide con el pk del Vehiculo legacy, no el del VehiculoDesarme -- es
    # justo el caso que ejercita la rama de fallback (líneas 1620-1627).
    request = _get_request(rf, f"/desarme/vehiculos/{legacy.pk}/revisar/", user_logueado)
    response = revisar_vehiculo(request, pk=legacy.pk)
    assert response.status_code == 200
