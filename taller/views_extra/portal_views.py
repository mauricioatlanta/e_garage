"""
🌐 VIEWS DEL PORTAL DE CLIENTES
==============================

Views para el portal web donde los clientes pueden:
- Iniciar sesión y ver sus documentos
- Solicitar presupuestos
- Revisar historial de servicios
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from taller.models.cliente import Cliente
from taller.models.documento import Documento
from taller.models.portal_cliente import (
    AccesoPortal,
    ClienteUsuario,
    PortalConfiguracion,
    SolicitudPresupuesto,
)
from taller.models.vehiculos import Vehiculo


def portal_login(request):
    """Vista de login del portal de clientes"""

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # 🔒 SEGURIDAD: Filtrar por empresa si es posible (aunque en login no tenemos empresa aún)
            # Buscar cliente por email
            # Nota: En login público, no podemos filtrar por empresa, pero debemos validar
            # que el cliente tiene empresa asignada
            cliente = Cliente.objects.filter(email_cliente=email).first()
            if not cliente:
                messages.error(request, "Cliente no encontrado")
                return render(request, "portal/login.html")

            # Validar que el cliente tiene empresa asignada
            if not hasattr(cliente, "empresa") or not cliente.empresa:
                messages.error(request, "Cliente no encontrado")
                return render(request, "portal/login.html")

            # Verificar si existe usuario del portal
            cliente_usuario = ClienteUsuario.objects.filter(cliente=cliente).first()
            if not cliente_usuario:
                messages.error(request, "Acceso al portal no configurado")
                return render(request, "portal/login.html")

            # Autenticar
            user = authenticate(request, username=cliente_usuario.user.username, password=password)
            if user:
                login(request, user)

                # Registrar acceso
                AccesoPortal.objects.create(
                    cliente_usuario=cliente_usuario,
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=request.headers.get("user-agent", ""),
                    pagina_visitada="login",
                    accion_realizada="login_exitoso",
                )

                # Actualizar último acceso
                cliente_usuario.ultimo_acceso = timezone.now()
                cliente_usuario.save()

                return redirect("portal_dashboard")
            else:
                messages.error(request, "Credenciales incorrectas")

        except Exception as e:
            messages.error(request, f"Error en el sistema: {str(e)}")

    return render(request, "portal/login.html")


@login_required
def portal_dashboard(request):
    """Dashboard principal del portal de clientes"""

    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente

        # Obtener configuración del portal
        portal_config = PortalConfiguracion.objects.filter(empresa=cliente.empresa).first()

        # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
        # Estadísticas básicas
        # Nota: Este código usa campos legacy (id_cliente). Debe migrar a 'cliente'
        vehiculos = Vehiculo.objects.filter(cliente=cliente, empresa=cliente.empresa)
        documentos_recientes = Documento.objects.filter(
            cliente=cliente, empresa=cliente.empresa
        ).order_by("-fecha_emision")[:5]

        solicitudes_pendientes = SolicitudPresupuesto.objects.filter(
            cliente=cliente, estado__in=["PENDIENTE", "EN_REVISION"]
        ).count()

        context = {
            "cliente": cliente,
            "vehiculos": vehiculos,
            "documentos_recientes": documentos_recientes,
            "solicitudes_pendientes": solicitudes_pendientes,
            "portal_config": portal_config,
        }

        # Registrar acceso
        AccesoPortal.objects.create(
            cliente_usuario=cliente_usuario,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.headers.get("user-agent", ""),
            pagina_visitada="dashboard",
            accion_realizada="vista_dashboard",
        )

        return render(request, "portal/dashboard.html", context)

    except ClienteUsuario.DoesNotExist:
        messages.error(request, "Acceso no autorizado")
        return redirect("portal_login")


@login_required
def portal_documentos(request):
    """Vista de documentos del cliente"""

    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente

        # Filtros
        vehiculo_id = request.GET.get("vehiculo")
        tipo_doc = request.GET.get("tipo")
        fecha_desde = request.GET.get("fecha_desde")
        fecha_hasta = request.GET.get("fecha_hasta")

        # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
        # Query base
        # Nota: Migrado de id_cliente a cliente, id_vehiculo a vehiculo, fecha_documento a fecha_emision, tipo_documento a tipo
        documentos = Documento.objects.filter(cliente=cliente, empresa=cliente.empresa)

        # Aplicar filtros
        if vehiculo_id:
            documentos = documentos.filter(vehiculo_id=vehiculo_id)
        if tipo_doc:
            documentos = documentos.filter(tipo=tipo_doc)
        if fecha_desde:
            documentos = documentos.filter(fecha_emision__gte=fecha_desde)
        if fecha_hasta:
            documentos = documentos.filter(fecha_emision__lte=fecha_hasta)

        documentos = documentos.order_by("-fecha_emision")

        # Paginación
        paginator = Paginator(documentos, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
        # Datos para filtros
        vehiculos = Vehiculo.objects.filter(cliente=cliente, empresa=cliente.empresa)
        tipos_documento = (
            Documento.objects.filter(cliente=cliente, empresa=cliente.empresa)
            .values_list("tipo", flat=True)
            .distinct()
        )

        context = {
            "cliente": cliente,
            "page_obj": page_obj,
            "vehiculos": vehiculos,
            "tipos_documento": tipos_documento,
            "filtros": {
                "vehiculo_id": vehiculo_id,
                "tipo_doc": tipo_doc,
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
            },
        }

        # Registrar acceso
        AccesoPortal.objects.create(
            cliente_usuario=cliente_usuario,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.headers.get("user-agent", ""),
            pagina_visitada="documentos",
            accion_realizada="vista_documentos",
        )

        return render(request, "portal/documentos.html", context)

    except ClienteUsuario.DoesNotExist:
        messages.error(request, "Acceso no autorizado")
        return redirect("portal_login")


@login_required
def portal_solicitar_presupuesto(request):
    """Vista para solicitar presupuestos"""

    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente

        if request.method == "POST":
            # Procesar solicitud
            vehiculo_id = request.POST.get("vehiculo")
            titulo = request.POST.get("titulo")
            descripcion = request.POST.get("descripcion")
            prioridad = request.POST.get("prioridad", "MEDIA")
            fecha_deseada = request.POST.get("fecha_deseada")

            try:
                # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
                vehiculo = Vehiculo.objects.get(
                    id=vehiculo_id, cliente=cliente, empresa=cliente.empresa
                )

                solicitud = SolicitudPresupuesto.objects.create(
                    empresa=cliente.empresa,
                    cliente=cliente,
                    vehiculo=vehiculo,
                    titulo=titulo,
                    descripcion=descripcion,
                    prioridad=prioridad,
                    fecha_deseada=fecha_deseada if fecha_deseada else None,
                )

                messages.success(
                    request,
                    f"Solicitud {solicitud.numero_solicitud} creada exitosamente",
                )

                # Registrar acceso
                AccesoPortal.objects.create(
                    cliente_usuario=cliente_usuario,
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=request.headers.get("user-agent", ""),
                    pagina_visitada="solicitar_presupuesto",
                    accion_realizada=f"crear_solicitud_{solicitud.numero_solicitud}",
                )

                return redirect("portal_mis_solicitudes")

            except Vehiculo.DoesNotExist:
                messages.error(request, "Vehículo no válido")
            except Exception as e:
                messages.error(request, f"Error al crear solicitud: {str(e)}")

        # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
        # Obtener vehículos del cliente
        vehiculos = Vehiculo.objects.filter(cliente=cliente, empresa=cliente.empresa)

        context = {
            "cliente": cliente,
            "vehiculos": vehiculos,
        }

        return render(request, "portal/solicitar_presupuesto.html", context)

    except ClienteUsuario.DoesNotExist:
        messages.error(request, "Acceso no autorizado")
        return redirect("portal_login")


@login_required
def portal_mis_solicitudes(request):
    """Vista de solicitudes del cliente"""

    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente

        # Obtener solicitudes
        solicitudes = SolicitudPresupuesto.objects.filter(cliente=cliente).order_by("-created_at")

        # Paginación
        paginator = Paginator(solicitudes, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "cliente": cliente,
            "page_obj": page_obj,
        }

        # Registrar acceso
        AccesoPortal.objects.create(
            cliente_usuario=cliente_usuario,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.headers.get("user-agent", ""),
            pagina_visitada="mis_solicitudes",
            accion_realizada="vista_solicitudes",
        )

        return render(request, "portal/mis_solicitudes.html", context)

    except ClienteUsuario.DoesNotExist:
        messages.error(request, "Acceso no autorizado")
        return redirect("portal_login")


@login_required
def portal_vehiculos(request):
    """Vista de vehículos del cliente"""

    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente

        # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
        vehiculos = Vehiculo.objects.filter(cliente=cliente, empresa=cliente.empresa)

        context = {
            "cliente": cliente,
            "vehiculos": vehiculos,
        }

        # Registrar acceso
        AccesoPortal.objects.create(
            cliente_usuario=cliente_usuario,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.headers.get("user-agent", ""),
            pagina_visitada="vehiculos",
            accion_realizada="vista_vehiculos",
        )

        return render(request, "portal/vehiculos.html", context)

    except ClienteUsuario.DoesNotExist:
        messages.error(request, "Acceso no autorizado")
        return redirect("portal_login")


def portal_logout(request):
    """Logout del portal"""
    logout(request)
    messages.info(request, "Sesión cerrada exitosamente")
    return redirect("portal_login")


# AJAX Views
@login_required
def ajax_detalle_documento(request, documento_id):
    """Vista AJAX para obtener detalles de un documento"""

    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente

        # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
        documento = get_object_or_404(
            Documento, id=documento_id, cliente=cliente, empresa=cliente.empresa
        )

        # Nota: Campos migrados de legacy a actuales
        data = {
            "numero": getattr(documento, "numero", getattr(documento, "numero_documento", "")),
            "fecha": documento.fecha_emision.strftime("%d/%m/%Y"),
            "tipo": documento.tipo,
            "vehiculo": (
                f"{documento.vehiculo.marca_texto or documento.vehiculo.marca} {documento.vehiculo.modelo_texto or documento.vehiculo.modelo}"
                if documento.vehiculo
                else "N/A"
            ),
            "total": float(documento.total),
            "observaciones": getattr(documento, "observaciones", ""),
        }

        return JsonResponse(data)

    except ClienteUsuario.DoesNotExist:
        return JsonResponse({"error": "Acceso no autorizado"}, status=403)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
