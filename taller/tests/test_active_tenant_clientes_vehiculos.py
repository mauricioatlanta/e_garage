import json
from types import SimpleNamespace

import pytest
from django.http import Http404
from django.test import RequestFactory

from taller.clientes.dal_views import ClientesAutocomplete
from taller.clientes.views_cbv import ClienteCreateView, ClienteDetailView, ClienteListView
from taller.models.marca import Marca
from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
from taller.models.modelo import Modelo
from taller.tests.factories import ClienteFactory, EmpresaFactory, VehiculoFactory
from taller.vehiculos.forms import VehiculoForm
from taller.vehiculos import views_fbv as vehiculos_views


def _active_request(path, empresa_a, empresa_b, method="get", data=None):
    factory = RequestFactory()
    request_method = getattr(factory, method)
    request = request_method(path, data=data or {})
    request.user = empresa_a.user
    request.empresa = empresa_b
    request.company = empresa_b
    request.country = empresa_b.pais
    request.company_country = empresa_b.pais
    return request


@pytest.fixture
def empresas_ab(db):
    return EmpresaFactory(pais="CL"), EmpresaFactory(pais="US")


@pytest.mark.django_db
def test_clientes_listado_usa_tenant_activo_y_aisla_propietaria(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a, nombre="Cliente A")
    cliente_b = ClienteFactory(empresa=empresa_b, nombre="Cliente B")
    request = _active_request("/us/clientes/", empresa_a, empresa_b)

    view = ClienteListView()
    view.setup(request)
    view.kwargs = {}
    ids = {cliente.pk for cliente in view.get_queryset()}

    assert cliente_b.pk in ids
    assert cliente_a.pk not in ids
    assert request.user.empresa == empresa_a


@pytest.mark.django_db
def test_cliente_creacion_y_detalle_usan_tenant_activo(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a)
    cliente_b = ClienteFactory(empresa=empresa_b)
    request = _active_request("/us/clientes/crear/", empresa_a, empresa_b)

    create_view = ClienteCreateView()
    create_view.setup(request)
    create_view.kwargs = {}
    kwargs = create_view.get_form_kwargs()
    assert kwargs["empresa"] == empresa_b

    detail_view = ClienteDetailView()
    detail_view.setup(request, pk=cliente_b.pk)
    detail_view.kwargs = {"pk": cliente_b.pk}
    assert detail_view.get_object() == cliente_b

    detail_view.kwargs = {"pk": cliente_a.pk}
    with pytest.raises(Http404):
        detail_view.get_object()


@pytest.mark.django_db
def test_cliente_autocomplete_dal_filtra_por_tenant_activo(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a, nombre="Mismo")
    cliente_b = ClienteFactory(empresa=empresa_b, nombre="Mismo")
    request = _active_request("/us/clientes/autocomplete/", empresa_a, empresa_b)

    view = ClientesAutocomplete()
    view.request = request
    view.q = "Mismo"
    ids = {cliente.pk for cliente in view.get_queryset()}

    assert cliente_b.pk in ids
    assert cliente_a.pk not in ids


@pytest.mark.django_db
def test_vehiculos_listado_y_busqueda_clientes_usan_tenant_activo(empresas_ab, monkeypatch):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a, nombre="Cliente")
    cliente_b = ClienteFactory(empresa=empresa_b, nombre="Cliente")
    vehiculo_a = VehiculoFactory(empresa=empresa_a, cliente=cliente_a, patente="AAA111")
    vehiculo_b = VehiculoFactory(empresa=empresa_b, cliente=cliente_b, patente="BBB222")
    captured = {}

    def fake_render(request, template_name, context):
        captured["context"] = context
        return SimpleNamespace(status_code=200, context_data=context)

    monkeypatch.setattr(vehiculos_views, "render", fake_render)
    request = _active_request("/us/vehiculos/", empresa_a, empresa_b)
    response = vehiculos_views.lista_vehiculos(request)

    assert response.status_code == 200
    ids = {vehiculo.pk for vehiculo in captured["context"]["vehiculos"]}
    assert vehiculo_b.pk in ids
    assert vehiculo_a.pk not in ids

    request = _active_request(
        "/us/vehiculos/api/clientes/",
        empresa_a,
        empresa_b,
        data={"q": "Cliente"},
    )
    response = vehiculos_views.api_busqueda_clientes(request)
    cliente_ids = {item["id"] for item in json.loads(response.content)}
    assert cliente_b.pk in cliente_ids
    assert cliente_a.pk not in cliente_ids


@pytest.mark.django_db
def test_vehiculos_listado_busca_por_cliente_y_terminos_inteligentes(empresas_ab, monkeypatch):
    empresa_a, empresa_b = empresas_ab
    cliente = ClienteFactory(empresa=empresa_b, nombre="Juan", apellido="Pérez")
    otro_cliente = ClienteFactory(empresa=empresa_b, nombre="María", apellido="López")
    vehiculo = VehiculoFactory(empresa=empresa_b, cliente=cliente, patente="JUA123")
    otro_vehiculo = VehiculoFactory(empresa=empresa_b, cliente=otro_cliente, patente="XYZ789")
    captured = {}

    def fake_render(request, template_name, context):
        captured["context"] = context
        return SimpleNamespace(status_code=200, context_data=context)

    monkeypatch.setattr(vehiculos_views, "render", fake_render)
    request = _active_request(
        "/us/es/vehiculos/",
        empresa_a,
        empresa_b,
        data={"q": "juan pérez"},
    )

    response = vehiculos_views.lista_vehiculos(request)

    assert response.status_code == 200
    assert captured["context"]["search_query"] == "juan pérez"
    ids = {item.pk for item in captured["context"]["vehiculos"]}
    assert ids == {vehiculo.pk}
    assert otro_vehiculo.pk not in ids


@pytest.mark.django_db
def test_vehiculos_listado_encuentra_cliente_con_busqueda_parcial(empresas_ab, monkeypatch):
    empresa_a, empresa_b = empresas_ab
    cliente = ClienteFactory(empresa=empresa_b, nombre="Juan", apellido="Pérez")
    vehiculo = VehiculoFactory(empresa=empresa_b, cliente=cliente, patente="JUA123")
    captured = {}

    def fake_render(request, template_name, context):
        captured["context"] = context
        return SimpleNamespace(status_code=200, context_data=context)

    monkeypatch.setattr(vehiculos_views, "render", fake_render)
    request = _active_request(
        "/us/es/vehiculos/",
        empresa_a,
        empresa_b,
        data={"q": "ju"},
    )

    response = vehiculos_views.lista_vehiculos(request)

    assert response.status_code == 200
    assert {item.pk for item in captured["context"]["vehiculos"]} == {vehiculo.pk}


@pytest.mark.django_db
def test_modelos_por_marca_usa_incluye_catalogo_usa_y_filtra_por_anio(empresa_usa):
    marca = Marca.objects.create(nombre="Example Motors", country="US")
    marca_usa = MarcaVehiculo.objects.create(nombre=marca.nombre)
    ModeloVehiculo.objects.create(
        marca=marca_usa,
        nombre="Compact",
        anio_inicio=2000,
        anio_fin=2010,
    )
    ModeloVehiculo.objects.create(
        marca=marca_usa,
        nombre="Crossover",
        anio_inicio=2015,
        anio_fin=2025,
    )
    request = RequestFactory().get(
        "/us/es/vehiculos/api/modelos-por-marca/",
        {"marca_id": str(marca.pk), "anio": "2020"},
    )
    request.user = empresa_usa.user

    response = vehiculos_views.modelos_por_marca_api(request)

    assert response.status_code == 200
    assert json.loads(response.content) == [{"id": "nombre:Crossover", "nombre": "Crossover"}]

    form = VehiculoForm(
        data={"marca": str(marca.pk), "modelo": "nombre:Crossover"},
        user=empresa_usa.user,
        request=request,
    )
    form.cleaned_data = {"marca": marca}
    modelo = form.clean_modelo()
    assert modelo is not None
    assert modelo.nombre == "Crossover"
    assert modelo.marca_id == marca.pk


@pytest.mark.django_db
def test_catalogo_vehiculos_sigue_pais_explicito_de_ruta_aunque_tenant_sea_otro(empresas_ab):
    empresa_cl, _ = empresas_ab
    marca_cl = Marca.objects.create(nombre="Route Test Make", country="CL")
    marca_us = Marca.objects.create(nombre="Route Test Make", country="US")
    Modelo.objects.create(marca=marca_cl, nombre="Modelo Chile", country="CL")
    Modelo.objects.create(marca=marca_us, nombre="US Route Model", country="US")

    request = _active_request(
        "/us/es/vehiculos/api/marcas/",
        empresa_cl,
        empresa_cl,
    )
    marcas_response = vehiculos_views.api_marcas(request)
    marcas = json.loads(marcas_response.content)
    assert {marca["id"] for marca in marcas} == {marca_us.pk}

    request = _active_request(
        "/us/es/vehiculos/api/modelos-por-marca/",
        empresa_cl,
        empresa_cl,
        data={"marca_id": str(marca_us.pk)},
    )
    modelos_response = vehiculos_views.modelos_por_marca_api(request)
    modelos = json.loads(modelos_response.content)
    assert modelos == [{"id": Modelo.objects.get(marca=marca_us).pk, "nombre": "US Route Model"}]


@pytest.mark.django_db
def test_modelos_por_marca_usa_usa_catalogo_predefinido_si_la_base_no_tiene_modelos(
    empresa_usa,
):
    marca = Marca.objects.create(nombre="Honda", country="US")
    request = RequestFactory().get(
        "/us/es/vehiculos/api/modelos-por-marca/",
        {"marca_id": str(marca.pk)},
    )
    request.user = empresa_usa.user

    response = vehiculos_views.modelos_por_marca_api(request)

    assert response.status_code == 200
    modelos = json.loads(response.content)
    assert {"id": "nombre:Civic", "nombre": "Civic"} in modelos
    assert {"id": "nombre:Accord", "nombre": "Accord"} in modelos


@pytest.mark.django_db
def test_modelos_por_marca_usa_no_falla_si_falta_tabla_catalogo_opcional(
    empresa_usa, monkeypatch
):
    marca = Marca.objects.create(nombre="Acura", country="US")
    modelo = Modelo.objects.create(marca=marca, nombre="ILX", country="US")
    real_table_names = vehiculos_views.connection.introspection.table_names

    def table_names_without_legacy_catalog(*args, **kwargs):
        return [
            table
            for table in real_table_names(*args, **kwargs)
            if table != ModeloVehiculo._meta.db_table
        ]

    monkeypatch.setattr(
        vehiculos_views.connection.introspection,
        "table_names",
        table_names_without_legacy_catalog,
    )
    request = RequestFactory().get(
        "/us/es/vehiculos/api/modelos-por-marca/",
        {"marca_id": str(marca.pk), "anio": "2027"},
    )
    request.user = empresa_usa.user

    response = vehiculos_views.modelos_por_marca_api(request)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert {"id": modelo.pk, "nombre": "ILX"} in data
    assert {"id": "nombre:Integra", "nombre": "Integra"} in data


@pytest.mark.django_db
def test_vehiculo_form_usa_carga_colores_en_select(empresa_usa):
    request = RequestFactory().get("/us/es/vehiculos/crear/")
    request.user = empresa_usa.user

    form = VehiculoForm(user=empresa_usa.user, request=request)

    choices = list(form.fields["color"].widget.choices)
    assert choices[0] == ("", "Select color...")
    assert any(label == "White" for _, label in choices)
    assert len(choices) > 1
    assert form.fields["cliente"].widget._url == "/us/es/vehiculos/autocomplete/cliente/"


@pytest.mark.django_db
def test_vehiculo_form_usa_en_usa_autocomplete_url_usa_ingles(empresa_usa):
    request = RequestFactory().get("/us/en/vehiculos/crear/")
    request.user = empresa_usa.user

    form = VehiculoForm(user=empresa_usa.user, request=request)

    assert form.fields["cliente"].widget._url == "/us/en/vehiculos/autocomplete/cliente/"


@pytest.mark.django_db
def test_vehiculo_form_guarda_motor_y_caja_ingresados_en_campos_nuevos(empresa_usa):
    request = RequestFactory().post("/us/es/vehiculos/crear/")
    request.user = empresa_usa.user
    form = VehiculoForm(
        data={
            "motor": "",
            "nuevo_motor": "1.8 4cyl",
            "caja": "",
            "nuevo_caja": "Automatic",
        },
        user=empresa_usa.user,
        request=request,
        empresa=empresa_usa,
    )
    form.cleaned_data = {}

    motor = form.clean_motor()
    caja = form.clean_caja()

    assert motor is not None
    assert motor.nombre == "1.8 4cyl"
    assert motor.country == "US"
    assert caja is not None
    assert caja.nombre == "Automatic"
    assert caja.country == "US"


@pytest.mark.django_db
def test_ajax_agregar_motor_devuelve_id_y_nombre_para_seleccion_del_formulario():
    marca = Marca.objects.create(nombre="Example Motors", country="US")
    modelo = Modelo.objects.create(
        marca=marca,
        nombre="Example Model",
        country="US",
    )
    request = RequestFactory().post(
        "/us/es/vehiculos/ajax/motores/agregar/",
        data=json.dumps({"nombre": "Example Engine", "modelo_id": str(modelo.pk)}),
        content_type="application/json",
    )

    response = vehiculos_views.ajax_agregar_motor(request)
    data = json.loads(response.content)

    assert response.status_code == 200
    assert data["success"] is True
    assert data["nombre"] == "Example Engine"
    assert data["motor"] == {"id": data["id"], "nombre": "Example Engine"}
    motor = MotorVehiculo.objects.get(pk=data["id"])
    assert motor.modelos.filter(pk=modelo.pk).exists()


@pytest.mark.django_db
def test_ajax_agregar_motor_resuelve_modelo_del_catalogo_por_nombre():
    marca = Marca.objects.create(nombre="Acura", country="US")
    otra_marca = Marca.objects.create(nombre="Other Make", country="US")
    otro_modelo = Modelo.objects.create(
        marca=otra_marca,
        nombre="Unrelated",
        country="US",
    )
    request = RequestFactory().post(
        "/us/es/vehiculos/ajax/motores/agregar/",
        data=json.dumps(
            {
                "nombre": "1.8 4cyl",
                "modelo_id": str(otro_modelo.pk),
                "marca_id": str(marca.pk),
                "modelo_nombre": "ILX",
            }
        ),
        content_type="application/json",
    )

    response = vehiculos_views.ajax_agregar_motor(request)
    data = json.loads(response.content)

    assert response.status_code == 200
    assert data["success"] is True
    modelo = Modelo.objects.get(marca=marca, nombre="ILX", country="US")
    motor = MotorVehiculo.objects.get(pk=data["id"], nombre="1.8 4cyl", country="US")
    assert motor.modelos.filter(pk=modelo.pk).exists()

    listado = vehiculos_views.ajax_motores_por_modelo(
        RequestFactory().get(
            "/us/es/vehiculos/ajax/motores-por-modelo/",
            {
                "modelo_id": str(otro_modelo.pk),
                "marca_id": str(marca.pk),
                "modelo_nombre": "ILX",
            },
        )
    )
    assert any(item["nombre"] == "1.8 4cyl" for item in json.loads(listado.content))

    request_caja = RequestFactory().post(
        "/us/es/vehiculos/ajax/agregar-caja/",
        data=json.dumps(
            {
                "nombre": "Automatic",
                "modelo_id": str(otro_modelo.pk),
                "marca_id": str(marca.pk),
                "modelo_nombre": "ILX",
            }
        ),
        content_type="application/json",
    )
    response_caja = vehiculos_views.ajax_agregar_caja(request_caja)
    caja_data = json.loads(response_caja.content)
    assert response_caja.status_code == 200
    assert caja_data["success"] is True
    assert caja_data["caja"] == {"id": caja_data["id"], "nombre": "Automatic"}
    caja = CajaVehiculo.objects.get(pk=caja_data["id"])
    assert caja.modelos.filter(pk=modelo.pk).exists()

    listado_cajas = vehiculos_views.ajax_cajas_por_modelo(
        RequestFactory().get(
            "/us/es/vehiculos/ajax/cajas-por-modelo/",
            {
                "modelo_id": str(otro_modelo.pk),
                "marca_id": str(marca.pk),
                "modelo_nombre": "ILX",
            },
        )
    )
    assert any(item["nombre"] == "Automatic" for item in json.loads(listado_cajas.content))


@pytest.mark.django_db
def test_vehiculo_detalle_bloquea_objetos_de_empresa_propietaria(empresas_ab, monkeypatch):
    empresa_a, empresa_b = empresas_ab
    vehiculo_a = VehiculoFactory(empresa=empresa_a)
    vehiculo_b = VehiculoFactory(empresa=empresa_b)

    def fake_template_response(request, template_name, context):
        return SimpleNamespace(status_code=200, context_data=context)

    monkeypatch.setattr(vehiculos_views, "TemplateResponse", fake_template_response)
    request = _active_request(f"/us/vehiculos/{vehiculo_b.pk}/", empresa_a, empresa_b)
    response = vehiculos_views.ver_vehiculo(request, vehiculo_b.pk)
    assert response.context_data["vehiculo"] == vehiculo_b

    with pytest.raises(Http404):
        vehiculos_views.ver_vehiculo(request, vehiculo_a.pk)
