import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404, HttpResponse
from django.test import RequestFactory
from django.urls import resolve

from core.views import TenantViewMixin
from taller.documentos import views as documentos_views
from taller.models.extras_vehiculo import CajaVehiculoEmpresa, MotorVehiculoEmpresa
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.repuesto import CategoriaRepuesto, Repuesto
from taller.repuestos.views_cbv import RepuestoCreateView, RepuestoUpdateView
from taller.servicios.models import CategoriaServicio, Servicio
from taller.servicios.views_cbv import (
    ServicioCreateView,
    ServicioDeleteView,
    ServicioDetailView,
    ServicioUpdateView,
)
from taller.tests.factories import (
    ClienteFactory,
    DocumentoFactory,
    EmpresaFactory,
    RepuestoFactory,
    UserFactory,
)
from taller.vehiculos import views_fbv as vehiculos_views
from taller.views.reabastecimiento import ReabastecimientoPanelView


def _request(path, empresa_a, empresa_b, method="get", data=None, body=None, content_type=None):
    factory = RequestFactory()
    request_method = getattr(factory, method)
    kwargs = {}
    if content_type:
        kwargs["content_type"] = content_type
    request = request_method(path, data=data or body or {}, **kwargs)
    request.user = empresa_a.user
    request.empresa = empresa_b
    request.company = empresa_b
    request.country = empresa_b.pais
    request.company_country = empresa_b.pais
    SessionMiddleware(lambda req: HttpResponse("ok")).process_request(request)
    request.session.save()
    request._messages = FallbackStorage(request)
    return request


@pytest.fixture
def empresas_ab(db):
    return EmpresaFactory(pais="CL"), EmpresaFactory(pais="CL")


def _categoria_servicio(country="CL"):
    return CategoriaServicio.objects.create(country=country, code=f"CAT-{country}")


def _vehicle_catalog(country="CL"):
    marca = Marca.objects.create(nombre=f"Marca {country}", country=country)
    modelo = Modelo.objects.create(nombre=f"Modelo {country}", marca=marca, country=country)
    return marca, modelo


@pytest.mark.django_db
def test_tenant_view_mixin_queryset_and_form_valid_use_active_tenant(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    repuesto_a = RepuestoFactory(empresa=empresa_a, nombre="A")
    repuesto_b = RepuestoFactory(empresa=empresa_b, nombre="B")
    request = _request("/cl/es/repuestos/", empresa_a, empresa_b)

    class _Base:
        def form_valid(self, form):
            return form.instance

    class _View(TenantViewMixin, _Base):
        model = Repuesto

    view = _View()
    view.request = request
    ids = set(view.get_queryset().values_list("pk", flat=True))
    assert repuesto_b.pk in ids
    assert repuesto_a.pk not in ids

    form = SimpleNamespace(instance=Repuesto(nombre="Nuevo"))
    instance = view.form_valid(form)
    assert instance.empresa == empresa_b


@pytest.mark.django_db
def test_vehiculo_create_edit_and_custom_auxiliaries_use_active_tenant(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a)
    cliente_b = ClienteFactory(empresa=empresa_b)
    marca, modelo = _vehicle_catalog("CL")

    data = {
        "cliente": str(cliente_b.pk),
        "anio": "2024",
        "marca": str(marca.pk),
        "modelo": str(modelo.pk),
        "patente": "BQA001",
        "vin": "",
        "color": "",
        "motor": "5.7 V8 QA",
        "caja": "Automatica QA",
    }
    request = _request("/cl/es/vehiculos/crear/", empresa_a, empresa_b, method="post", data=data)
    response = vehiculos_views.crear_vehiculo(request)

    assert response.status_code == 302
    vehiculo = empresa_b.vehiculo_set.get(patente="BQA001")
    assert vehiculo.cliente == cliente_b
    assert not empresa_a.vehiculo_set.filter(patente="BQA001").exists()
    assert MotorVehiculoEmpresa.objects.filter(empresa=empresa_b, nombre="5.7 V8 QA").exists()
    assert not MotorVehiculoEmpresa.objects.filter(empresa=empresa_a, nombre="5.7 V8 QA").exists()
    assert CajaVehiculoEmpresa.objects.filter(empresa=empresa_b, nombre="Automatica QA").exists()
    assert not CajaVehiculoEmpresa.objects.filter(empresa=empresa_a, nombre="Automatica QA").exists()

    bad_data = data | {"cliente": str(cliente_a.pk), "patente": "BAD001"}
    bad_request = _request(
        "/cl/es/vehiculos/crear/",
        empresa_a,
        empresa_b,
        method="post",
        data=bad_data,
    )
    with patch("taller.vehiculos.views_fbv.render", return_value=HttpResponse("invalid")):
        bad_response = vehiculos_views.crear_vehiculo(bad_request)
    assert bad_response.status_code == 200
    assert not empresa_b.vehiculo_set.filter(patente="BAD001").exists()
    assert not empresa_a.vehiculo_set.filter(patente="BAD001").exists()

    edit_data = data | {"cliente": str(cliente_b.pk), "patente": "BQA002", "motor": "", "caja": ""}
    edit_request = _request(
        f"/cl/es/vehiculos/{vehiculo.pk}/editar/",
        empresa_a,
        empresa_b,
        method="post",
        data=edit_data,
    )
    edit_response = vehiculos_views.editar_vehiculo(edit_request, vehiculo.pk)
    assert edit_response.status_code == 302
    vehiculo.refresh_from_db()
    assert vehiculo.patente == "BQA002"

    vehiculo_a = empresa_a.vehiculo_set.create(cliente=cliente_a, patente="AQA001")
    with pytest.raises(Http404):
        vehiculos_views.editar_vehiculo(edit_request, vehiculo_a.pk)


@pytest.mark.django_db
def test_repuesto_create_update_categories_and_duplicates_use_active_tenant(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    RepuestoFactory(empresa=empresa_a, part_number="ONLY-A", nombre="Solo A")

    request = _request(
        "/cl/es/repuestos/crear/",
        empresa_a,
        empresa_b,
        method="post",
        data={
            "part_number": "ONLY-A",
            "nombre": "Creado B",
            "precio_compra": "10.00",
            "precio_venta": "20.00",
            "cantidad_stock": "3",
            "stock_minimo": "1",
            "return_to": "/cl/es/repuestos/",
        },
    )
    view = RepuestoCreateView()
    view.setup(request)
    form = view.get_form()
    assert form.is_valid(), form.errors
    response = view.form_valid(form)
    assert response.status_code == 302
    assert Repuesto.objects.filter(empresa=empresa_b, part_number="ONLY-A").exists()
    assert CategoriaRepuesto.objects.filter(empresa=empresa_b).exists()
    assert not CategoriaRepuesto.objects.filter(empresa=empresa_a).exists()

    duplicate_b = RepuestoFactory(empresa=empresa_b, part_number="DUP-B", nombre="Dup B")
    duplicate_request = _request(
        "/cl/es/repuestos/crear/",
        empresa_a,
        empresa_b,
        method="post",
        data={
            "part_number": "DUP-B",
            "nombre": "Debe fallar",
            "precio_compra": "10.00",
            "precio_venta": "20.00",
            "cantidad_stock": "3",
        },
    )
    duplicate_view = RepuestoCreateView()
    duplicate_view.setup(duplicate_request)
    duplicate_form = duplicate_view.get_form()
    assert not duplicate_form.is_valid()
    assert "part_number" in duplicate_form.errors

    update_request = _request(
        f"/cl/es/repuestos/editar/{duplicate_b.pk}/",
        empresa_a,
        empresa_b,
        method="post",
        data={
            "part_number": "DUP-B-EDIT",
            "nombre": "Editado B",
            "precio_compra": "11.00",
            "precio_venta": "21.00",
            "cantidad_stock": "4",
        },
    )
    update_view = RepuestoUpdateView()
    update_view.setup(update_request, pk=duplicate_b.pk)
    update_view.kwargs = {"pk": duplicate_b.pk}
    update_view.object = duplicate_b
    update_form = update_view.get_form()
    assert update_form.is_valid(), update_form.errors
    update_form.save()
    duplicate_b.refresh_from_db()
    assert duplicate_b.nombre == "Editado B"

    repuesto_a = RepuestoFactory(empresa=empresa_a)
    update_view.kwargs = {"pk": repuesto_a.pk}
    with pytest.raises(Http404):
        update_view.get_object()


@pytest.mark.django_db
def test_servicio_create_duplicates_and_object_access_use_active_tenant(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    categoria = _categoria_servicio("CL")
    Servicio.objects.create(empresa=empresa_a, categoria=categoria, nombre="Solo A")

    request = _request(
        "/cl/es/servicios/crear/",
        empresa_a,
        empresa_b,
        method="post",
        data={"nombre": "Solo A", "categoria": str(categoria.pk), "return_to": "/cl/es/servicios/"},
    )
    view = ServicioCreateView()
    view.setup(request)
    form = view.get_form()
    assert form.is_valid(), form.errors
    response = view.form_valid(form)
    assert response.status_code == 302
    servicio_b = Servicio.objects.get(empresa=empresa_b, nombre="Solo A")

    duplicate_request = _request(
        "/cl/es/servicios/crear/",
        empresa_a,
        empresa_b,
        method="post",
        data={"nombre": "Solo A", "categoria": str(categoria.pk)},
    )
    duplicate_view = ServicioCreateView()
    duplicate_view.setup(duplicate_request)
    duplicate_form = duplicate_view.get_form()
    assert not duplicate_form.is_valid()

    detail_view = ServicioDetailView()
    detail_view.setup(_request("/cl/es/servicios/", empresa_a, empresa_b), pk=servicio_b.pk)
    detail_view.kwargs = {"pk": servicio_b.pk}
    assert detail_view.get_object() == servicio_b

    servicio_a = Servicio.objects.get(empresa=empresa_a, nombre="Solo A")
    detail_view.kwargs = {"pk": servicio_a.pk}
    with pytest.raises(Http404):
        detail_view.get_object()

    update_request = _request(
        f"/cl/es/servicios/{servicio_b.pk}/editar/",
        empresa_a,
        empresa_b,
        method="post",
        data={"nombre": "Solo B Editado", "categoria": str(categoria.pk)},
    )
    update_view = ServicioUpdateView()
    update_view.setup(update_request, pk=servicio_b.pk)
    update_view.kwargs = {"pk": servicio_b.pk}
    update_view.object = servicio_b
    update_form = update_view.get_form()
    assert update_form.is_valid(), update_form.errors
    update_form.save()
    servicio_b.refresh_from_db()
    assert servicio_b.nombre == "Solo B Editado"

    delete_view = ServicioDeleteView()
    delete_view.setup(_request("/cl/es/servicios/", empresa_a, empresa_b), pk=servicio_b.pk)
    delete_view.kwargs = {"pk": servicio_b.pk}
    assert delete_view.get_object() == servicio_b
    delete_view.kwargs = {"pk": servicio_a.pk}
    with pytest.raises(Http404):
        delete_view.get_object()


@pytest.mark.django_db
def test_reabastecimiento_panel_receives_active_tenant_and_excludes_owner(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    repuesto_a = RepuestoFactory(empresa=empresa_a)
    repuesto_b = RepuestoFactory(empresa=empresa_b)
    request = _request("/cl/es/repuestos/reabastecimiento/", empresa_a, empresa_b)

    view = ReabastecimientoPanelView()
    view.setup(request)
    object_list = view.get_queryset()
    view.object_list = object_list

    with patch(
        "taller.views.reabastecimiento.InventoryIntelligenceService.build_panel",
        return_value={
            "rows": [],
            "summary": {},
            "lookback_days": 30,
            "target_coverage_days": 30,
        },
    ) as build_panel:
        view.get_context_data(object_list=object_list)

    ids = set(object_list.values_list("pk", flat=True))
    assert repuesto_b.pk in ids
    assert repuesto_a.pk not in ids
    assert build_panel.call_args.kwargs["empresa"] == empresa_b


@pytest.mark.django_db
def test_document_routes_restrict_superadmin_to_active_tenant(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    user = UserFactory(email="mauricioatlanta@gmail.com", is_superuser=True, is_staff=True)
    empresa_a.user = user
    empresa_a.save(update_fields=["user"])
    cliente_a = ClienteFactory(empresa=empresa_a, email="a@example.com")
    cliente_b = ClienteFactory(empresa=empresa_b, email="b@example.com")
    doc_a = DocumentoFactory(empresa=empresa_a, cliente=cliente_a)
    doc_b = DocumentoFactory(empresa=empresa_b, cliente=cliente_b)

    def request_for(path):
        request = _request(path, empresa_a, empresa_b)
        request.user = user
        request.empresa = empresa_b
        request.company = empresa_b
        return request

    route_patches = {
        "pdf": [
            patch("taller.desarme.views_pdf._render_documento_pdf_bytes", return_value=b"pdf"),
        ],
        "imprimir": [
            patch("taller.desarme.views_pdf.render", return_value=HttpResponse("print")),
        ],
        "whatsapp": [],
        "email": [
            patch("taller.desarme.views_pdf._render_documento_pdf_bytes", return_value=b"pdf"),
            patch("taller.desarme.views_pdf.render_to_string", return_value="body"),
            patch("taller.desarme.views_pdf.EmailMessage.send", return_value=1),
            patch("taller.desarme.views_pdf.redirect", return_value=HttpResponse("redirect")),
        ],
    }

    for suffix, patches in route_patches.items():
        path_b = f"/cl/documentos/{doc_b.pk}/{suffix}/"
        match = resolve(path_b)
        managers = [p.__enter__() for p in patches]
        try:
            response = match.func(request_for(path_b), documento_id=doc_b.pk)
        finally:
            for patcher in reversed(patches):
                patcher.__exit__(None, None, None)
        assert response.status_code in {200, 302}

        path_a = f"/cl/documentos/{doc_a.pk}/{suffix}/"
        match = resolve(path_a)
        managers = [p.__enter__() for p in patches]
        try:
            with pytest.raises(Http404):
                match.func(request_for(path_a), documento_id=doc_a.pk)
        finally:
            for patcher in reversed(patches):
                patcher.__exit__(None, None, None)


@pytest.mark.django_db
def test_documentos_api_crear_servicio_uses_active_tenant_only(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    categoria_a = CategoriaServicio.objects.create(country="CL", code="CUSTOM")
    Servicio.objects.create(empresa=empresa_a, categoria=categoria_a, nombre="Lavado")

    payload = json.dumps({"nombre": "Lavado", "precio": "1500", "descripcion": "QA"}).encode()
    request = _request(
        "/cl/documentos/api/crear-servicio/",
        empresa_a,
        empresa_b,
        method="post",
        body=payload,
        content_type="application/json",
    )
    response = documentos_views.api_crear_servicio(request)
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["creado"] is True
    servicio_b = Servicio.objects.get(pk=data["id"])
    assert servicio_b.empresa == empresa_b

    second_request = _request(
        "/cl/documentos/api/crear-servicio/",
        empresa_a,
        empresa_b,
        method="post",
        body=payload,
        content_type="application/json",
    )
    second_response = documentos_views.api_crear_servicio(second_request)
    second_data = json.loads(second_response.content)
    assert second_data["creado"] is False
    assert second_data["id"] == servicio_b.pk
    assert Servicio.objects.filter(empresa=empresa_b, nombre="Lavado").count() == 1
    assert not Servicio.objects.filter(empresa__isnull=True, nombre="Lavado").exists()
