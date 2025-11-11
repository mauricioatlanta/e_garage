from django.shortcuts import render


def servicios_menu(request):
    return render(request, "taller/servicios/servicios_menu.html")


def otros_servicios_menu(request):
    return render(request, "taller/servicios/otros_servicios_menu.html")


def changelog_view(request):
    cambios = [
        {
            "version": "v1.0.0-beta",
            "fecha": "2025-08-14",
            "items": [
                "Lanzamiento de prueba con plan gratuito de 30 días.",
                "Módulos base: clientes, vehículos, repuestos y documentos.",
                "UI base con Tailwind y flow de activación de cuenta.",
            ],
        },
    ]
    return render(request, "taller/changelog.html", {"cambios": cambios})


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import NoReverseMatch, reverse

from .forms.empresa import DatosPersonalesForm, EmpresaForm

try:
    from taller.models.tecnico import Tecnico  # type: ignore
except Exception:  # pragma: no cover
    Tecnico = None


@login_required
def configuracion(request):
    empresa = getattr(request.user, "empresa", None)
    empresa_form = EmpresaForm(instance=empresa)
    datos_form = DatosPersonalesForm(user=request.user)
    created = False

    # Procesar formularios
    if request.method == "POST":
        if "datos_form" in request.POST:
            datos_form = DatosPersonalesForm(request.POST, user=request.user)
            if datos_form.is_valid():
                request.user.first_name = datos_form.cleaned_data["first_name"]
                request.user.last_name = datos_form.cleaned_data["last_name"]
                request.user.email = datos_form.cleaned_data["email"]
                request.user.save()
                messages.success(request, "Datos personales actualizados.")
        elif "empresa_form" in request.POST:
            empresa_form = EmpresaForm(request.POST, request.FILES, instance=empresa)
            if empresa_form.is_valid():
                empresa_form.save()
                messages.success(request, "Datos de la empresa actualizados.")
        elif "crear_tecnico_rapido" in request.POST and Tecnico and empresa:
            nombre = request.POST.get("nombre", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            direccion = request.POST.get("direccion", "").strip()
            if len(nombre) < 2:
                messages.error(request, "Nombre de técnico demasiado corto.")
            elif Tecnico.objects.filter(empresa=empresa, nombre__iexact=nombre).exists():
                messages.error(request, f'Ya existe un técnico llamado "{nombre}".')
            else:
                Tecnico.objects.create(
                    empresa=empresa,
                    nombre=nombre,
                    telefono=telefono,
                    direccion=direccion,
                )
                messages.success(request, f'Técnico "{nombre}" creado.')
        elif "toggle_tecnico" in request.POST and Tecnico and empresa:
            tec_id = request.POST.get("toggle_tecnico")
            tec = Tecnico.objects.by_empresa(empresa).filter(id=tec_id).first()
            if tec:
                tec.activo = not tec.activo
                tec.save()
                messages.success(
                    request,
                    f'Técnico "{tec.nombre}" ahora está {"activo" if tec.activo else "inactivo"}.',
                )
            else:
                messages.error(request, "Técnico no encontrado o no pertenece a tu empresa.")

    # Técnicos asociados (si el modelo existe)
    tecnicos = []
    if Tecnico and empresa:
        tecnicos = list(Tecnico.objects.filter(empresa=empresa).order_by("nombre")[:25])

    # Resolver URL crear técnico de forma segura (evita NoReverseMatch en template)
    crear_tecnico_url = None
    for name in [
        "taller:tecnicos:nuevo",
        "tecnicos:crear_tecnico",
        "taller:crear_tecnico",
        "crear_tecnico",
    ]:
        try:
            crear_tecnico_url = reverse(name)
            break
        except NoReverseMatch:
            continue

    context = {
        "empresa": empresa,
        "empresa_form": empresa_form,
        "datos_form": datos_form,
        "created": created,
        "tecnicos": tecnicos,
        "crear_tecnico_url": crear_tecnico_url,
        "enable_space_bg": 2,  # modo ligero para esta página
    }
    return render(request, "taller/configuracion.html", context)
