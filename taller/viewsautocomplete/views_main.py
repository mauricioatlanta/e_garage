"""eGarage — módulo limpiado para pre-commit (docstring al inicio)."""

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect

from taller.forms.clientes import ClienteForm
from taller.models.clientes import Cliente
from taller.models.modelo import Modelo  # Modelo estándar de vehículos
from taller.models.region_ciudad import TallerCiudad, TallerRegion  # noqa: F401
from taller.vehiculos.forms import VehiculoForm
from taller.services.empresa_service import get_empresa_safe


def lista_clientes(request):
    q = request.GET.get("q", "").strip()
    # BLINDAJE MULTI-TENANT: Filtrar por empresa del usuario
    empresa = get_empresa_safe(request)
    if not empresa:
        return redirect("/")
    clientes = Cliente.objects.filter(empresa=empresa)

    if q:
        clientes = clientes.filter(nombre__icontains=q) | clientes.filter(apellido__icontains=q)

    paginator = Paginator(clientes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "clientes/lista_clientes.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(
        request,
        template_name,
        {
            "page_obj": page_obj,
            "clientes": page_obj,
            "q": q,
        },
    )


def crear_cliente(request):
    empresa = get_empresa_safe(request)
    if not empresa:
        return redirect("/")
    if request.method == "POST":
        form = ClienteForm(request.POST, empresa=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Cliente creado exitosamente.")
            return redirect("taller:clientes:lista_clientes")
    else:
        form = ClienteForm(empresa=empresa)

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse

    # TEMPORAL: Usar template existente para testing mientras arreglamos la estructura
    template_name = "taller/clientes/crear_cliente.html"

    return TemplateResponse(
        request,
        template_name,
        {
            "form": form,
        },
    )


def obtener_ciudades(request):
    region_id = request.GET.get("region_id")
    ciudades = TallerCiudad.objects.filter(region_id=region_id).values("id", "nombre")
    return JsonResponse(list(ciudades), safe=False)


def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    empresa = get_empresa_safe(request)
    if not empresa:
        return redirect("/")
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente, empresa=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Cliente actualizado exitosamente.")
            return redirect("taller:clientes:lista_clientes")
    else:
        form = ClienteForm(instance=cliente, empresa=empresa)

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "clientes/editar_cliente.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(
        request,
        template_name,
        {
            "form": form,
            "cliente": cliente,
        },
    )


# """Vista legacy de eliminación eliminada.

# Se delega ahora en ``taller.clientes.views.eliminar_cliente`` que acepta
# ``pk`` o ``cliente_id``. Si en algún punto se estaba importando esta
# función desde aquí, puede hacerse:

#     from taller.clientes.views import eliminar_cliente

# Esto evita mantener dos implementaciones divergentes.
# """


def ver_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    empresa = get_empresa_safe(request)
    if not empresa:
        return redirect("/")
    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "clientes/ver_cliente.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(request, template_name, {"cliente": cliente})


def api_ciudades(request):
    region_id = request.GET.get("region_id")
    ciudades = []
    if region_id:
        ciudades_qs = TallerCiudad.objects.filter(region_id=region_id).order_by("nombre")
    # Atributos id y nombre existen en el modelo; comentario para linters dinámicos
    ciudades = [{"id": c.id, "nombre": c.nombre} for c in ciudades_qs]  # noqa: B009
    return JsonResponse({"ciudades": ciudades})


def obtener_modelos_por_marca(request):
    marca_id = request.GET.get("marca_id")
    modelos = []
    if marca_id:
        modelos_qs = Modelo.objects.filter(marca_id=marca_id).order_by("nombre")
    modelos = [{"id": m.id, "nombre": m.nombre} for m in modelos_qs]  # noqa: B009
    return JsonResponse(modelos, safe=False)


def test_autocomplete_minimal(request):
    form = VehiculoForm(user=request.user)
    empresa = get_empresa_safe(request)
    if not empresa:
        return redirect("/")
    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "vehiculos/test_autocomplete_minimal.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(request, template_name, {"form": form})
