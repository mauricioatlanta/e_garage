"""
Regresión: ClienteCreateView.form_valid() no debe devolver 500 para
duplicados de teléfono/email/tax_id, y ClienteForm.clean() debe detectar
duplicados de email/teléfono en el flujo de CREACIÓN (no solo edición).

IMPORTANTE — estado real de `phonenumbers` en este proyecto (confirmado en
producción: no está instalado, ni está en requirements*.txt): validar_telefono()
cae al fallback de `taller/utils/validators.py` (regex `[^0-9+]` strip) en vez
de usar libphonenumber. Ese fallback SÍ unifica diferencias de puntuación/
espacios (p.ej. "+56 9 1234 5678" -> "+56912345678"), pero NO agrega el
código de país a un número local (p.ej. "912345678" NO se normaliza a
"+56912345678"). Por eso hay dos categorías de "distinto formato" con
comportamiento distinto, cubiertas por separado abajo. Instalar phonenumbers
para cerrar el segundo caso queda fuera de este hotfix (decisión explícita).

Ver auditoría: ClienteForm.clean() resolvía `empresa` con un ternario roto
(`self.initial.get("empresa") or self.instance.empresa if hasattr(...) else None`)
que siempre evaluaba a None en creación (self.instance es un Cliente() sin
guardar; acceder a .empresa lanza RelatedObjectDoesNotExist, que hasattr()
silencia a False) — dejando INACTIVO el bloque completo de detección de
duplicados (email y teléfono) para clientes nuevos. Corregido usando
`self.empresa` (ya seteado correctamente en __init__ para ambos flujos).
"""

import pytest
from django.db import IntegrityError
from django.test import RequestFactory
from django.views.generic.edit import ModelFormMixin

from taller.clientes.forms import ClienteForm
from taller.clientes.views_cbv import ClienteCreateView
from taller.models.clientes import Cliente


@pytest.mark.django_db
def test_form_detecta_telefono_duplicado_mismo_string_en_creacion(empresa_chile):
    """Regresión principal del bug de `empresa = self.empresa`: con el
    mismo string exacto, el duplicado ya se detecta al crear (antes del fix,
    `empresa` resolvía a None y este bloque nunca corría)."""
    Cliente.objects.create(
        empresa=empresa_chile,
        nombre="Juan",
        apellido="Perez",
        telefono="+56912345678",
    )

    form = ClienteForm(
        data={"nombre": "Juan", "apellido": "Otro", "telefono": "+56912345678"},
        empresa=empresa_chile,
        pais="CL",
    )
    assert not form.instance.pk  # flujo de creación, no edición

    assert not form.is_valid()
    assert "telefono" in form.errors


@pytest.mark.django_db
def test_form_detecta_telefono_duplicado_con_espacios_via_fallback(empresa_chile):
    """El fallback sin phonenumbers SÍ unifica puntuación/espacios (regex
    `[^0-9+]` strip), así que este caso de "distinto formato" queda cubierto
    por el fix del ítem 2 incluso sin la librería instalada."""
    Cliente.objects.create(
        empresa=empresa_chile,
        nombre="Juan",
        apellido="Perez",
        telefono="+56912345678",
    )

    form = ClienteForm(
        data={"nombre": "Juan", "apellido": "Otro", "telefono": "+56 9 1234 5678"},
        empresa=empresa_chile,
        pais="CL",
    )

    assert not form.is_valid()
    assert "telefono" in form.errors


@pytest.mark.django_db
def test_form_no_detecta_telefono_local_sin_codigo_pais_sin_phonenumbers(empresa_chile):
    """Gap DOCUMENTADO y aceptado (fuera de scope de este hotfix): sin
    phonenumbers, "912345678" (formato local) no se normaliza a
    "+56912345678", así que ClienteForm.clean() NO detecta esta colisión —
    y tampoco Cliente.clean() al guardar (usa el mismo fallback), por lo que
    esto NO produce un IntegrityError: se guarda como un Cliente distinto en
    la BD (duplicado "lógico" no detectado). Cerrar esto requiere instalar
    phonenumbers (tarea separada, decisión explícita del usuario)."""
    Cliente.objects.create(
        empresa=empresa_chile,
        nombre="Juan",
        apellido="Perez",
        telefono="+56912345678",
    )

    form = ClienteForm(
        data={"nombre": "Juan", "apellido": "Otro", "telefono": "912345678"},
        empresa=empresa_chile,
        pais="CL",
    )

    assert form.is_valid(), form.errors
    cliente = form.save()

    assert Cliente.objects.filter(empresa=empresa_chile, telefono="+56912345678").count() == 1
    assert Cliente.objects.filter(empresa=empresa_chile, telefono="912345678").count() == 1
    assert cliente.telefono == "912345678"


@pytest.mark.django_db
def test_form_detecta_email_duplicado_exacto_en_creacion(empresa_chile):
    """Regresión: detección de email duplicado también estaba inactiva en
    creación por el mismo bug de resolución de `empresa`."""
    Cliente.objects.create(
        empresa=empresa_chile,
        nombre="Ana",
        apellido="Soto",
        telefono="+56911111111",
        email="ana@example.com",
    )

    form = ClienteForm(
        data={
            "nombre": "Ana",
            "apellido": "Otra",
            "telefono": "+56922222222",
            "email": "ana@example.com",
        },
        empresa=empresa_chile,
        pais="CL",
    )
    assert not form.instance.pk

    assert not form.is_valid()
    assert "email" in form.errors


def _build_view_with_form(empresa_chile):
    view = ClienteCreateView()
    view.request = RequestFactory().post("/clientes/crear/")
    view.request.user = empresa_chile.user

    form = ClienteForm(
        data={"nombre": "Test", "apellido": "Test", "telefono": "+56933333333"},
        empresa=empresa_chile,
        pais="CL",
    )
    return view, form


@pytest.mark.django_db
def test_view_form_valid_mapea_constraint_telefono_a_form_error(monkeypatch, empresa_chile):
    def boom(self, form):
        raise IntegrityError(
            'duplicate key value violates unique constraint "uq_cliente_empresa_telefono_present"'
        )

    monkeypatch.setattr(ModelFormMixin, "form_valid", boom)
    monkeypatch.setattr(ClienteCreateView, "form_invalid", lambda self, form: form)

    view, form = _build_view_with_form(empresa_chile)

    result = view.form_valid(form)

    assert result is form
    assert "telefono" in form.errors


@pytest.mark.django_db
def test_view_form_valid_mapea_constraint_email_a_form_error_sqlite_legacy(
    monkeypatch, empresa_chile
):
    # Formato legacy de mensaje de SQLite (nombres de columna, no de constraint).
    def boom(self, form):
        raise IntegrityError(
            "UNIQUE constraint failed: taller_cliente.empresa_id, taller_cliente.email"
        )

    monkeypatch.setattr(ModelFormMixin, "form_valid", boom)
    monkeypatch.setattr(ClienteCreateView, "form_invalid", lambda self, form: form)

    view, form = _build_view_with_form(empresa_chile)

    result = view.form_valid(form)

    assert result is form
    assert "email" in form.errors


@pytest.mark.django_db
def test_view_form_valid_reraises_constraint_no_mapeado(monkeypatch, empresa_chile):
    def boom(self, form):
        raise IntegrityError('duplicate key value violates unique constraint "uq_otro_constraint"')

    monkeypatch.setattr(ModelFormMixin, "form_valid", boom)

    view, form = _build_view_with_form(empresa_chile)

    with pytest.raises(IntegrityError):
        view.form_valid(form)


@pytest.mark.django_db(transaction=True)
def test_view_form_valid_catches_race_condition_telefono_duplicate(monkeypatch, empresa_chile):
    """Reproduce el caso real donde el pre-check de ClienteForm.clean() no
    alcanza a atrapar el duplicado: el form se valida cuando el teléfono
    todavía es único (is_valid() -> True, _post_clean ya normalizó
    self.instance.telefono), y justo después — antes del guardado real —
    otra request concurrente inserta el mismo teléfono. El INSERT final
    choca contra uq_cliente_empresa_telefono_present y debe ser atrapado por
    el catch de la vista (ítem 1), no propagarse como 500.

    Usa transaction=True (en vez del atomic() implícito de @pytest.mark.django_db)
    porque el proyecto no tiene ATOMIC_REQUESTS activado (grep confirmado en
    gestion_taller/settings/): en producción el IntegrityError de form.save()
    NO deja la conexión en un estado de transacción rota, así que las queries
    posteriores (p.ej. las de form_invalid) siguen funcionando con normalidad.
    El atomic() implícito de pytest-django sí la deja rota, lo cual es un
    artefacto de aislamiento de tests, no el comportamiento real."""
    telefono = "+56955555555"
    form = ClienteForm(
        data={"nombre": "Race", "apellido": "Condition", "telefono": telefono},
        empresa=empresa_chile,
        pais="CL",
    )
    assert form.is_valid()  # todavía no existe el duplicado

    # Condición de carrera: otra request concurrente ya insertó el mismo
    # teléfono entre la validación del form y el guardado de esta request.
    Cliente.objects.create(
        empresa=empresa_chile, nombre="Otro", apellido="Cliente", telefono=telefono
    )

    monkeypatch.setattr(ClienteCreateView, "form_invalid", lambda self, form: form)

    view = ClienteCreateView()
    view.request = RequestFactory().post("/clientes/crear/")
    view.request.user = empresa_chile.user

    result = view.form_valid(form)

    assert result is form
    assert "telefono" in form.errors
    # Solo se creó el Cliente de la carrera, no un segundo duplicado.
    assert Cliente.objects.filter(empresa=empresa_chile, telefono=telefono).count() == 1
