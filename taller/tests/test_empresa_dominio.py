"""
Tests de Fase 1 para EmpresaDominio y DomainService.

Cubre:
  - Modelo: creación, estados, propiedades, métodos DNS
  - Validaciones: formato de dominio, dominios reservados
  - Restricciones de DB: unicidad de dominio, único ACTIVO por empresa
  - Transiciones de estado
  - DomainService: registrar, suspender, preparar_verificacion
  - Sin DNS, sin SSL, sin middleware — solo infraestructura de modelo
"""

import uuid

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from taller.models.empresa import Empresa
from taller.models.empresa_dominio import EmpresaDominio, DOMINIOS_RESERVADOS
from taller.services.domain_service import DomainService


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def usuario(db):
    return User.objects.create_user("dominio_user", "dom@test.com", "pass")


@pytest.fixture
def empresa(db, usuario):
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(user=usuario, nombre_taller="Taller Dominio Test", pais="CL")


@pytest.fixture
def empresa_b(db):
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(nombre_taller="Taller B", pais="CL")


@pytest.fixture
def dominio_pendiente(db, empresa):
    """EmpresaDominio en estado PENDIENTE."""
    return EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="taller.midominio.cl",
    )


@pytest.fixture
def dominio_activo(db, empresa):
    """EmpresaDominio en estado ACTIVO."""
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="taller-activo.midominio.cl",
        estado=EmpresaDominio.Estado.ACTIVO,
    )
    return ed


# ─────────────────────────────────────────────────────────────────────────────
# Tests: creación básica del modelo
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestEmpresaDominioCreacion:
    def test_crea_con_defaults(self, empresa):
        ed = EmpresaDominio.objects.create(empresa=empresa, dominio="mi.taller.com")

        assert ed.pk is not None
        assert ed.estado == EmpresaDominio.Estado.PENDIENTE
        assert ed.ssl_emitido is False
        assert ed.intentos_verificacion == 0
        assert ed.verificado_en is None
        assert ed.ssl_cert_path == ""
        assert ed.ssl_key_path == ""
        assert isinstance(ed.token_verificacion, uuid.UUID)

    def test_dominio_normalizado_a_minusculas(self, empresa):
        ed = EmpresaDominio.objects.create(empresa=empresa, dominio="MI.TALLER.COM")
        assert ed.dominio == "mi.taller.com"

    def test_str_incluye_dominio_y_estado(self, dominio_pendiente):
        s = str(dominio_pendiente)
        assert "taller.midominio.cl" in s
        assert "PENDIENTE" in s

    def test_token_unico_por_registro(self, empresa):
        ed1 = EmpresaDominio.objects.create(empresa=empresa, dominio="a.dominio.com")
        ed2 = EmpresaDominio.objects.create(empresa=empresa, dominio="b.dominio.com")
        assert ed1.token_verificacion != ed2.token_verificacion


# ─────────────────────────────────────────────────────────────────────────────
# Tests: propiedades calculadas
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestEmpresaDominioProperties:
    def test_esta_activo_true_solo_en_ACTIVO(self, empresa):
        for estado in EmpresaDominio.Estado:
            ed = EmpresaDominio(empresa=empresa, dominio="x.com", estado=estado)
            assert ed.esta_activo == (estado == EmpresaDominio.Estado.ACTIVO)

    def test_esta_verificado_en_ACTIVO_y_SSL_PENDIENTE(self, empresa):
        for estado, esperado in [
            (EmpresaDominio.Estado.PENDIENTE,     False),
            (EmpresaDominio.Estado.VERIFICANDO,   False),
            (EmpresaDominio.Estado.ACTIVO,        True),
            (EmpresaDominio.Estado.SSL_PENDIENTE, True),
            (EmpresaDominio.Estado.ERROR_DNS,     False),
            (EmpresaDominio.Estado.SUSPENDIDO,    False),
        ]:
            ed = EmpresaDominio(empresa=empresa, dominio="x.com", estado=estado)
            assert ed.esta_verificado == esperado, f"Falló para estado={estado}"

    def test_puede_verificarse_estados_correctos(self, empresa):
        puede = {EmpresaDominio.Estado.PENDIENTE, EmpresaDominio.Estado.VERIFICANDO, EmpresaDominio.Estado.ERROR_DNS}
        for estado in EmpresaDominio.Estado:
            ed = EmpresaDominio(empresa=empresa, dominio="x.com", estado=estado)
            assert ed.puede_verificarse == (estado in puede)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: métodos DNS
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestMetodosDNS:
    def test_txt_record_name(self, dominio_pendiente):
        assert dominio_pendiente.get_txt_record_name() == "_egarage-verify.taller.midominio.cl"

    def test_txt_record_value_contiene_token(self, dominio_pendiente):
        valor = dominio_pendiente.get_txt_record_value()
        assert valor.startswith("egarage-verify=")
        assert str(dominio_pendiente.token_verificacion) in valor

    def test_cname_target(self, dominio_pendiente):
        assert dominio_pendiente.get_cname_target() == "proxy.egarage.cl"

    def test_txt_record_name_formato(self, empresa):
        ed = EmpresaDominio.objects.create(empresa=empresa, dominio="sub.ejemplo.com")
        assert ed.get_txt_record_name() == "_egarage-verify.sub.ejemplo.com"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: transiciones de estado
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestTransicionesEstado:
    def test_marcar_verificado_cambia_a_ACTIVO(self, dominio_pendiente):
        dominio_pendiente.estado = EmpresaDominio.Estado.VERIFICANDO
        dominio_pendiente.save()

        dominio_pendiente.marcar_verificado()

        dominio_pendiente.refresh_from_db()
        assert dominio_pendiente.estado == EmpresaDominio.Estado.ACTIVO
        assert dominio_pendiente.verificado_en is not None

    def test_suspender_cambia_a_SUSPENDIDO(self, dominio_activo):
        dominio_activo.suspender()
        dominio_activo.refresh_from_db()
        assert dominio_activo.estado == EmpresaDominio.Estado.SUSPENDIDO

    def test_iniciar_verificacion_desde_PENDIENTE(self, dominio_pendiente):
        dominio_pendiente.iniciar_verificacion()
        dominio_pendiente.refresh_from_db()
        assert dominio_pendiente.estado == EmpresaDominio.Estado.VERIFICANDO

    def test_iniciar_verificacion_desde_ERROR_DNS(self, empresa):
        ed = EmpresaDominio.objects.create(
            empresa=empresa,
            dominio="error.dominio.com",
            estado=EmpresaDominio.Estado.ERROR_DNS,
        )
        ed.iniciar_verificacion()
        ed.refresh_from_db()
        assert ed.estado == EmpresaDominio.Estado.VERIFICANDO

    def test_iniciar_verificacion_desde_ACTIVO_levanta_error(self, dominio_activo):
        with pytest.raises(ValueError, match="No se puede iniciar verificación"):
            dominio_activo.iniciar_verificacion()

    def test_iniciar_verificacion_desde_SUSPENDIDO_levanta_error(self, empresa):
        ed = EmpresaDominio.objects.create(
            empresa=empresa,
            dominio="suspendido.dominio.com",
            estado=EmpresaDominio.Estado.SUSPENDIDO,
        )
        with pytest.raises(ValueError):
            ed.iniciar_verificacion()


# ─────────────────────────────────────────────────────────────────────────────
# Tests: validación de formato de dominio
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestValidacionFormatoDominio:
    def _clean(self, empresa, dominio):
        ed = EmpresaDominio(empresa=empresa, dominio=dominio)
        ed.clean()

    def test_dominio_valido_pasa(self, empresa):
        self._clean(empresa, "taller.midominio.cl")         # OK
        self._clean(empresa, "sub.sub.midominio.com")       # OK
        self._clean(empresa, "mi-taller.com")               # guiones permitidos

    def test_dominio_con_protocolo_rechazado(self, empresa):
        with pytest.raises(ValidationError, match="protocolo"):
            self._clean(empresa, "https://taller.com")

    def test_dominio_con_barra_final_rechazado(self, empresa):
        with pytest.raises(ValidationError, match="barra"):
            self._clean(empresa, "taller.com/")

    def test_dominio_con_espacios_rechazado(self, empresa):
        with pytest.raises(ValidationError, match="espacio"):
            self._clean(empresa, "taller ejemplo.com")

    def test_dominio_sin_punto_rechazado(self, empresa):
        with pytest.raises(ValidationError, match="punto"):
            self._clean(empresa, "tallerlocalhost")

    def test_dominio_vacio_rechazado(self, empresa):
        with pytest.raises(ValidationError, match="vacío"):
            self._clean(empresa, "")

    def test_etiqueta_demasiado_larga_rechazada(self, empresa):
        etiqueta_64 = "a" * 64
        with pytest.raises(ValidationError, match="63"):
            self._clean(empresa, f"{etiqueta_64}.com")

    def test_etiqueta_con_guion_al_inicio_rechazada(self, empresa):
        with pytest.raises(ValidationError, match="guión"):
            self._clean(empresa, "-taller.com")

    def test_etiqueta_con_guion_al_final_rechazada(self, empresa):
        with pytest.raises(ValidationError, match="guión"):
            self._clean(empresa, "taller-.com")

    def test_etiqueta_con_caracter_invalido_rechazada(self, empresa):
        with pytest.raises(ValidationError, match="no permitidos"):
            self._clean(empresa, "taller_mecanico.com")  # underscore no válido

    def test_dominio_con_doble_punto_rechazado(self, empresa):
        with pytest.raises(ValidationError, match="vacías"):
            self._clean(empresa, "taller..com")


# ─────────────────────────────────────────────────────────────────────────────
# Tests: dominios reservados
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDominiosReservados:
    def _clean(self, empresa, dominio):
        ed = EmpresaDominio(empresa=empresa, dominio=dominio)
        ed.clean()

    def test_dominios_reservados_rechazados(self, empresa):
        # Algunos reservados (localhost, IPs) fallan validación de formato antes
        # de llegar al check reservado; basta con que levanten ValidationError.
        for dom in DOMINIOS_RESERVADOS:
            with pytest.raises(ValidationError):
                self._clean(empresa, dom)

    def test_subdominio_de_egarage_rechazado(self, empresa):
        # api/app.egarage.cl están en DOMINIOS_RESERVADOS → mensaje "reservado".
        # Solo los subdominios NOT listados explícitamente llegan al branch "subdominios".
        for dom in ["mi.egarage.cl", "taller.egarage.cl"]:
            with pytest.raises(ValidationError, match="subdominios"):
                self._clean(empresa, dom)

    def test_dominio_externo_similar_permitido(self, empresa):
        # Dominio que contiene "egarage" pero no es subdominio de egarage.cl
        self._clean(empresa, "egarage-taller.com")  # no debe lanzar


# ─────────────────────────────────────────────────────────────────────────────
# Tests: restricciones de base de datos
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRestricciones:
    def test_unicidad_de_dominio_entre_empresas(self, empresa, empresa_b):
        EmpresaDominio.objects.create(empresa=empresa, dominio="shared.taller.com")
        with pytest.raises(IntegrityError):
            EmpresaDominio.objects.create(empresa=empresa_b, dominio="shared.taller.com")

    def test_una_empresa_puede_tener_multiples_dominios_no_activos(self, empresa):
        EmpresaDominio.objects.create(empresa=empresa, dominio="d1.taller.com", estado=EmpresaDominio.Estado.PENDIENTE)
        EmpresaDominio.objects.create(empresa=empresa, dominio="d2.taller.com", estado=EmpresaDominio.Estado.PENDIENTE)
        assert EmpresaDominio.objects.filter(empresa=empresa).count() == 2

    def test_constraint_un_solo_activo_por_empresa(self, empresa):
        EmpresaDominio.objects.create(
            empresa=empresa, dominio="activo1.taller.com", estado=EmpresaDominio.Estado.ACTIVO
        )
        with pytest.raises(IntegrityError):
            EmpresaDominio.objects.create(
                empresa=empresa, dominio="activo2.taller.com", estado=EmpresaDominio.Estado.ACTIVO
            )

    def test_dos_empresas_distintas_pueden_tener_cada_una_un_dominio_activo(self, empresa, empresa_b):
        EmpresaDominio.objects.create(
            empresa=empresa, dominio="activo.empresa-a.com", estado=EmpresaDominio.Estado.ACTIVO
        )
        EmpresaDominio.objects.create(
            empresa=empresa_b, dominio="activo.empresa-b.com", estado=EmpresaDominio.Estado.ACTIVO
        )
        # No debe lanzar IntegrityError


# ─────────────────────────────────────────────────────────────────────────────
# Tests: DomainService
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDomainServiceRegistrar:
    def test_registrar_crea_en_PENDIENTE(self, empresa, usuario):
        ed = DomainService.registrar(empresa, "nuevo.taller.com", creado_por=usuario)

        assert ed.pk is not None
        assert ed.estado == EmpresaDominio.Estado.PENDIENTE
        assert ed.dominio == "nuevo.taller.com"
        assert ed.empresa == empresa
        assert ed.creado_por == usuario

    def test_registrar_normaliza_dominio(self, empresa):
        ed = DomainService.registrar(empresa, "  NUEVO.Taller.COM  ")
        assert ed.dominio == "nuevo.taller.com"

    def test_registrar_dominio_duplicado_levanta_error(self, empresa, empresa_b):
        DomainService.registrar(empresa, "dup.taller.com")
        with pytest.raises(ValidationError, match="ya está registrado"):
            DomainService.registrar(empresa_b, "dup.taller.com")

    def test_registrar_dominio_reservado_levanta_error(self, empresa):
        with pytest.raises(ValidationError, match="reservado"):
            DomainService.registrar(empresa, "egarage.cl")

    def test_registrar_dominio_invalido_levanta_error(self, empresa):
        with pytest.raises(ValidationError):
            DomainService.registrar(empresa, "no-tiene-punto")

    def test_registrar_dominio_con_protocolo_levanta_error(self, empresa):
        with pytest.raises(ValidationError):
            DomainService.registrar(empresa, "https://taller.com")


@pytest.mark.django_db
class TestDomainServiceSuspender:
    def test_suspender_dominio_activo(self, empresa):
        ed = EmpresaDominio.objects.create(
            empresa=empresa, dominio="suspen.taller.com", estado=EmpresaDominio.Estado.ACTIVO
        )
        DomainService.suspender(ed)
        ed.refresh_from_db()
        assert ed.estado == EmpresaDominio.Estado.SUSPENDIDO

    def test_suspender_idempotente(self, empresa):
        ed = EmpresaDominio.objects.create(
            empresa=empresa, dominio="idem.taller.com", estado=EmpresaDominio.Estado.SUSPENDIDO
        )
        DomainService.suspender(ed)  # no debe lanzar
        ed.refresh_from_db()
        assert ed.estado == EmpresaDominio.Estado.SUSPENDIDO


@pytest.mark.django_db
class TestDomainServicePreparar:
    def test_preparar_verificacion_desde_PENDIENTE(self, empresa):
        ed = DomainService.registrar(empresa, "prep.taller.com")
        DomainService.preparar_verificacion(ed)
        ed.refresh_from_db()
        assert ed.estado == EmpresaDominio.Estado.VERIFICANDO

    def test_preparar_verificacion_desde_estado_invalido_levanta_error(self, empresa):
        ed = EmpresaDominio.objects.create(
            empresa=empresa, dominio="inv.taller.com", estado=EmpresaDominio.Estado.ACTIVO
        )
        with pytest.raises(ValueError):
            DomainService.preparar_verificacion(ed)


@pytest.mark.django_db
class TestDomainServiceGet:
    def test_get_activo_para_empresa_con_activo(self, empresa):
        EmpresaDominio.objects.create(
            empresa=empresa, dominio="getact.taller.com", estado=EmpresaDominio.Estado.ACTIVO
        )
        resultado = DomainService.get_activo_para_empresa(empresa)
        assert resultado is not None
        assert resultado.dominio == "getact.taller.com"

    def test_get_activo_para_empresa_sin_activo(self, empresa):
        EmpresaDominio.objects.create(
            empresa=empresa, dominio="noact.taller.com", estado=EmpresaDominio.Estado.PENDIENTE
        )
        resultado = DomainService.get_activo_para_empresa(empresa)
        assert resultado is None

    def test_listar_para_empresa_ordena_por_creacion(self, empresa):
        DomainService.registrar(empresa, "l1.taller.com")
        DomainService.registrar(empresa, "l2.taller.com")
        lista = list(DomainService.listar_para_empresa(empresa))
        assert len(lista) == 2
        # Más reciente primero
        assert lista[0].dominio == "l2.taller.com"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: aislamiento multi-tenant
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAislamientoTenant:
    def test_get_activo_no_devuelve_dominio_de_otra_empresa(self, empresa, empresa_b):
        EmpresaDominio.objects.create(
            empresa=empresa_b, dominio="otro.taller.com", estado=EmpresaDominio.Estado.ACTIVO
        )
        resultado = DomainService.get_activo_para_empresa(empresa)
        assert resultado is None

    def test_listar_no_incluye_dominios_de_otra_empresa(self, empresa, empresa_b):
        EmpresaDominio.objects.create(empresa=empresa,   dominio="mio.taller.com")
        EmpresaDominio.objects.create(empresa=empresa_b, dominio="otro.taller.com")

        lista_a = list(DomainService.listar_para_empresa(empresa))
        lista_b = list(DomainService.listar_para_empresa(empresa_b))

        assert len(lista_a) == 1 and lista_a[0].dominio == "mio.taller.com"
        assert len(lista_b) == 1 and lista_b[0].dominio == "otro.taller.com"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: DomainService.reactivar
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDomainServiceReactivar:
    def test_reactivar_suspendido_transiciona_a_pendiente(self, empresa):
        ed = EmpresaDominio.objects.create(
            empresa=empresa,
            dominio="suspendido.taller.com",
            estado=EmpresaDominio.Estado.SUSPENDIDO,
        )
        DomainService.reactivar(ed)
        ed.refresh_from_db()
        assert ed.estado == EmpresaDominio.Estado.PENDIENTE

    def test_reactivar_no_suspendido_es_idempotente(self, empresa):
        ed = EmpresaDominio.objects.create(
            empresa=empresa,
            dominio="pendiente.taller.com",
            estado=EmpresaDominio.Estado.PENDIENTE,
        )
        DomainService.reactivar(ed)  # no debe lanzar ni cambiar estado
        ed.refresh_from_db()
        assert ed.estado == EmpresaDominio.Estado.PENDIENTE

    def test_reactivar_invalida_cache(self, empresa):
        from django.core.cache import cache
        from taller.services.domain_resolver_service import DomainResolverService

        dominio = "cached.taller.com"
        cache.set(DomainResolverService._cache_key(dominio), None, timeout=60)

        ed = EmpresaDominio.objects.create(
            empresa=empresa,
            dominio=dominio,
            estado=EmpresaDominio.Estado.SUSPENDIDO,
        )
        DomainService.reactivar(ed)

        sentinel = object()
        assert cache.get(DomainResolverService._cache_key(dominio), sentinel) is sentinel
