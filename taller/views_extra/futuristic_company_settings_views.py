import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from taller.context_processors import invalidate_company_cache
from taller.models.company_settings import CompanySettings
from taller.models.tecnico import Tecnico
from taller.utils.empresa import get_or_create_empresa


@login_required(login_url=None)
def futuristic_company_settings_view(request):
    """
    Vista futurista para configuración de empresa y gestión de técnicos
    """
    empresa = get_or_create_empresa(request)

    # Obtener o crear configuración de empresa
    company_settings, created = CompanySettings.objects.get_or_create(
        user=request.user,
        defaults={
            "company_name": empresa.nombre_taller or f"Taller de {request.user.username}",
            "primary_color": "#00ffff",
            "currency": "USD" if empresa.pais == "US" else "CLP",
        },
    )

    # Obtener técnicos de la empresa
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")

    if request.method == "POST":
        section = request.POST.get("section")

        if section == "company":
            return handle_company_settings(request, company_settings)
        elif section == "technician":
            return handle_technician_management(request, empresa)

    context = {
        "company_settings": company_settings,
        "tecnicos": tecnicos,
        "empresa": empresa,
    }

    return render(request, "taller/us/en/settings/futuristic_company_settings.html", context)


def handle_company_settings(request, company_settings):
    """
    Maneja la actualización de configuración de empresa
    """
    try:
        # Actualizar campos básicos
        company_settings.company_name = request.POST.get("company_name", "")
        company_settings.tagline = request.POST.get("tagline", "")
        company_settings.address = request.POST.get("address", "")
        company_settings.phone = request.POST.get("phone", "")
        company_settings.email = request.POST.get("email", "")
        company_settings.website = request.POST.get("website", "")
        company_settings.primary_color = request.POST.get("primary_color", "#00ffff")
        company_settings.currency = request.POST.get("currency", "USD")

        # Manejar logo
        if "logo" in request.FILES:
            company_settings.logo = request.FILES["logo"]

        company_settings.save()

        # Actualizar también la empresa principal
        empresa = company_settings.user.empresa
        empresa.nombre_taller = company_settings.company_name
        empresa.telefono = company_settings.phone
        empresa.email = company_settings.email
        empresa.direccion = company_settings.address
        empresa.save()

        # Invalidar caché para actualizar la cabecera
        invalidate_company_cache(request.user)

        messages.success(request, "✅ Company profile updated successfully!")

    except Exception as e:
        messages.error(request, f"❌ Error updating company profile: {str(e)}")

    return redirect(request.path)


def handle_technician_management(request, empresa):
    """
    Maneja la gestión de técnicos (agregar, editar, activar/desactivar, eliminar)
    """
    action = request.POST.get("action")

    try:
        if action == "add":
            return add_technician(request, empresa)
        elif action == "toggle":
            return toggle_technician(request, empresa)
        elif action == "delete":
            return delete_technician(request, empresa)
        elif action == "edit":
            return edit_technician(request, empresa)

    except Exception as e:
        messages.error(request, f"❌ Error in technician management: {str(e)}")

    return redirect(request.path)


def add_technician(request, empresa):
    """
    Agrega un nuevo técnico
    """
    nombre = request.POST.get("nombre", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    direccion = request.POST.get("direccion", "").strip()

    if not nombre or len(nombre) < 2:
        messages.error(request, "❌ Technician name must be at least 2 characters long.")
        return redirect(request.path)

    # Verificar si ya existe un técnico con ese nombre
    if Tecnico.objects.filter(empresa=empresa, nombre__iexact=nombre).exists():
        messages.error(request, f"❌ A technician named '{nombre}' already exists.")
        return redirect(request.path)

    tecnico = Tecnico.objects.create(
        empresa=empresa,
        nombre=nombre,
        telefono=telefono if telefono else None,
        direccion=direccion if direccion else None,
        activo=True,
    )

    messages.success(request, f"✅ Technician '{nombre}' added successfully!")
    return redirect(request.path)


def toggle_technician(request, empresa):
    """
    Activa o desactiva un técnico
    """
    technician_id = request.POST.get("technician_id")
    activate = request.POST.get("activate") == "true"

    try:
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        tecnico.activo = activate
        tecnico.save()

        status = "activated" if activate else "deactivated"
        messages.success(request, f"✅ Technician '{tecnico.nombre}' {status} successfully!")

    except Tecnico.DoesNotExist:
        messages.error(request, "❌ Technician not found.")

    return redirect(request.path)


def delete_technician(request, empresa):
    """
    Elimina un técnico
    """
    technician_id = request.POST.get("technician_id")

    try:
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        nombre = tecnico.nombre
        tecnico.delete()

        messages.success(request, f"✅ Technician '{nombre}' deleted successfully!")

    except Tecnico.DoesNotExist:
        messages.error(request, "❌ Technician not found.")

    return redirect(request.path)


def edit_technician(request, empresa):
    """
    Edita un técnico existente
    """
    technician_id = request.POST.get("technician_id")
    nombre = request.POST.get("nombre", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    direccion = request.POST.get("direccion", "").strip()

    if not nombre or len(nombre) < 2:
        messages.error(request, "❌ Technician name must be at least 2 characters long.")
        return redirect(request.path)

    try:
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        tecnico.nombre = nombre
        tecnico.telefono = telefono if telefono else None
        tecnico.direccion = direccion if direccion else None
        tecnico.save()

        messages.success(request, f"✅ Technician '{nombre}' updated successfully!")

    except Tecnico.DoesNotExist:
        messages.error(request, "❌ Technician not found.")

    return redirect(request.path)


@csrf_exempt
@require_http_methods(["POST"])
def api_technician_toggle(request):
    """
    API endpoint para toggle de técnicos via AJAX
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
        technician_id = data.get("technician_id")
        activate = data.get("activate", False)

        empresa = request.user.empresa
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        tecnico.activo = activate
        tecnico.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Technician {tecnico.nombre} {'activated' if activate else 'deactivated'} successfully!",
                "technician": {
                    "id": tecnico.id,
                    "nombre": tecnico.nombre,
                    "activo": tecnico.activo,
                },
            }
        )

    except Tecnico.DoesNotExist:
        return JsonResponse({"error": "Technician not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_technician_delete(request):
    """
    API endpoint para eliminar técnicos via AJAX
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
        technician_id = data.get("technician_id")

        empresa = request.user.empresa
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        nombre = tecnico.nombre
        tecnico.delete()

        return JsonResponse(
            {"success": True, "message": f"Technician '{nombre}' deleted successfully!"}
        )

    except Tecnico.DoesNotExist:
        return JsonResponse({"error": "Technician not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
