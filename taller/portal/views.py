"""
Vistas del Portal del Cliente - Acceso público para clientes finales
"""

import logging

from django.contrib import messages
from django.contrib.auth import login
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.portal.models import ClienteCredencial, ClienteToken
from taller.reportes.kilometraje_reportes import ReporteKilometraje

logger = logging.getLogger(__name__)


def portal_login(request):
    """
    Vista de login para el portal del cliente.
    Permite autenticación por token o por credenciales.
    """
    if request.method == "POST":
        token = request.POST.get("token")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Autenticación por token
        if token:
            try:
                cliente_token = ClienteToken.objects.get(token=token)
                if not cliente_token.es_valido():
                    messages.error(request, "El enlace ha expirado o ya fue usado.")
                    return render(request, "taller/portal/login.html")

                # Token válido, crear sesión
                cliente = cliente_token.cliente
                request.session["cliente_id"] = cliente.id
                request.session["cliente_token_id"] = cliente_token.id

                # Marcar token como usado
                ip = request.META.get("REMOTE_ADDR")
                cliente_token.usar(ip=ip)

                messages.success(request, f"¡Bienvenido, {cliente.nombre}!")
                return redirect("portal:historial")

            except ClienteToken.DoesNotExist:
                messages.error(request, "Enlace inválido.")

        # Autenticación por credenciales
        elif email and password:
            try:
                credencial = ClienteCredencial.objects.get(email=email, activo=True)
                if credencial.check_password(password):
                    # Contraseña correcta
                    cliente = credencial.cliente
                    request.session["cliente_id"] = cliente.id
                    credencial.actualizar_ultimo_acceso()

                    messages.success(request, f"¡Bienvenido, {cliente.nombre}!")
                    return redirect("portal:historial")
                else:
                    messages.error(request, "Email o contraseña incorrectos.")
            except ClienteCredencial.DoesNotExist:
                messages.error(request, "Email o contraseña incorrectos.")

    # GET request o error en POST
    token = request.GET.get("token")
    return render(request, "taller/portal/login.html", {"token": token})


def portal_logout(request):
    """Cerrar sesión del portal"""
    if "cliente_id" in request.session:
        del request.session["cliente_id"]
    if "cliente_token_id" in request.session:
        del request.session["cliente_token_id"]

    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("portal:login")


def _get_cliente_autenticado(request):
    """
    Helper para obtener el cliente autenticado desde la sesión.

    Returns:
        Cliente: Instancia del cliente o None
    """
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        return None

    try:
        return Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        return None


def require_cliente_login(view_func):
    """
    Decorator para requerir autenticación de cliente.
    Similar a @login_required pero para clientes.
    """

    def wrapper(request, *args, **kwargs):
        cliente = _get_cliente_autenticado(request)
        if not cliente:
            messages.warning(request, "Por favor, inicia sesión para acceder a esta página.")
            return redirect("portal:login")
        return view_func(request, *args, **kwargs)

    return wrapper


@require_cliente_login
def portal_historial(request):
    """
    Vista principal del portal - Muestra historial de mantenimiento
    de todos los vehículos del cliente.
    """
    cliente = _get_cliente_autenticado(request)
    if not cliente:
        return redirect("portal:login")

    # Obtener todos los vehículos del cliente
    vehiculos = (
        Vehiculo.objects.filter(cliente=cliente, empresa=cliente.empresa)
        .select_related("cliente")
        .order_by("-id")
    )

    # Obtener historial para cada vehículo
    historiales = []
    if vehiculos.exists():
        reporte = ReporteKilometraje(cliente.empresa)

        for vehiculo in vehiculos:
            historial_data = reporte.historial_mantenimiento_vehiculo(vehiculo)
            historiales.append({"vehiculo": vehiculo, "historial_data": historial_data})

    context = {
        "cliente": cliente,
        "vehiculos": vehiculos,
        "historiales": historiales,
    }

    return render(request, "taller/portal/historial.html", context)


@require_cliente_login
def portal_historial_vehiculo(request, vehiculo_id):
    """
    Vista detallada del historial de un vehículo específico.
    """
    cliente = _get_cliente_autenticado(request)
    if not cliente:
        return redirect("portal:login")

    # Verificar que el vehículo pertenece al cliente
    try:
        vehiculo = Vehiculo.objects.get(pk=vehiculo_id, cliente=cliente, empresa=cliente.empresa)
    except Vehiculo.DoesNotExist:
        raise Http404("Vehículo no encontrado")

    # Obtener historial
    reporte = ReporteKilometraje(cliente.empresa)
    historial_data = reporte.historial_mantenimiento_vehiculo(vehiculo)

    context = {
        "cliente": cliente,
        "vehiculo": vehiculo,
        "historial_data": historial_data,
    }

    return render(request, "taller/portal/historial_vehiculo.html", context)


@require_cliente_login
def portal_exportar_pdf(request, vehiculo_id):
    """
    Exportar historial a PDF desde el portal.
    Reutiliza la vista de reportes pero con validación de cliente.
    """
    cliente = _get_cliente_autenticado(request)
    if not cliente:
        return redirect("portal:login")

    # Verificar que el vehículo pertenece al cliente
    try:
        vehiculo = Vehiculo.objects.get(pk=vehiculo_id, cliente=cliente, empresa=cliente.empresa)
    except Vehiculo.DoesNotExist:
        raise Http404("Vehículo no encontrado")

    # Reutilizar la vista de exportación de reportes
    from taller.reportes.views import exportar_historial_pdf

    return exportar_historial_pdf(request, vehiculo_id)
