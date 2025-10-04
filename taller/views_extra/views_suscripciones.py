from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from taller.forms.comprobante_form import ComprobantePagoForm
from taller.models.comprobante_pago import ComprobantePago
from taller.models.empresa import Empresa


def suspension(request):
    """Vista de suspensión por suscripción vencida"""
    if not request.user.is_authenticated:
        return redirect("login")

    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        messages.error(request, "No se encontró información de empresa")
        return redirect("taller:dashboard")

    # Si la suscripción está activa, redirigir al dashboard
    if not empresa.debe_bloquear:
        return redirect("taller:dashboard")

    # Obtener comprobantes pendientes
    comprobantes_pendientes = ComprobantePago.objects.filter(
        empresa=empresa, estado="pendiente"
    ).order_by("-fecha_subida")

    context = {
        "empresa": empresa,
        "comprobantes_pendientes": comprobantes_pendientes,
        "whatsapp_url": f"https://wa.me/56912345678?text=Hola, necesito renovar mi suscripción de eGarage para {empresa.nombre_taller}",
        "precios": {
            "basic": 15000,
            "premium": 25000,
            "enterprise": 45000,
        },
    }

    return render(request, "suspension/suspension.html", context)


@login_required
def subir_comprobante(request):
    """Vista para subir comprobante de pago"""
    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        messages.error(request, "No se encontró información de empresa")
        return redirect("taller:dashboard")

    if request.method == "POST":
        form = ComprobantePagoForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.empresa = empresa
            comprobante.save()

            messages.success(
                request,
                "Comprobante subido exitosamente. Te notificaremos cuando sea revisado.",
            )
            return redirect("suspension")
    else:
        form = ComprobantePagoForm()

    context = {
        "form": form,
        "empresa": empresa,
    }

    return render(request, "suspension/subir_comprobante.html", context)


@login_required
def estado_suscripcion(request):
    """Vista AJAX para obtener estado de suscripción"""
    try:
        empresa = request.user.empresa
        data = {
            "dias_restantes": empresa.dias_restantes,
            "fecha_expiracion": empresa.fecha_expiracion.strftime("%d/%m/%Y"),
            "estado": empresa.estado_suscripcion,
            "debe_mostrar_alerta": empresa.debe_mostrar_alerta(),
            "mensaje_alerta": empresa.get_mensaje_alerta(),
            "color_estado": empresa.color_estado,
        }
        return JsonResponse(data)
    except Empresa.DoesNotExist:
        return JsonResponse({"error": "Empresa no encontrada"}, status=404)


def precios(request):
    """Vista pública con información de precios diferenciada por país"""
    from taller.models.precio_suscripcion import PrecioSuscripcion

    # Detectar país del usuario
    pais_usuario = "CL"  # Default Chile
    if request.user.is_authenticated and hasattr(request.user, "empresa"):
        pais_usuario = request.user.empresa.pais
    elif request.GET.get("country"):
        pais_usuario = request.GET.get("country").upper()

    # Obtener precios según el país usando el nuevo manager
    planes_precios = PrecioSuscripcion.objects.activos().para_pais(pais_usuario).order_by("precio")

    # Si no hay precios configurados, usar valores por defecto
    if not planes_precios.exists():
        # Crear estructura de precios por defecto
        planes = {
            "mensual": {
                "nombre": "Plan Mensual",
                "precio": 20000 if pais_usuario == "CL" else 20,
                "moneda": "CLP" if pais_usuario == "CL" else "USD",
                "caracteristicas": [
                    "Documentos ilimitados",
                    "Hasta 5 usuarios",
                    "Reportes básicos",
                    "Soporte por email",
                ],
            },
            "semestral": {
                "nombre": "Plan Semestral",
                "precio": 110000 if pais_usuario == "CL" else 110,
                "moneda": "CLP" if pais_usuario == "CL" else "USD",
                "caracteristicas": [
                    "Todo del Plan Mensual",
                    "Reportes avanzados",
                    "Diagnóstico IA incluido",
                    "Soporte prioritario",
                ],
            },
            "anual": {
                "nombre": "Plan Anual",
                "precio": 200000 if pais_usuario == "CL" else 200,
                "moneda": "CLP" if pais_usuario == "CL" else "USD",
                "caracteristicas": [
                    "Todo del Plan Semestral",
                    "API personalizada",
                    "Multi-sucursales",
                    "Soporte 24/7",
                ],
            },
        }
    else:
        # Usar precios de la base de datos
        planes = {}
        for precio in planes_precios:
            planes[precio.tipo_plan] = {
                "nombre": precio.nombre_plan,
                "precio": precio.precio,
                "moneda": precio.moneda,
                "caracteristicas": precio.caracteristicas_list(),
                "precio_formateado": precio.precio_formateado(),
            }

    # Información de contacto según el país
    whatsapp_contacto = "https://wa.me/56912345678?text=Hola, quiero información sobre los planes de eGarage"
    if pais_usuario == "US":
        whatsapp_contacto = (
            "https://wa.me/15551234567?text=Hi, I want information about eGarage plans"
        )

    context = {
        "planes": planes,
        "pais_usuario": pais_usuario,
        "whatsapp_contacto": whatsapp_contacto,
        "moneda_simbolo": "$",
        "es_chile": pais_usuario == "CL",
        "es_usa": pais_usuario == "US",
    }

    return render(request, "suspension/precios.html", context)
