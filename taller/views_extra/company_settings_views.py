from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render

from taller.forms.configuracion_empresa import ConfiguracionEmpresaForm
from taller.models import Tecnico
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
        # Verificar si es un formulario de técnico
        if "crear_tecnico" in request.POST:
            # Manejar creación de técnico
            nombre = request.POST.get("nombre", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            direccion = request.POST.get("direccion", "").strip()

            if nombre:
                try:
                    Tecnico.objects.create(
                        nombre=nombre,
                        telefono=telefono,
                        direccion=direccion,
                        empresa=empresa,
                        activo=True,
                    )
                    messages.success(
                        request, f"✅ Técnico '{nombre}' creado exitosamente."
                    )
                except Exception as e:
                    messages.error(request, f"❌ Error al crear técnico: {str(e)}")
            else:
                messages.error(request, "❌ El nombre del técnico es obligatorio.")

            return redirect(request.path)

        # Manejar toggle de técnico
        elif "toggle_tecnico" in request.POST:
            tecnico_id = request.POST.get("toggle_tecnico")
            try:
                tecnico = Tecnico.objects.get(id=tecnico_id, empresa=empresa)
                tecnico.activo = not tecnico.activo
                tecnico.save()
                estado = "activado" if tecnico.activo else "desactivado"
                messages.success(
                    request, f"✅ Técnico '{tecnico.nombre}' {estado} exitosamente."
                )
            except Tecnico.DoesNotExist:
                messages.error(request, "❌ Técnico no encontrado.")
            except Exception as e:
                messages.error(request, f"❌ Error al actualizar técnico: {str(e)}")

            return redirect(request.path)

        # Manejar formulario de configuración de empresa
        else:
            form = ConfiguracionEmpresaForm(
                request.POST, request.FILES, instance=config, request=request
            )
            if form.is_valid():
                cfg = form.save()

                # Invalidar caché de branding para que se actualice en todas las páginas
                cache_key = f"company_branding_{request.user.id}"
                cache.delete(cache_key)

                messages.success(
                    request,
                    "✅ Configuración actualizada correctamente. Los cambios se reflejarán en todas las páginas.",
                )
                return redirect(request.path)
            else:
                messages.error(
                    request, "❌ Revisa los campos, hay errores en el formulario."
                )
    else:
        form = ConfiguracionEmpresaForm(instance=config, request=request)

    # Obtener técnicos de la empresa
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")

    return render(
        request, "settings/company_settings.html", {"form": form, "tecnicos": tecnicos}
    )
