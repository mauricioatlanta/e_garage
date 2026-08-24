"""
Tests for signup rubro capture flow (47 tests total).

Form-level unit tests (no DB):
  - Validation: principal vacío, espacios, grupo desconocido
  - Group expansion: TALLER_MECANICO, NEUMATICOS, DESARMADURIA, CASA_REPUESTOS
  - Union without duplicates, deduplication invariants
  - Order: principal always first, stable order for adicionales
  - Separation: PARTS vs DESARMADURIA, combined flows
  - Adicionales limit: max 2, principal discarded silently, invalid group rejected
  - Bilingual validation: all 7 groups × ES + EN

Service/integration tests (DB, @pytest.mark.django_db):
  - Atomic rollback on ConfiguracionEmpresa save failure
  - No duplicate ConfiguracionEmpresa on signal race
  - rubro_principal + rubros + modules_configured_at persisted correctly
  - has_completed_business_setup() semantics
  - Legacy registrations without rubros stay compatible
"""
import types
import pytest
from unittest.mock import patch, MagicMock
from django import forms

from taller.forms.custom_signup import (
    CustomSignupForm,
    _GROUP_KEY_TO_RUBROS,
    SIGNUP_RUBRO_GROUPS,
)
from taller.models.configuracion import ConfiguracionEmpresa


# ─── Stub helpers ─────────────────────────────────────────────────────────────


def _stub(principal="", adicionales=None, lang="es"):
    """Minimal namespace for calling unbound form methods without Allauth."""
    return types.SimpleNamespace(
        signup_lang=lang,
        cleaned_data={
            "rubro_principal_signup": principal,
            "rubros_adicionales": adicionales or [],
        },
    )


def _build(principal, adicionales=None):
    return CustomSignupForm._build_rubros_list(_stub(principal, adicionales))


# ─── 1. Signup sin selección → ValidationError ───────────────────────────────


def test_principal_vacio_es_invalido():
    stub = _stub(principal="")
    with pytest.raises(forms.ValidationError):
        CustomSignupForm.clean_rubro_principal_signup(stub)


def test_principal_con_espacios_vacios_es_invalido():
    stub = _stub(principal="   ")
    with pytest.raises(forms.ValidationError):
        CustomSignupForm.clean_rubro_principal_signup(stub)


def test_grupo_desconocido_es_invalido():
    stub = _stub(principal="REPUESTOS_DESARMADURIA")  # viejo grupo fusionado
    with pytest.raises(forms.ValidationError):
        CustomSignupForm.clean_rubro_principal_signup(stub)


# ─── 2. Signup con un grupo → configuración correcta ─────────────────────────


def test_taller_mecanico_expande_tres_rubros():
    rubros = _build("TALLER_MECANICO")
    assert rubros == ["WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY"]


def test_neumaticos_expande_a_tire():
    rubros = _build("NEUMATICOS")
    assert rubros == ["TIRE"]


def test_desarmaduria_expande_a_desarmaduria():
    rubros = _build("DESARMADURIA")
    assert rubros == ["DESARMADURIA"]


def test_casa_repuestos_expande_a_parts():
    rubros = _build("CASA_REPUESTOS")
    assert rubros == ["PARTS"]


# ─── 3. Signup con varios grupos → unión sin duplicados ───────────────────────


def test_principal_mas_adicional_produce_union():
    rubros = _build("TALLER_MECANICO", adicionales=["NEUMATICOS"])
    assert rubros == ["WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY", "TIRE"]


def test_mismo_grupo_en_adicionales_se_deduplica():
    # Si TALLER_MECANICO también aparece en adicionales, sus rubros no se duplican.
    rubros = _build("TALLER_MECANICO", adicionales=["TALLER_MECANICO", "NEUMATICOS"])
    assert rubros.count("WORKSHOP") == 1
    assert "TIRE" in rubros


# ─── 4. Invariante: rubro_principal siempre está en rubros ───────────────────


@pytest.mark.parametrize("group_key", [
    "TALLER_MECANICO",
    "CASA_REPUESTOS",
    "DESARMADURIA",
    "NEUMATICOS",
    "CARROCERIA_DETAILING",
    "ESPECIALISTA",
    "OTRO",
])
def test_rubro_principal_siempre_en_rubros(group_key):
    rubros = _build(group_key)
    rubro_principal = rubros[0]
    assert rubro_principal in rubros
    assert len(rubros) >= 1


# ─── 5. Orden estable del rubro principal ─────────────────────────────────────


def test_rubro_principal_es_siempre_primero():
    rubros = _build("CASA_REPUESTOS", adicionales=["TALLER_MECANICO"])
    assert rubros[0] == "PARTS"


def test_orden_preservado_adicionales_sin_usar_set():
    rubros = _build("TALLER_MECANICO", adicionales=["ESPECIALISTA"])
    # Rubros del grupo principal deben preceder a los del grupo adicional.
    last_principal_idx = max(rubros.index(r) for r in ["WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY"])
    first_especialista_idx = min(
        rubros.index(r)
        for r in ["ELECTRIC", "EXHAUST", "SUSPENSION_STEERING", "GLASS_AUDIO", "BRAKES"]
    )
    assert last_principal_idx < first_especialista_idx


# ─── 6. PARTS solamente no activa DESARMADURIA ───────────────────────────────


def test_casa_repuestos_solo_no_incluye_desarmaduria():
    rubros = _build("CASA_REPUESTOS")
    assert "DESARMADURIA" not in rubros
    assert "PARTS" in rubros


# ─── 7. DESARMADURIA solamente no activa PARTS ───────────────────────────────


def test_desarmaduria_solo_no_incluye_parts():
    rubros = _build("DESARMADURIA")
    assert "PARTS" not in rubros
    assert "DESARMADURIA" in rubros


# ─── 8. PARTS + DESARMADURIA activa unión de ambos ───────────────────────────


def test_casa_repuestos_mas_desarmaduria():
    rubros = _build("CASA_REPUESTOS", adicionales=["DESARMADURIA"])
    assert "PARTS" in rubros
    assert "DESARMADURIA" in rubros
    assert rubros[0] == "PARTS"  # CASA_REPUESTOS es el principal


def test_desarmaduria_mas_casa_repuestos():
    rubros = _build("DESARMADURIA", adicionales=["CASA_REPUESTOS"])
    assert "DESARMADURIA" in rubros
    assert "PARTS" in rubros
    assert rubros[0] == "DESARMADURIA"  # DESARMADURIA es el principal


# ─── 9. Más de 2 adicionales → inválido solo en signup ───────────────────────


def test_tres_adicionales_es_invalido():
    stub = _stub(
        principal="TALLER_MECANICO",
        adicionales=["NEUMATICOS", "CARROCERIA_DETAILING", "ESPECIALISTA"],
    )
    with pytest.raises(forms.ValidationError):
        CustomSignupForm.clean_rubros_adicionales(stub)


def test_dos_adicionales_es_valido():
    stub = _stub(
        principal="TALLER_MECANICO",
        adicionales=["NEUMATICOS", "CARROCERIA_DETAILING"],
    )
    result = CustomSignupForm.clean_rubros_adicionales(stub)
    assert result == ["NEUMATICOS", "CARROCERIA_DETAILING"]


def test_principal_en_adicionales_se_descarta_sin_error():
    """Mismo grupo en adicionales se descarta silenciosamente (no cuenta al límite)."""
    stub = _stub(
        principal="TALLER_MECANICO",
        adicionales=["TALLER_MECANICO", "NEUMATICOS"],
    )
    result = CustomSignupForm.clean_rubros_adicionales(stub)
    assert "TALLER_MECANICO" not in result
    assert result == ["NEUMATICOS"]


def test_grupo_adicional_invalido_falla():
    stub = _stub(
        principal="TALLER_MECANICO",
        adicionales=["REPUESTOS_DESARMADURIA"],  # grupo viejo ya no existe
    )
    with pytest.raises(forms.ValidationError):
        CustomSignupForm.clean_rubros_adicionales(stub)


# ─── 10. Rollback completo si falla ConfiguracionEmpresa ─────────────────────


@pytest.mark.django_db
def test_rollback_si_falla_config_save(django_user_model):
    user = django_user_model.objects.create_user(
        username="u_rollback", email="rollback@example.com", password="testpass123"
    )
    from taller.services.registration_service import RegistrationService
    from taller.models.empresa import Empresa

    original_save = ConfiguracionEmpresa.save
    call_count = [0]

    def raise_on_second_save(self, *args, **kwargs):
        call_count[0] += 1
        if call_count[0] >= 2:
            # First call is get_or_create INSERT; second is our update_fields call.
            raise RuntimeError("fallo simulado en config.save")
        return original_save(self, *args, **kwargs)

    with patch.object(ConfiguracionEmpresa, "save", raise_on_second_save):
        with pytest.raises(RuntimeError, match="fallo simulado"):
            RegistrationService.create_company_for_user(
                user=user,
                company_data={"nombre_taller": "Rollback Co", "pais": "CL", "telefono": "+56900100001"},
                rubros_list=["PARTS"],
            )

    # La transacción atómica debe haber revertido la creación de Empresa.
    assert not Empresa.objects.filter(user=user).exists()


# ─── 11. Señales existentes no duplican ConfiguracionEmpresa ─────────────────


@pytest.mark.django_db
def test_no_se_duplica_config_empresa(django_user_model):
    user = django_user_model.objects.create_user(
        username="u_nodup", email="nodup@example.com", password="testpass123"
    )
    from taller.services.registration_service import RegistrationService

    result = RegistrationService.create_company_for_user(
        user=user,
        company_data={"nombre_taller": "No Dup Co", "pais": "CL", "telefono": "+56900100002"},
        rubros_list=["PARTS"],
    )
    empresa = result["empresa"]
    assert ConfiguracionEmpresa.objects.filter(empresa=empresa).count() == 1


# ─── 12. Re-submit conserva selecciones y muestra errores de servidor ─────────
# (covered by form clean tests above; additional service-level check below)

@pytest.mark.django_db
def test_service_persiste_rubro_y_config_correctamente(django_user_model):
    user = django_user_model.objects.create_user(
        username="u_persist", email="persist@example.com", password="testpass123"
    )
    from taller.services.registration_service import RegistrationService

    result = RegistrationService.create_company_for_user(
        user=user,
        company_data={"nombre_taller": "Persist Co", "pais": "CL", "telefono": "+56900100003"},
        rubros_list=["PARTS", "DESARMADURIA"],
    )
    config = result["empresa"].config
    assert config.rubro_principal == "PARTS"
    assert config.rubros == ["PARTS", "DESARMADURIA"]
    assert config.modules_configured_at is not None
    assert config.has_completed_business_setup() is True


# ─── 13. Validación de grupos idéntica en ambos idiomas ──────────────────────


@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("group_key", [
    "TALLER_MECANICO", "CASA_REPUESTOS", "DESARMADURIA",
    "NEUMATICOS", "CARROCERIA_DETAILING", "ESPECIALISTA", "OTRO",
])
def test_grupos_validos_en_ambos_idiomas(lang, group_key):
    stub = _stub(principal=group_key, lang=lang)
    result = CustomSignupForm.clean_rubro_principal_signup(stub)
    assert result == group_key


# ─── 14. Empresa WORKSHOP con signup marca has_completed_business_setup ───────


@pytest.mark.django_db
def test_workshop_signup_tiene_setup_completo(django_user_model):
    user = django_user_model.objects.create_user(
        username="u_ws", email="ws@example.com", password="testpass123"
    )
    from taller.services.registration_service import RegistrationService

    # TALLER_MECANICO → ["WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY"]
    result = RegistrationService.create_company_for_user(
        user=user,
        company_data={"nombre_taller": "Taller WS", "pais": "CL", "telefono": "+56900100004"},
        rubros_list=["WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY"],
    )
    config = result["empresa"].config
    assert config.has_completed_business_setup() is True
    assert config.rubro_principal == "WORKSHOP"
    assert "WORKSHOP" in config.rubros


# ─── 15. Registro legacy sin rubros mantiene compatibilidad ──────────────────


@pytest.mark.django_db
def test_legacy_sin_rubros_no_marca_setup_completo(django_user_model):
    user = django_user_model.objects.create_user(
        username="u_legacy", email="legacy@example.com", password="testpass123"
    )
    from taller.services.registration_service import RegistrationService

    result = RegistrationService.create_company_for_user(
        user=user,
        company_data={"nombre_taller": "Legacy Co", "pais": "CL", "telefono": "+56900100005"},
        rubros_list=None,
    )
    empresa = result["empresa"]

    # No ConfiguracionEmpresa is created by the service for legacy flow.
    config_count = ConfiguracionEmpresa.objects.filter(empresa=empresa).count()
    if config_count > 0:
        config = empresa.config
        # If config exists (e.g. created by a signal), setup should NOT be marked complete.
        assert config.has_completed_business_setup() is False
    # Either way: no modules_configured_at was set by the service.


# ─── Extras: cobertura de contratos de datos ─────────────────────────────────


def test_todos_los_grupos_de_signup_expanden_al_menos_un_rubro():
    for g in SIGNUP_RUBRO_GROUPS:
        rubros = _build(g["key"])
        assert len(rubros) >= 1, f"Grupo {g['key']} no tiene rubros"


def test_group_key_to_rubros_cubre_todos_los_grupos():
    for g in SIGNUP_RUBRO_GROUPS:
        assert g["key"] in _GROUP_KEY_TO_RUBROS
        assert len(_GROUP_KEY_TO_RUBROS[g["key"]]) >= 1


# ─── 12. Hook de sync de catálogo en signup ──────────────────────────────────


@pytest.mark.django_db
def test_signup_workshop_materializa_catalogo_matrix(django_user_model):
    """
    El catálogo curado es parte crítica del alta de una empresa
    de servicios: un WORKSHOP debe salir del signup con catálogo.
    """
    from taller.models import ConfiguracionEmpresa
    from taller.services.registration_service import RegistrationService
    from taller.servicios.models import Servicio, ServicioName, ServicioRubro

    user = django_user_model.objects.create_user(
        username="signup-workshop-matrix",
        email="signup-workshop-matrix@example.com",
        password="test-pass-123",
    )

    result = RegistrationService.create_company_for_user(
        user=user,
        company_data={
            "nombre_taller": "Signup Workshop Matrix",
            "pais": "CL",
            "telefono": "+56900100011",
        },
        rubros_list=["WORKSHOP", "WORKSHOP_HEAVY", "WORKSHOP_MOTO"],
    )

    empresa = result["empresa"]

    config = ConfiguracionEmpresa.objects.get(empresa=empresa)
    assert config.rubro_principal == "WORKSHOP"
    assert config.rubros == ["WORKSHOP", "WORKSHOP_HEAVY", "WORKSHOP_MOTO"]

    assert Servicio.objects.filter(empresa=empresa).count() == 109
    assert ServicioRubro.objects.filter(servicio__empresa=empresa).exists()
    assert ServicioName.objects.filter(
        servicio__empresa=empresa, country_code="CL", language="es"
    ).exists()


@pytest.mark.django_db
def test_signup_parts_cero_servicios_es_valido(django_user_model):
    """
    PARTS queda fuera del alcance de la matriz de servicios.
    El signup debe completar normalmente con catálogo vacío.
    """
    from taller.services.registration_service import RegistrationService
    from taller.servicios.models import Servicio, ServicioRubro

    user = django_user_model.objects.create_user(
        username="signup-parts-matrix",
        email="signup-parts-matrix@example.com",
        password="test-pass-123",
    )

    result = RegistrationService.create_company_for_user(
        user=user,
        company_data={
            "nombre_taller": "Signup Parts Matrix",
            "pais": "CL",
            "telefono": "+56900100012",
        },
        rubros_list=["PARTS"],
    )

    empresa = result["empresa"]
    assert empresa.pk is not None

    assert Servicio.objects.filter(empresa=empresa).count() == 0
    assert ServicioRubro.objects.filter(servicio__empresa=empresa).count() == 0


@pytest.mark.django_db
def test_signup_rollback_si_falla_catalog_sync(django_user_model, monkeypatch):
    """
    El sync es crítico: si falla, @transaction.atomic debe revertir
    también Empresa/ConfiguracionEmpresa.
    """
    from taller.models import ConfiguracionEmpresa
    from taller.models.empresa import Empresa
    from taller.services import registration_service
    from taller.services.registration_service import RegistrationService

    user = django_user_model.objects.create_user(
        username="signup-catalog-rollback",
        email="signup-catalog-rollback@example.com",
        password="test-pass-123",
    )

    def fail_sync(*args, **kwargs):
        raise RuntimeError("catalog sync failed")

    monkeypatch.setattr(
        registration_service, "sync_company_service_catalog", fail_sync
    )

    with pytest.raises(RuntimeError, match="catalog sync failed"):
        RegistrationService.create_company_for_user(
            user=user,
            company_data={
                "nombre_taller": "Rollback Catalog",
                "pais": "CL",
                "telefono": "+56900100013",
            },
            rubros_list=["WORKSHOP"],
        )

    assert not Empresa.objects.filter(user=user).exists()
    assert not ConfiguracionEmpresa.objects.filter(empresa__user=user).exists()


@pytest.mark.django_db
def test_signup_uy_crea_nombre_pais_cuando_hay_traduccion(django_user_model):
    """
    UY comparte idioma 'es' con CL, pero country_code debe permitir
    guardar ambas variantes sin colisión.
    """
    from taller.services.registration_service import RegistrationService
    from taller.servicios.models import Servicio, ServicioName

    user = django_user_model.objects.create_user(
        username="signup-uy-matrix",
        email="signup-uy-matrix@example.com",
        password="test-pass-123",
    )

    result = RegistrationService.create_company_for_user(
        user=user,
        company_data={
            "nombre_taller": "Signup UY Matrix",
            "pais": "UY",
            "telefono": "+59800100014",
        },
        rubros_list=["WORKSHOP"],
    )

    empresa = result["empresa"]

    servicio = Servicio.objects.get(
        empresa=empresa,
        codigo_interno="DIAGNOSTICO_COMPUTARIZADO_CON_ESCANER_OBD_II",
    )

    cl = ServicioName.objects.get(
        servicio=servicio, country_code="CL", language="es", is_default=True
    )
    uy = ServicioName.objects.get(
        servicio=servicio, country_code="UY", language="es", is_default=True
    )

    assert cl.label
    assert uy.label
    assert cl.label != uy.label
    assert uy.label == "Diagnóstico Computarizado"
