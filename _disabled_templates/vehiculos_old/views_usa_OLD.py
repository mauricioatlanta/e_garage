import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from taller.models.clientes import Cliente
from taller.models.extras_vehiculo import ColorVehiculo
from taller.models.vehiculos import Vehiculo
from taller.vehiculos.forms import VehiculoForm

try:
    from taller.models.marcas_usa import MarcaVehiculo as MarcaUSA
    from taller.models.marcas_usa import ModeloVehiculo as ModeloUSA
except ImportError:
    MarcaUSA = ModeloUSA = None

log = logging.getLogger(__name__)


def _get_empresa(request):
    empresa = getattr(request, "empresa", None)
    if empresa:
        return empresa
    from taller.models.empresa import Empresa

    empresa, _ = Empresa.objects.get_or_create(
        user=request.user,
        defaults={"nombre_taller": f"Taller de {request.user.username}"},
    )
    return empresa


def _template_us(name: str) -> str:
    return f"taller/us/en/vehiculos/{name}"


@login_required
def lista_vehiculos(request):
    empresa = _get_empresa(request)
    vehiculos = Vehiculo.objects.filter(empresa=empresa).select_related(
        "cliente", "marca", "modelo"
    )
    marcas = (
        MarcaUSA.objects.filter(activa=True).order_by("nombre")[:500]
        if MarcaUSA
        else []
    )
    modelos = (
        ModeloUSA.objects.filter(activo=True).order_by("nombre")[:500]
        if ModeloUSA
        else []
    )
    return render(
        request,
        _template_us("vehiculo_list.html"),
        {"vehiculos": vehiculos, "marcas": marcas, "modelos": modelos, "country": "US"},
    )


@login_required
@transaction.atomic
def crear_vehiculo(request):
    empresa = _get_empresa(request)
    if request.method == "POST":
        form = VehiculoForm(request.POST, user=request.user)
        if form.is_valid():
            v = form.save(commit=False)
            v.empresa = empresa
            v.save()
            form.save_m2m()
            messages.success(request, "🚗 Vehicle registered successfully.")
            return redirect("vehiculos_usa:lista_vehiculos")
    else:
        form = VehiculoForm(user=request.user)
    ctx = {
        "form": form,
        "country": "US",
        "clientes": Cliente.objects.filter(empresa=empresa)[:500],
        "colores": ColorVehiculo.get_colores_para_pais("US"),
        "marcas_usa": (
            MarcaUSA.objects.filter(activa=True).order_by("nombre")[:500]
            if MarcaUSA
            else []
        ),
        "modelos_usa": (
            ModeloUSA.objects.filter(activo=True).order_by("nombre")[:500]
            if ModeloUSA
            else []
        ),
    }
    return render(request, _template_us("crear.html"), ctx)


@login_required
def ver_vehiculo(request, pk):
    empresa = _get_empresa(request)
    vehiculo = get_object_or_404(Vehiculo, pk=pk, empresa=empresa)
    return render(
        request, _template_us("detalle.html"), {"vehiculo": vehiculo, "country": "US"}
    )


@login_required
@transaction.atomic
def editar_vehiculo(request, vehiculo_id):
    empresa = _get_empresa(request)
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id, empresa=empresa)
    if request.method == "POST":
        form = VehiculoForm(request.POST, instance=vehiculo, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            form.save_m2m()
            messages.success(request, "🚗 Vehicle updated successfully.")
            return redirect("vehiculos_usa:lista_vehiculos")
    else:
        form = VehiculoForm(instance=vehiculo, user=request.user)
    ctx = {
        "form": form,
        "vehiculo": vehiculo,
        "country": "US",
        "clientes": Cliente.objects.filter(empresa=empresa)[:500],
        "colores": ColorVehiculo.get_colores_para_pais("US"),
    }
    return render(request, _template_us("editar.html"), ctx)
