from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from taller.forms.configuracion_empresa import ConfiguracionEmpresaForm
from taller.utils.empresa import get_or_create_empresa  # tu helper


@login_required(login_url=None)  # usa tu LOGIN_URL global
def company_settings_view(request):
    empresa = get_or_create_empresa(request)
    config = getattr(empresa, "configuracionempresa", None)
    if config is None:
        # crear en caliente si no existe usando get_or_create para evitar duplicados
        from taller.models import ConfiguracionEmpresa

        config, created = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)

    if request.method == "POST":
        form = ConfiguracionEmpresaForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            cfg = form.save()
            messages.success(request, "Configuración actualizada.")
            return redirect(request.path)
        else:
            messages.error(request, "Revisa los campos, hay errores en el formulario.")
    else:
        form = ConfiguracionEmpresaForm(instance=config)

    return render(request, "settings/company_settings.html", {"form": form})
