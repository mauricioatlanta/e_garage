# taller/views_extra/cortesia_admin.py
"""
Vistas administrativas para otorgar extensiones de cortesía
"""

import logging
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from taller.forms.cortesia import CortesiaExtensionForm
from taller.models.empresa import Empresa

logger = logging.getLogger(__name__)


@staff_member_required
def cortesia_extension_view(request):
    """
    Vista principal para otorgar extensiones de cortesía
    """
    if request.method == "POST":
        form = CortesiaExtensionForm(request.POST)

        if form.is_valid():
            try:
                user_email = form.cleaned_data["user_email"]
                duration_months = int(form.cleaned_data["duration_months"])
                reason = form.cleaned_data.get("reason", "")

                # Otorgar la cortesía
                result = Empresa.admin_grant_courtesy_extension(
                    user_email=user_email,
                    duration_months=duration_months,
                    reason=reason,
                    admin_user=request.user,
                )

                # Mensaje de éxito
                duration_display = {
                    1: "1 mes",
                    6: "6 meses",
                    12: "1 año",
                }.get(duration_months, f"{duration_months} meses")

                messages.success(
                    request,
                    f"✅ Extensión de cortesía otorgada exitosamente. "
                    f"Se extendió la suscripción de {result['empresa']} por {duration_display}. "
                    f"Notificación enviada al cliente.",
                )

                logger.info(
                    f"Admin {request.user.username} otorgó cortesía de {duration_months} meses "
                    f"a {user_email}. Razón: {reason}"
                )

                # Redirigir a la misma página para mostrar el mensaje
                return redirect("admin_monitoring:cortesia_extension")

            except ValueError as e:
                messages.error(request, f"❌ Error: {str(e)}")
                logger.error(f"Error al otorgar cortesía: {str(e)}")
            except Exception as e:
                messages.error(request, f"❌ Error inesperado al otorgar la cortesía: {str(e)}")
                logger.error(f"Error inesperado al otorgar cortesía: {str(e)}", exc_info=True)
    else:
        form = CortesiaExtensionForm()

    # Obtener historial reciente de cortesías (últimas 10)
    from taller.models.auditoria import LogAuditoria

    cortesias_recientes = LogAuditoria.objects.filter(
        modelo="EMPRESA",
        accion="UPDATE",
        descripcion__icontains="Extensión de cortesía",
    ).order_by("-fecha_hora")[:10]

    context = {
        "form": form,
        "cortesias_recientes": cortesias_recientes,
        "page_title": "Otorgar Extensión de Cortesía",
    }

    return render(request, "admin_panel/cortesia_extension.html", context)


@staff_member_required
@require_http_methods(["POST"])
def cortesia_extension_api(request):
    """
    API endpoint para otorgar cortesías (para uso con AJAX)
    """
    try:
        user_email = request.POST.get("user_email")
        duration_months = int(request.POST.get("duration_months"))
        reason = request.POST.get("reason", "")

        if not user_email:
            return JsonResponse(
                {"success": False, "error": "Email del usuario es requerido"}, status=400
            )

        if duration_months not in [1, 6, 12]:
            return JsonResponse(
                {"success": False, "error": "Duración inválida. Debe ser 1, 6 o 12 meses"},
                status=400,
            )

        # Otorgar la cortesía
        result = Empresa.admin_grant_courtesy_extension(
            user_email=user_email,
            duration_months=duration_months,
            reason=reason,
            admin_user=request.user,
        )

        logger.info(
            f"Admin {request.user.username} otorgó cortesía de {duration_months} meses "
            f"a {user_email} via API"
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Extensión de cortesía otorgada exitosamente",
                "data": result,
            }
        )

    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error en API de cortesía: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "error": f"Error inesperado: {str(e)}"}, status=500)
