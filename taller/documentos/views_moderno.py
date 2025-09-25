import json
import logging
from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


# Helper para obtener el parámetro country del request
def _country_from_request(request):
    return (
        getattr(request, "country_code", None)
        or getattr(request, "country", None)
        or "us"
    )


# API para búsqueda en tiempo real de repuestos
@csrf_exempt
@require_GET
def api_buscar_repuestos(request):
    query = request.GET.get("q", "").strip()

    # Obtener país desde la URL
    country = _country_from_request(request)
    if not country:
        path = request.path
        if path.startswith("/cl/"):
            country = "cl"
        elif path.startswith("/us/"):
            country = "us"
        else:
            country = "cl"

    # Obtener empresa del usuario autenticado o usar una demo para testing
    empresa = None
    if request.user.is_authenticated and hasattr(request.user, "empresa"):
        empresa = request.user.empresa
    else:
        # Para testing sin autenticación, usar empresa demo basada en el país
        if country.lower() == "us":
            empresa = Empresa.objects.filter(pais="US").first()
        else:
            empresa = Empresa.objects.filter(pais="CL").first()

        if not empresa:
            return JsonResponse({"repuestos": []})

    if len(query) < 2:
        return JsonResponse({"repuestos": []})
    repuestos = (
        Repuesto.objects.filter(empresa=empresa)
        .filter(Q(nombre__icontains=query) | Q(part_number__icontains=query))
        .values(
            "id",
            "part_number",
            "nombre",
            "precio_compra",
            "precio_venta",
            "cantidad_stock",
            "proveedor",
        )[:20]
    )
    return JsonResponse({"repuestos": list(repuestos)})


from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)
from taller.models.repuesto import Repuesto
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio as ServicioInterno
from taller.servicios.models import ServicioExterno


@login_required
def crear_documento_moderno(request):
    """Vista moderna para crear documentos con interfaz futurista"""

    # Obtener país desde la URL o request
    country = _country_from_request(request)
    if not country:
        # Detectar país desde el path de la URL
        path = request.path
        if path.startswith("/cl/"):
            country = "cl"
        elif path.startswith("/us/"):
            country = "us"
        else:
            country = "cl"  # fallback por defecto

    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={"nombre_taller": f"Taller de {request.user.username}"},
        )

    # Debug mode: mostrar template de debug
    if request.GET.get("debug") == "1":
        context = obtener_datos_formulario(empresa)
        context["country"] = country
        return render(request, "documentos/debug_documento.html", context)

    if request.method == "POST":
        return procesar_documento_moderno(request, empresa)

    # GET: Mostrar formulario usando template resolution
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    context = obtener_datos_formulario(empresa)
    context["country"] = country

    # Usar template resolution para documentos/documento_form.html
    template_name = select_country_lang_template(
        "documentos/documento_form.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    from django.template.response import TemplateResponse

    return TemplateResponse(request, template_name, context)


def obtener_datos_formulario(empresa):
    """Obtener todos los datos necesarios para el formulario"""

    # Obtener clientes de la empresa
    clientes = Cliente.objects.filter(empresa=empresa).order_by("nombre")

    # Obtener técnicos de la empresa
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")

    # Obtener servicios internos
    servicios_internos = ServicioInterno.objects.filter(empresa=empresa).select_related(
        "categoria"
    )

    # Obtener servicios externos
    servicios_externos = ServicioExterno.objects.filter(
        empresa=empresa, activo=True
    ).select_related("categoria")

    # Obtener repuestos
    repuestos = Repuesto.objects.filter(empresa=empresa).order_by("nombre")

    # Tipos de documento con colores y próximos números
    tipos_documento = []
    if empresa.pais == "US":
        tipos_base = [
            {"value": "PRES", "label": "Estimate", "color": "#4CAF50"},
            {"value": "OT", "label": "Work Order", "color": "#FF9800"},
            {"value": "FAC", "label": "Invoice", "color": "#F44336"},
        ]
    else:
        tipos_base = [
            {"value": "PRES", "label": "Presupuesto", "color": "#4CAF50"},
            {"value": "OT", "label": "Orden de Trabajo", "color": "#FF9800"},
            {"value": "FAC", "label": "Factura", "color": "#F44336"},
            {"value": "BOL", "label": "Boleta", "color": "#2196F3"},
        ]

    for tipo in tipos_base:
        # Calcular próximo número
        ultimo_doc = (
            Documento.objects.filter(empresa=empresa, tipo=tipo["value"])
            .order_by("-numero")
            .first()
        )

        proximo_numero = (
            (ultimo_doc.numero + 1) if ultimo_doc and ultimo_doc.numero else 1
        )

        # Generar preview del número de documento
        if empresa.pais == "US":
            prefijos = {"PRES": "E", "OT": "WO", "FAC": "I"}
        else:
            prefijos = {"PRES": "E", "OT": "OT", "FAC": "F", "BOL": "B"}

        prefijo = prefijos.get(tipo["value"], tipo["value"])
        numero_preview = f"{prefijo}-{proximo_numero:03d}"

        tipos_documento.append(
            {
                "value": tipo["value"],
                "label": tipo["label"],
                "color": tipo["color"],
                "numero_preview": numero_preview,
            }
        )

    return {
        "empresa": empresa,
        "clientes": clientes,
        "tecnicos": tecnicos,
        "servicios_internos": servicios_internos,
        "servicios_externos": servicios_externos,
        "repuestos": repuestos,
        "tipos_documento": tipos_documento,
        "today": now(),
    }


@login_required
@transaction.atomic
def procesar_documento_moderno_wrapper(request):
    """Wrapper para procesar documento que obtiene la empresa"""
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={"nombre_taller": f"Taller de {request.user.username}"},
        )

    return procesar_documento_moderno(request, empresa)


def procesar_documento_moderno(request, empresa):
    """Procesar la creación del documento con todas las líneas y totales correctos"""
    # 1) Validar método
    if request.method != "POST":
        # Renderizar formulario o redirigir a crear
        return redirect("documentos:crear_documento")

    try:
        # 2) Extraer campos base del documento
        tipo = request.POST.get("tipo")
        fecha_emision = request.POST.get("fecha") or now().date()
        cliente_id = request.POST.get("cliente")
        vehiculo_id = request.POST.get("vehiculo")
        tecnico_id = request.POST.get("tecnico") or None
        kilometraje = request.POST.get("kilometraje") or request.POST.get(
            "millas"
        )  # millas/odómetro
        estado = request.POST.get("estado", "borrador")
        incluir_impuesto = request.POST.get("incluir_impuesto") == "on"

        # Validaciones básicas
        if not all([tipo, fecha_emision, cliente_id]):
            messages.error(request, "Faltan campos obligatorios: tipo, fecha y cliente")
            return redirect("documentos:crear_documento")

        # Obtener objetos relacionados
        cliente = get_object_or_404(Cliente, id=cliente_id, empresa=empresa)
        tecnico = (
            get_object_or_404(Tecnico, id=tecnico_id, empresa=empresa)
            if tecnico_id
            else None
        )
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id) if vehiculo_id else None

        # 3) Crear/actualizar Documento
        documento = Documento.objects.create(
            empresa=empresa,
            tipo=tipo,
            fecha_emision=(
                datetime.strptime(str(fecha_emision), "%Y-%m-%d").date()
                if isinstance(fecha_emision, str)
                else fecha_emision
            ),
            cliente=cliente,
            tecnico_responsable=tecnico,
            vehiculo=vehiculo,
            estado=estado,
            country=empresa.pais,
            moneda="USD" if empresa.pais == "US" else "CLP",
            # Asignar millas/odómetro si el modelo lo tiene
            **(
                {"kilometraje": kilometraje}
                if hasattr(Documento, "kilometraje") and kilometraje
                else {}
            ),
        )

        # Generar número de documento
        ultimo_doc = (
            Documento.objects.filter(empresa=empresa, tipo=tipo)
            .order_by("-numero")
            .first()
        )
        proximo_numero = (
            (ultimo_doc.numero + 1) if ultimo_doc and ultimo_doc.numero else 1
        )
        documento.numero = proximo_numero
        documento.save()

        # Actualizar kilometraje del vehículo si se proporcionó
        if kilometraje and hasattr(vehiculo, "millas"):
            try:
                vehiculo.millas = int(kilometraje)
                vehiculo.save()
            except (ValueError, TypeError):
                pass  # Ignorar errores de conversión

        # 4) Recibir líneas desde el POST (arrays dinámicos o JSON)
        # Intentar JSON primero, luego arrays
        repuestos_data = []
        servicios_data = []
        otros_servicios_data = []

        # Intentar parsear desde JSON
        try:
            repuestos_data = json.loads(request.POST.get("repuestos_data", "[]"))
        except (json.JSONDecodeError, TypeError):
            # Fallback a arrays de POST
            rep_ids = request.POST.getlist("repuestos_ids[]") or request.POST.getlist(
                "repuesto_id[]"
            )
            rep_parts = request.POST.getlist(
                "repuestos_partnumber[]"
            ) or request.POST.getlist("repuesto_partnumber[]")
            rep_cant = request.POST.getlist("repuestos_cantidades[]")
            rep_precio = request.POST.getlist("repuestos_precios[]")
            rep_desc = request.POST.getlist("repuestos_descuentos[]")

            # LOG de diagnóstico (dejar temporalmente)
            print(
                "DEBUG rep_ids:",
                len(rep_ids or []),
                "rep_parts:",
                len(rep_parts or []),
                "cant:",
                len(rep_cant or []),
                "precio:",
                len(rep_precio or []),
                "desc:",
                len(rep_desc or []),
            )

            repuestos_data = []
            total_items = max(
                len(rep_ids or []),
                len(rep_parts or []),
                len(rep_cant or []),
                len(rep_precio or []),
                len(rep_desc or []),
            )
            for i in range(total_items):
                repuesto_id = (
                    rep_ids[i] if rep_ids and len(rep_ids) > i and rep_ids[i] else None
                )
                partnum = (
                    rep_parts[i]
                    if rep_parts and len(rep_parts) > i and rep_parts[i]
                    else None
                )
                if not repuesto_id and partnum:
                    rep_obj = Repuesto.objects.filter(
                        part_number__iexact=partnum, empresa=empresa
                    ).first()
                    repuesto_id = rep_obj.id if rep_obj else None
                    print(
                        f"DEBUG: Resolviendo part_number '{partnum}' -> repuesto_id={repuesto_id}"
                    )
                if not repuesto_id:
                    continue  # sin ID ni partnumber -> saltar

                repuestos_data.append(
                    {
                        "id": repuesto_id,
                        "cantidad": rep_cant[i] if i < len(rep_cant) else 1,
                        "precio": rep_precio[i] if i < len(rep_precio) else 0,
                        "descuento": rep_desc[i] if i < len(rep_desc) else 0,
                    }
                )

        try:
            servicios_data = json.loads(request.POST.get("servicios_data", "[]"))
        except (json.JSONDecodeError, TypeError):
            # Fallback a arrays de POST
            serv_nombres = request.POST.getlist("servicios_nombres[]")
            serv_cant = request.POST.getlist("servicios_cantidades[]")
            serv_precio = request.POST.getlist("servicios_precios[]")
            serv_desc = request.POST.getlist("servicios_descuentos[]")
            serv_codigo = request.POST.getlist("servicios_codigos[]")

            servicios_data = []
            for i, nombre in enumerate(serv_nombres or []):
                if nombre:
                    servicios_data.append(
                        {
                            "nombre": nombre,
                            "cantidad": serv_cant[i] if i < len(serv_cant) else 1,
                            "precio": serv_precio[i] if i < len(serv_precio) else 0,
                            "descuento": serv_desc[i] if i < len(serv_desc) else 0,
                            "codigo": serv_codigo[i] if i < len(serv_codigo) else "",
                        }
                    )

        try:
            otros_servicios_data = json.loads(
                request.POST.get("otros_servicios_data", "[]")
            )
        except (json.JSONDecodeError, TypeError):
            # Fallback a arrays de POST
            otro_emp = request.POST.getlist("otros_empresa_externa[]")
            otro_nombre = request.POST.getlist("otros_nombres[]")
            otro_cant = request.POST.getlist("otros_cantidades[]")
            otro_costo = request.POST.getlist("otros_costos_internos[]")
            otro_precio = request.POST.getlist("otros_precios_cliente[]")

            otros_servicios_data = []
            for i, nom in enumerate(otro_nombre or []):
                if nom:
                    otros_servicios_data.append(
                        {
                            "nombre": nom,
                            "empresa_externa": otro_emp[i] if i < len(otro_emp) else "",
                            "cantidad": otro_cant[i] if i < len(otro_cant) else 1,
                            "costo_interno": (
                                otro_costo[i] if i < len(otro_costo) else 0
                            ),
                            "precio_cliente": (
                                otro_precio[i] if i < len(otro_precio) else 0
                            ),
                        }
                    )

        # 5) Flag para heredar técnico a las líneas (dividir por técnico OFF => hereda)
        dividir_por_tecnico = False
        if hasattr(empresa, "configuracion") and hasattr(
            empresa.configuracion, "dividir_por_tecnico"
        ):
            dividir_por_tecnico = empresa.configuracion.dividir_por_tecnico

        # 6) Crear líneas de Repuestos
        for item in repuestos_data:
            if not item.get("id"):
                continue
            repuesto = get_object_or_404(Repuesto, id=item["id"], empresa=empresa)
            cantidad = Decimal(str(item.get("cantidad", 1)))
            precio = Decimal(str(item.get("precio", 0)))
            descuento = Decimal(str(item.get("descuento", 0)))

            LineaRepuesto.objects.create(
                documento=documento,
                repuesto=repuesto,
                codigo=getattr(repuesto, "part_number", "")
                or getattr(repuesto, "codigo", ""),
                nombre=repuesto.nombre,
                cantidad=cantidad,
                precio_unitario=precio,
                descuento=descuento,
                # herencia de técnico si aplica
                **(
                    {"tecnico_responsable": tecnico}
                    if not dividir_por_tecnico and tecnico
                    else {}
                ),
            )

        # 7) Crear líneas de Servicios
        print(f"[DEBUG] servicios_data recibido: {servicios_data}")
        print(f"[DEBUG] Cantidad de servicios a procesar: {len(servicios_data)}")

        for item in servicios_data:
            print(f"[DEBUG] Procesando servicio: {item}")
            nombre = item.get("nombre", "")
            if hasattr(item, "get") and item.get("id"):
                # Es un servicio existente
                servicio = get_object_or_404(
                    ServicioInterno, id=item["id"], empresa=empresa
                )
                nombre = servicio.nombre
                codigo = getattr(servicio, "codigo", f'SER-{item["id"]}')
            else:
                # Es un servicio personalizado
                codigo = item.get("codigo", "")

            if not nombre:
                print(f"[DEBUG] Servicio omitido - sin nombre: {item}")
                continue

            cantidad = Decimal(str(item.get("cantidad", 1)))
            precio = Decimal(str(item.get("precio", 0)))
            descuento = Decimal(str(item.get("descuento", 0)))

            linea_servicio = LineaServicio.objects.create(
                documento=documento,
                servicio=(
                    servicio if "servicio" in locals() and item.get("id") else None
                ),
                codigo=codigo,
                nombre=nombre,
                cantidad=cantidad,
                precio_unitario=precio,
                descuento=descuento,
                **(
                    {"tecnico_responsable": tecnico}
                    if not dividir_por_tecnico and tecnico
                    else {}
                ),
            )
            print(
                f"[DEBUG] Línea de servicio creada: {linea_servicio.id} - {nombre} - ${precio}"
            )

        print(f"[DEBUG] otros_servicios_data recibido: {otros_servicios_data}")
        print(
            f"[DEBUG] Cantidad de otros servicios a procesar: {len(otros_servicios_data)}"
        )

        # 8) Crear líneas de Otros Servicios Tercerizados
        for item in otros_servicios_data:
            print(f"[DEBUG] Procesando otro servicio: {item}")
            nombre = item.get("nombre", "")
            if hasattr(item, "get") and item.get("id"):
                # Es un servicio externo existente
                servicio_externo = get_object_or_404(
                    ServicioExterno, id=item["id"], empresa=empresa
                )
                nombre = servicio_externo.nombre
                empresa_externa = servicio_externo.empresa_externa
                costo_interno = servicio_externo.costo_taller
                precio_cliente = servicio_externo.precio_cliente
            else:
                # Es un servicio personalizado
                empresa_externa = item.get("empresa_externa", "")
                costo_interno = Decimal(str(item.get("costo_interno", 0)))
                precio_cliente = Decimal(str(item.get("precio_cliente", 0)))

            if not nombre:
                print(f"[DEBUG] Otro servicio omitido - sin nombre: {item}")
                continue

            cantidad = Decimal(str(item.get("cantidad", 1)))

            linea_otro_servicio = LineaOtroServicio.objects.create(
                documento=documento,
                servicio_externo=(
                    servicio_externo
                    if "servicio_externo" in locals() and item.get("id")
                    else None
                ),
                nombre=nombre,
                empresa_externa=empresa_externa,
                cantidad=cantidad,
                costo_interno=costo_interno,
                precio_cliente=precio_cliente,
                ganancia=precio_cliente - costo_interno,
                **(
                    {"tecnico_responsable": tecnico}
                    if not dividir_por_tecnico and tecnico
                    else {}
                ),
            )
            print(
                f"[DEBUG] Línea de otro servicio creada: {linea_otro_servicio.id} - {nombre} - ${precio_cliente}"
            )

        # 9) Recalcular totales (IVA solo sobre repuestos en Chile)
        rep_subtotal = sum(
            [
                lr.cantidad
                * lr.precio_unitario
                * (Decimal("1.0") - (lr.descuento or Decimal(0)) / Decimal("100"))
                for lr in documento.lineas_repuesto.all()
            ]
        )
        serv_subtotal = sum(
            [
                ls.cantidad
                * ls.precio_unitario
                * (Decimal("1.0") - (ls.descuento or Decimal(0)) / Decimal("100"))
                for ls in documento.lineas_servicio.all()
            ]
        )
        otro_subtotal = sum(
            [
                los.precio_cliente * los.cantidad
                for los in documento.lineas_otro_servicio.all()
            ]
        )

        # Calcular IVA según el país y configuración
        tax_amount = Decimal("0.00")
        tax_rate_applied = Decimal("0.00")

        if incluir_impuesto:
            if empresa.pais == "CL":
                # IVA 19% en Chile, solo sobre repuestos
                iva_rate = Decimal("19.00")
                tax_amount = (rep_subtotal * iva_rate / Decimal("100")).quantize(
                    Decimal("0.01")
                )
                tax_rate_applied = iva_rate
            elif empresa.pais == "US":
                # Tax sobre todo en USA
                tax_rate_usa = Decimal("8.50")  # Ajustable según configuración
                total_gravable = rep_subtotal + serv_subtotal + otro_subtotal
                tax_amount = (total_gravable * tax_rate_usa / Decimal("100")).quantize(
                    Decimal("0.01")
                )
                tax_rate_applied = tax_rate_usa

        total = (rep_subtotal + serv_subtotal + otro_subtotal + tax_amount).quantize(
            Decimal("0.01")
        )

        # 10) Persistir campos de totales en Documento
        documento.neto_repuestos = rep_subtotal
        documento.neto_servicios = serv_subtotal + otro_subtotal
        documento.tax_rate_applied = tax_rate_applied
        documento.tax_amount = tax_amount
        documento.total = total
        documento.save(
            update_fields=[
                "neto_repuestos",
                "neto_servicios",
                "tax_rate_applied",
                "tax_amount",
                "total",
            ]
        )

        messages.success(
            request,
            f"Documento {documento.tipo}-{documento.numero} creado exitosamente",
        )

        # 11) Redirección al listado (requisito #2)
        return redirect("documentos:lista_documentos")

    except Exception as e:
        messages.error(request, f"Error al crear documento: {str(e)}")
        return redirect("documentos:crear_documento")


@csrf_exempt
@require_GET
def api_vehiculos_cliente(request):
    """API para obtener vehículos de un cliente"""
    import logging

    logger = logging.getLogger(__name__)

    # Obtener país desde la URL
    country = _country_from_request(request)
    if not country:
        path = request.path
        if path.startswith("/cl/"):
            country = "cl"
        elif path.startswith("/us/"):
            country = "us"
        else:
            country = "cl"

    cliente_id = request.GET.get("cliente_id")
    logger.info(f"API vehiculos_cliente - cliente_id: {cliente_id}, country: {country}")

    if not cliente_id:
        return JsonResponse({"vehiculos": []})

    try:
        # Obtener empresa del usuario autenticado o usar una demo para testing
        empresa = None
        if request.user.is_authenticated and hasattr(request.user, "empresa"):
            empresa = request.user.empresa
        else:
            # Para testing sin autenticación, usar empresa demo basada en el país
            if country.lower() == "us":
                empresa = Empresa.objects.filter(pais="US").first()
            else:
                empresa = Empresa.objects.filter(pais="CL").first()

            if not empresa:
                logger.warning(f"No hay empresa configurada para país {country}")
                return JsonResponse({"vehiculos": []})

        logger.info(f"Empresa: {empresa.nombre_taller}")

        # Verificar que el cliente pertenece a la empresa
        cliente = Cliente.objects.filter(id=cliente_id, empresa=empresa).first()
        if not cliente:
            logger.warning(
                f"Cliente {cliente_id} no encontrado para empresa {empresa.id}"
            )
            return JsonResponse({"vehiculos": []})

        logger.info(f"Cliente encontrado: {cliente.nombre}")

        # Obtener vehículos asociados al cliente
        vehiculos = Vehiculo.objects.filter(cliente=cliente)
        logger.info(f"Vehículos encontrados: {vehiculos.count()}")

        vehiculos_data = []
        for v in vehiculos:
            vehiculos_data.append(
                {
                    "id": v.id,
                    "patente": v.patente,
                    "marca": v.marca.nombre if v.marca else "",
                    "modelo": v.modelo.nombre if v.modelo else "",
                    "anio": v.anio,
                }
            )

        logger.info(f"Retornando {len(vehiculos_data)} vehículos")
        return JsonResponse({"vehiculos": vehiculos_data})

    except Exception as e:
        logger.error(f"Error en api_vehiculos_cliente: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Error interno: {str(e)}"}, status=500)


@csrf_exempt
@require_GET
def api_buscar_servicios_internos(request):
    # Obtener el país desde la URL
    country = _country_from_request(request)
    """API para buscar servicios internos"""
    try:
        # Obtener empresa del usuario o una por defecto para testing
        if request.user.is_authenticated and hasattr(request.user, "empresa"):
            empresa = request.user.empresa
        else:
            # Para testing sin autenticación, usar la empresa demo USA
            empresa = Empresa.objects.filter(nombre_taller="USA Test Garage").first()
            if not empresa:
                # Si no existe la empresa demo, usar cualquier empresa USA
                empresa = Empresa.objects.filter(pais="US").first()
                if not empresa:
                    return JsonResponse(
                        {"error": "No hay empresa configurada"}, status=400
                    )

        query = request.GET.get("q", "")

        if len(query) < 2:
            return JsonResponse({"servicios": []})

        servicios = ServicioInterno.objects.filter(
            empresa=empresa, nombre__icontains=query
        ).values("id", "nombre")[:20]

        return JsonResponse({"servicios": list(servicios)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_obtener_numero_documento(request):
    # Obtener el país desde la URL
    country = _country_from_request(request)
    """API para obtener el próximo número de documento según el tipo"""
    if request.method != "GET":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    raw_tipo = (request.GET.get("tipo") or "").upper()

    # Mapear tipos legacy y nuevos
    tipo_map = {
        "FAC": "REC",  # Factura → Recibo
        "BOL": "REC",  # Boleta → Recibo
        "REC": "REC",  # Recibo (nuevo)
        "OT": "OT",  # Orden de Trabajo
        "PRES": "PRES",  # Presupuesto
    }
    tipo_documento = tipo_map.get(raw_tipo, "OT")  # por defecto OT

    if not tipo_documento:
        return JsonResponse({"error": "Tipo de documento requerido"}, status=400)

    try:
        # Obtener empresa del usuario o una por defecto para testing
        if request.user.is_authenticated and hasattr(request.user, "empresa"):
            empresa = request.user.empresa
        else:
            # Para testing sin autenticación, usar la empresa demo USA
            empresa = Empresa.objects.filter(nombre_taller="USA Test Garage").first()
            if not empresa:
                # Si no existe la empresa demo, usar cualquier empresa USA
                empresa = Empresa.objects.filter(pais="US").first()
                if not empresa:
                    return JsonResponse(
                        {"error": "No hay empresa configurada"}, status=400
                    )

        # Mapear códigos de tipo a nombres completos para prefijos
        tipo_mapping = {
            "FAC": "FACTURA",
            "PRES": "PRESUPUESTO",
            "OT": "ORDEN_TRABAJO",
            "REC": "RECIBO",  # Nuevo tipo
            "BOL": "BOLETA",
            "FACTURA": "FACTURA",
            "PRESUPUESTO": "PRESUPUESTO",
            "ORDEN_TRABAJO": "ORDEN_TRABAJO",
            "RECIBO": "RECIBO",
            "BOLETA": "BOLETA",
        }

        tipo_documento_normalizado = tipo_mapping.get(
            tipo_documento.upper(), tipo_documento.upper()
        )

        # Buscar el último número para este tipo de documento en esta empresa
        ultimo_doc = (
            Documento.objects.filter(
                empresa=empresa,
                tipo=tipo_documento,  # Usar el tipo original para la consulta DB
            )
            .order_by("-numero")
            .first()
        )

        if ultimo_doc and ultimo_doc.numero:
            proximo_numero = ultimo_doc.numero + 1
        else:
            proximo_numero = 1

        # Generar el número formateado según el país y tipo
        if empresa.pais == "US":
            prefijos = {
                "PRESUPUESTO": "E",  # Estimate
                "ORDEN_TRABAJO": "WO",  # Work Order
                "RECIBO": "R",  # Receipt
                "FACTURA": "I",  # Invoice (legacy)
                "BOLETA": "B",  # Boleta (legacy)
            }
        else:  # Chile
            prefijos = {
                "PRESUPUESTO": "E",  # Estimado
                "ORDEN_TRABAJO": "OT",  # Orden de Trabajo
                "RECIBO": "R",  # Recibo/Boleta
                "FACTURA": "F",  # Factura (legacy)
                "BOLETA": "B",  # Boleta (legacy)
            }

        prefijo = prefijos.get(tipo_documento_normalizado, "DOC")
        numero_formateado = f"{prefijo}-{proximo_numero:03d}"

        return JsonResponse(
            {
                "numero": numero_formateado,
                "tipo": tipo_documento,
                "secuencia": proximo_numero,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# === VISTA UNIFICADA CREAR/EDITAR ===

# === VISTA UNIFICADA CREAR/EDITAR ===


def _to_decimal_pct(txt: str) -> Decimal | None:
    """
    Convierte '8.5' o '8,5' o '8.5%' en Decimal 0.085, o None si vacío/no válido.
    """
    if not txt:
        return None
    s = txt.strip().replace("%", "").replace(",", ".")
    if not s:
        return None
    try:
        return (Decimal(s) / Decimal("100")).quantize(Decimal("0.0001"))
    except (InvalidOperation, ValueError):
        return None


@login_required
@transaction.atomic
def documento_form(request, pk=None):
    """Vista unificada para crear y editar documentos"""

    from django.db.models import Sum

    from taller.documentos.forms import DocumentoForm

    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={"nombre_taller": f"Taller de {request.user.username}"},
        )

    # Obtener el documento si estamos editando
    if pk:
        try:
            documento = Documento.objects.get(pk=pk, empresa=empresa)
        except Documento.DoesNotExist:
            # Proporcionar información de debug para 404
            from django.conf import settings

            if settings.DEBUG:
                # Verificar si el documento existe para otra empresa
                documento_exists = Documento.objects.filter(pk=pk).first()
                if documento_exists:
                    from django.http import HttpResponseNotFound

                    error_msg = f"""
                    <h1>Documento no encontrado (404)</h1>
                    <p><strong>El documento {pk} existe pero pertenece a otra empresa.</strong></p>
                    <ul>
                        <li>Tu empresa: {empresa.nombre_taller} (ID: {empresa.id})</li>
                        <li>Empresa del documento: {documento_exists.empresa.nombre_taller} (ID: {documento_exists.empresa.id})</li>
                        <li>Usuario del documento: {documento_exists.empresa.user.username}</li>
                        <li>Tu usuario: {request.user.username}</li>
                    </ul>
                    <p><strong>Solución:</strong> Inicia sesión como el usuario correcto o accede a un documento de tu empresa.</p>
                    """
                    return HttpResponseNotFound(error_msg)
            raise Http404(
                f"No se encontró el documento {pk} para la empresa {empresa.nombre_taller}"
            )
    else:
        documento = None

    # Obtener país desde el contexto de la empresa o request
    company_country = getattr(
        request, "company_country", getattr(empresa, "pais", None)
    )
    if not company_country:
        # Fallback desde la URL
        path = request.path
        if path.startswith("/cl/"):
            company_country = "CL"
        elif path.startswith("/us/"):
            company_country = "US"
        else:
            company_country = "CL"

    if request.method == "POST":
        form = DocumentoForm(
            request.POST, request.FILES or None, instance=documento, user=request.user
        )
        if form.is_valid():
            doc = (
                form.save()
            )  # Documento + lógica del form (kilometraje→vehiculo.millas, pagado, etc.)

            # ------------------------
            # Recalcular netos desde líneas (campos 'subtotal' existentes)
            # ------------------------
            neto_rep = doc.lineas_repuesto.aggregate(s=Sum("subtotal"))["s"] or Decimal(
                "0"
            )
            neto_serv = doc.lineas_servicio.aggregate(s=Sum("subtotal"))[
                "s"
            ] or Decimal("0")
            neto_otros = doc.lineas_otro_servicio.aggregate(
                s=Sum(
                    ExpressionWrapper(
                        F("precio_cliente") * F("cantidad"),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    )
                )
            )["s"] or Decimal("0")

            # ------------------------
            # Impuestos por país
            #   CL: IVA 19% SOLO sobre repuestos
            #   US: Sales tax opcional (checkbox) sobre repuestos + servicios (si aplica)
            # ------------------------
            if company_country == "CL":
                tax_base = neto_rep
                tax_rate = Decimal("0.19")
            else:
                apply_sales_tax = bool(request.POST.get("apply_sales_tax"))
                rate = _to_decimal_pct(
                    (request.POST.get("sales_tax_rate") or "").strip()
                )
                # fallback si no se envía tasa: conserva o 0
                tax_rate = (
                    rate
                    if (rate is not None and rate >= 0)
                    else (doc.tax_rate_applied or Decimal("0"))
                )
                tax_base = (neto_rep + neto_serv) if apply_sales_tax else Decimal("0")

            tax_amount = (tax_base * tax_rate).quantize(Decimal("0.01"))
            total = (neto_rep + neto_serv + neto_otros + tax_amount).quantize(
                Decimal("0.01")
            )

            # Persistir totales
            doc.neto_repuestos = neto_rep
            doc.neto_servicios = neto_serv
            doc.neto_otros = neto_otros
            doc.tax_rate_applied = tax_rate
            doc.tax_amount = tax_amount
            doc.total = total
            doc.save(
                update_fields=[
                    "neto_repuestos",
                    "neto_servicios",
                    "neto_otros",
                    "tax_rate_applied",
                    "tax_amount",
                    "total",
                ]
            )

            messages.success(request, "Cambios guardados.")
            return redirect("documentos:ver_documento_cbv", pk=doc.pk)

        # Form inválido → Diagnosticar y registrar errores detallados
        # POST keys y valores relevantes
        posted = {
            k: request.POST.get(k)
            for k in (
                "tipo",
                "numero",
                "fecha_emision",
                "cliente",
                "vehiculo",
                "tecnico_responsable",
                "pagado",
            )
        }
        logger.error(
            "DOC_EDIT_INVALID pk=%s POST_KEYS=%s POST_CORE=%s",
            getattr(documento, "pk", None),
            list(request.POST.keys()),
            posted,
        )

        # Errores detallados
        logger.error(
            "DOC_EDIT_ERRORS non_field=%s fields=%s",
            form.non_field_errors(),
            form.errors.as_json(),
        )

        # Detección de campos deshabilitados (no llegan en POST)
        missing = [
            name
            for name in form.fields.keys()
            if name not in request.POST and form.fields[name].required
        ]
        logger.error("DOC_EDIT_MISSING_REQUIRED_FIELDS=%s", missing)

        # NO redirigir; render con errores visibles
        messages.error(request, "Corrige los errores del formulario.")

        # URLs para navegación
        from django.urls import NoReverseMatch, reverse

        try:
            settings_url = reverse("taller:company_settings")
        except NoReverseMatch:
            settings_url = ""

        # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "documentos/documento_form.html",
        getattr(request.user.empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(
        request,
        template_name,
        {
            "form": form,
            "documento": documento,
            "es_edicion": bool(pk),
            "company_country": company_country,
            "today": now().date(),
            "settings_url": settings_url,
        },
        status=422,
    )

    # GET
    form = DocumentoForm(instance=documento, user=request.user)

    # URLs para navegación
    from django.urls import NoReverseMatch, reverse

    try:
        settings_url = reverse("taller:company_settings")
    except NoReverseMatch:
        settings_url = ""

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "documentos/documento_form.html",
        getattr(request.user.empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(
        request,
        template_name,
        {
            "form": form,
            "documento": documento,
            "es_edicion": bool(pk),
            "company_country": company_country,
            "today": now().date(),
            "settings_url": settings_url,
        },
    )
