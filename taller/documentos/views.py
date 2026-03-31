import json
from decimal import Decimal

from django.db import models
from django.http import JsonResponse
from django.shortcuts import redirect


# Vista wrapper para lista de documentos de Chile sin requerir parámetro country
def lista_documentos_cl(request):
    return redirect("documentos:lista_documentos", country="cl")


from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from taller.models.tecnico import Tecnico
from taller.services.empresa_service import get_empresa_safe
from taller.services.documento_service import calcular_totales


# API para crear técnicos (SEGURO)
@login_required
@require_POST
def api_crear_tecnico(request):
    """
    API segura para crear técnicos.
    - Requiere autenticación (@login_required)
    - Solo acepta POST (@require_POST)
    - Usa empresa del usuario autenticado (no del cliente)
    """
    try:
        data = json.loads(request.body.decode())
        nombre = (data.get("nombre") or "").strip()

        if not nombre:
            return JsonResponse({"error": "Nombre requerido"}, status=400)

        # Usar empresa del usuario autenticado (seguridad)
        empresa = get_empresa_safe(request)
        if not empresa:
            return JsonResponse({"error": "Usuario sin empresa asociada"}, status=400)

        tecnico = Tecnico.objects.create(
            empresa=empresa,
            nombre=nombre,
            activo=True,
        )

        return JsonResponse(
            {
                "ok": True,
                "id": tecnico.id,
                "nombre": tecnico.nombre,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Alias para autocompletar servicios por nombre
from taller.models.repuesto import Repuesto


# Autocompletado de repuestos para documentos
def autocomplete_repuesto(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"results": []}, safe=False)
    repuestos = Repuesto.objects.filter(
        models.Q(nombre__icontains=q) | models.Q(part_number__icontains=q)
    )[:20]
    data = {
        "results": [
            {
                "id": r.pk,
                "nombre": r.nombre,
                "partnumber": getattr(r, "part_number", None),
                "precio": float(getattr(r, "precio_venta", 0)),
                "precio_venta": float(getattr(r, "precio_venta", 0)),
                "precio_compra": float(getattr(r, "precio_compra", 0)),
            }
            for r in repuestos
        ]
    }
    return JsonResponse(data, safe=False)


from taller.servicios.models import Servicio


# Autocompletado de servicios para documentos
def autocomplete_servicio(request):
    q = request.GET.get("q", "").strip()

    # Obtener empresa del usuario
    empresa = get_empresa_safe(request)
    if not empresa:
        return JsonResponse([], safe=False)

    # Filtrar servicios por empresa y búsqueda
    servicios = Servicio.objects.filter(empresa=empresa)

    if q:
        servicios = servicios.filter(
            models.Q(nombre__icontains=q) | models.Q(categoria__code__icontains=q)
        )

    servicios = servicios.order_by("nombre")[:20]

    data = [
        {
            "id": s.pk,
            "nombre": s.nombre,
            "descripcion": f"{s.categoria} - {s.nombre}",
            "precio": 15000,  # Precio por defecto, ya que el modelo no tiene campo precio
        }
        for s in servicios
    ]
    return JsonResponse(data, safe=False)


# Autocompletado de otros servicios (servicios externos)
def autocomplete_otro_servicio(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)

    # Buscar en líneas de otros servicios existentes para sugerir
    from taller.models.lineas_documento import LineaOtroServicio

    lineas_existentes = (
        LineaOtroServicio.objects.filter(
            models.Q(nombre__icontains=q) | models.Q(empresa_externa__icontains=q)
        )
        .values("nombre", "empresa_externa", "costo_interno", "precio_cliente")
        .distinct()[:20]
    )

    data = []
    for linea in lineas_existentes:
        data.append(
            {
                "id": f"existing_{len(data)}",
                "nombre": linea["nombre"],
                "empresa_externa": linea["empresa_externa"] or "",
                "costo_interno": float(linea["costo_interno"] or 0),
                "precio_cliente": float(linea["precio_cliente"] or 0),
                "tipo": "existing",
            }
        )

    return JsonResponse(data, safe=False)


# API para crear servicios sobre la marcha
@csrf_exempt
def api_crear_servicio(request):
    if request.method != "POST":
        return JsonResponse({"error": "Solo se permite POST"}, status=405)

    try:
        data = json.loads(request.body.decode())
        nombre = data.get("nombre", "").strip()
        precio = data.get("precio", 0)
        descripcion = data.get("descripcion", "").strip()

        if not nombre:
            return JsonResponse({"error": "El nombre del servicio es obligatorio"}, status=400)

        # Verificar si ya existe
        servicio_existente = Servicio.objects.filter(nombre__iexact=nombre).first()
        if servicio_existente:
            return JsonResponse(
                {
                    "id": servicio_existente.pk,
                    "nombre": servicio_existente.nombre,
                    "precio": float(getattr(servicio_existente, "precio", 0)),
                    "descripcion": getattr(servicio_existente, "descripcion", ""),
                    "creado": False,
                    "mensaje": "El servicio ya existía",
                }
            )

        # Crear nuevo servicio
        servicio = Servicio.objects.create(nombre=nombre, precio=precio, descripcion=descripcion)

        return JsonResponse(
            {
                "id": servicio.pk,
                "nombre": servicio.nombre,
                "precio": float(getattr(servicio, "precio", 0)),
                "descripcion": getattr(servicio, "descripcion", ""),
                "creado": True,
                "mensaje": "Servicio creado exitosamente",
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# Alias para autocompletar servicios por nombre
autocomplete_servicio_nombre = autocomplete_servicio


from taller.models.clientes import Cliente


# Autocompletado de clientes para documentos
def autocomplete_cliente(request):
    q = request.GET.get("q", "").strip()

    # Obtener empresa del usuario autenticado
    empresa = get_empresa_safe(request)

    # Si no hay empresa, retornar vacío
    if not empresa:
        return JsonResponse({"results": []})

    # Filtrar clientes por empresa
    clientes = Cliente.objects.filter(empresa=empresa)

    # Si hay término de búsqueda, filtrar por él
    if q:
        clientes = clientes.filter(
            models.Q(nombre__icontains=q)
            | models.Q(apellido__icontains=q)
            | models.Q(email__icontains=q)
            | models.Q(telefono__icontains=q)
        )[:20]
    else:
        # Si no hay término, mostrar los primeros 20 clientes
        clientes = clientes[:20]

    data = {
        "results": [
            {
                "id": c.pk,
                "text": f"{c.nombre} {c.apellido or ''} - {c.telefono or 'Sin teléfono'}",
                "nombre": c.nombre,
                "apellido": c.apellido,
                "email": c.email,
                "telefono": c.telefono,
            }
            for c in clientes
        ]
    }
    return JsonResponse(data, safe=False)


from taller.models.vehiculos import Vehiculo


# Devuelve los vehículos asociados a un cliente (por cliente_id) con filtrado de empresa
def obtener_vehiculos_por_cliente(request):
    cliente_id = request.GET.get("cliente_id")
    if not cliente_id:
        return JsonResponse([], safe=False)

    # Obtener empresa del usuario autenticado
    empresa = get_empresa_safe(request)
    if not empresa:
        return JsonResponse([], safe=False)

    # Filtrar vehículos por cliente y empresa
    vehiculos = Vehiculo.objects.filter(cliente_id=cliente_id, cliente__empresa=empresa).values(
        "id", "patente", "marca_id", "modelo_id"
    )

    return JsonResponse(list(vehiculos), safe=False)


import logging

log = logging.getLogger(__name__)

from .views_cbv import (
    DocumentoCreateView,
    DocumentoDetailView,
    DocumentoListView,
    DocumentoUpdateView,
)


def lista_documentos(request, *args, **kwargs):
    log.info("FBV shim: lista_documentos")
    return DocumentoListView.as_view()(request, *args, **kwargs)


def ver_documento(request, *args, **kwargs):
    log.info("FBV shim: ver_documento")
    return DocumentoDetailView.as_view()(request, *args, **kwargs)


def crear_documento(request, *args, **kwargs):
    log.info("FBV shim: crear_documento")
    return DocumentoCreateView.as_view()(request, *args, **kwargs)


def editar_documento(request, *args, **kwargs):
    log.info("FBV shim: editar_documento")
    return DocumentoUpdateView.as_view()(request, *args, **kwargs)


import os

# IMPORTS PESADOS (weasyprint / xhtml2pdf) deben cargarse de forma perezosa
# porque al importar el módulo a nivel de módulo pueden fallar dependencias
# externas (p.ej. pyhanko) y bloquear el arranque del servidor.
# Se realizan imports locales dentro de las funciones que generan PDFs.

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from taller.documentos.forms import DocumentoForm
from taller.documentos.models import DetalleDocumento
from taller.models.documento import Documento
from taller.utils.export_utils import DocumentoPDFExporter


@login_required
def crear_documento(request):
    print("[DEBUG CREAR] ========== VERSIÓN CORREGIDA - INICIO CREAR DOCUMENTO ==========")
    print(f"[DEBUG CREAR] Usuario: {request.user.username}")
    print(f"[DEBUG CREAR] Método: {request.method}")

    # Obtener empresa del usuario (común para GET y POST)
    empresa = get_empresa_safe(request)
    if not empresa:
        return redirect("/")
    print(f"[DEBUG CREAR] Empresa obtenida: {empresa.nombre_taller}")

    if request.method == "POST":
        print("[DEBUG CREAR] ===== PROCESANDO POST =====")
        post_data = request.POST.copy()
        print(f"[DEBUG CREAR] Datos POST recibidos: {list(post_data.keys())}")
        print(f"[DEBUG CREAR] json_items: {post_data.get('json_items')}")

        # Manejar mecánico (si es texto, crear mecánico nuevo)
        mecanico_id = post_data.get("mecanico")
        if mecanico_id and not mecanico_id.isdigit():
            from taller.models.tecnico import Tecnico

            mecanico_obj, _ = Tecnico.objects.get_or_create(nombre=mecanico_id, empresa=empresa)
            post_data["mecanico"] = mecanico_obj.pk
            print(
                f"[DEBUG CREAR] Mecánico creado/encontrado: {mecanico_obj.nombre} (ID: {mecanico_obj.pk})"
            )

        form = DocumentoForm(post_data, empresa=empresa, user=request.user)
        if form.is_valid():
            print("[DEBUG CREAR] Formulario válido")
            documento = form.save(commit=False)
            documento.empresa = empresa

            # Generar número de documento si no existe
            if not documento.numero_documento:
                tipo = documento.tipo.lower().replace(" ", "_")
                count = Documento.objects.filter(tipo=documento.tipo, empresa=empresa).count() + 1
                documento.numero = count
                print(f"[DEBUG CREAR] Número generado: {documento.numero_documento}")

            documento.save()
            form.save_m2m()

            # Procesar ítems desde JSON (repuestos y servicios)
            json_items = post_data.get("json_items")
            print(f"[DEBUG CREAR] json_items recibido: {json_items}")
            if json_items is not None and json_items.strip() not in ["", "[]", "null"]:
                try:
                    items = json.loads(json_items)
                    print(f"[DEBUG CREAR] Items parseados: {len(items)} items")
                    from taller.models.lineas_documento import (
                        LineaOtroServicio,
                        LineaRepuesto,
                        LineaServicio,
                    )

                    for item in items:
                        print(f"[DEBUG CREAR] Procesando item: {item}")
                        tipo = item.get("tipo")
                        nombre = item.get("nombre", "").strip()
                        precio = float(item.get("precio", 0))

                        if tipo == "repuesto" and nombre and precio > 0:
                            LineaRepuesto.objects.create(
                                documento=documento,
                                codigo=item.get("partnumber", "").strip(),
                                nombre=nombre,
                                cantidad=int(item.get("cantidad", 1)),
                                precio_unitario=precio,
                            )
                            print(f"[DEBUG CREAR] ✅ Repuesto guardado: {nombre} (${precio})")

                        elif tipo == "servicio" and nombre and precio > 0:
                            LineaServicio.objects.create(
                                documento=documento,
                                nombre=nombre,
                                precio_unitario=precio,
                                cantidad=int(item.get("cantidad", 1)),
                            )
                            print(f"[DEBUG CREAR] ✅ Servicio guardado: {nombre} (${precio})")

                        elif tipo == "otro_servicio" and nombre and precio > 0:
                            # Buscar o crear el servicio en el catálogo por nombre localizado
                            from taller.servicios.models import Servicio, ServicioName

                            servicio_obj = Servicio.objects.filter(
                                names__label__iexact=nombre, names__language="es"
                            ).first()
                            if not servicio_obj:
                                # Crear servicio y nombre localizado
                                from taller.servicios.models import SubcategoriaServicio

                                subcat = SubcategoriaServicio.objects.filter(
                                    code="especiales", country="CL"
                                ).first()
                                servicio_obj = Servicio.objects.create(
                                    subcategoria=subcat, country="CL", tipo="externo"
                                )
                                ServicioName.objects.create(
                                    servicio=servicio_obj,
                                    language="es",
                                    label=nombre,
                                    is_default=True,
                                )
                                print(
                                    f"[DEBUG CREAR] ➕ Nuevo otro servicio creado en catálogo: {nombre}"
                                )

                            LineaOtroServicio.objects.create(
                                documento=documento,
                                servicio=servicio_obj,
                                nombre_servicio=nombre,
                                empresa_externa=item.get("empresa", "").strip(),
                                costo_interno=int(item.get("costo", 0)),
                                precio_cliente=int(precio),
                                observaciones=item.get("observaciones", "").strip(),
                            )
                            print(
                                f"[DEBUG CREAR] ✅ Otro servicio guardado: {nombre} - {item.get('empresa', '')} (${precio})"
                            )

                        else:
                            print(
                                f"[DEBUG CREAR] Item ignorado por datos incompletos o inválidos: {item}"
                            )

                except Exception as e:
                    print(f"❌ Error procesando json_items: {e}")
                    import traceback

                    traceback.print_exc()
            else:
                print("[DEBUG CREAR] json_items es None o vacío - no se recibieron items")

            # Recalcular totales del documento tras crear/modificar líneas
            documento.recompute_totals(persist=True)

            # Redirigir al listado de documentos después de crear exitosamente
            print("[DEBUG CREAR] ✅ DOCUMENTO CREADO EXITOSAMENTE - REDIRIGIENDO AL LISTADO")
            return redirect("documentos:lista_documentos")
        else:
            print(f"[DEBUG CREAR] Formulario inválido: {form.errors}")
            print("[DEBUG CREAR] ❌ DOCUMENTO NO CREADO - ERRORES EN FORMULARIO")

            # Agregar mensajes de error para mostrar al usuario
            from django.contrib import messages

            messages.error(request, f"Error al crear documento: {form.errors}")

            return redirect("documentos:lista_documentos")
    else:
        # GET: Mostrar formulario vacío
        from datetime import date

        hoy = date.today().strftime("%Y-%m-%d")
        form = DocumentoForm(initial={"fecha": hoy}, empresa=empresa, user=request.user)

    # Cargar mecánicos activos del taller
    from taller.models.tecnico import Tecnico

    mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)

    # 🚀 BISTURÍ: Determinar país desde la empresa (no desde la URL)
    country = "cl" if (getattr(empresa, "pais", "") or "").upper() == "CL" else "us"
    print(f"[DEBUG CREAR] País derivado de empresa: {country}")

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "documentos/crear_documento.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(
        request,
        template_name,
        {
            "form": form,
            "mecanicos": mecanicos,
            "tecnicos": mecanicos,  # Alias para compatibilidad con templates
            "es_edicion": False,
            "country": country,  # 🚀 BISTURÍ: Pasar país desde empresa
            "company_country": getattr(request, "company_country", None),  # viene del middleware
        },
    )


def _country_from_request(request):
    """Extrae el país desde la URL del request"""
    path = request.path
    if path.startswith("/cl/"):
        return "CL"
    elif path.startswith("/us/"):
        return "US"
    else:
        return "CL"  # fallback por defecto


@login_required
def ver_documento(request, documento_id):
    print(f"[DEBUG VER] Solicitando documento ID: {documento_id}")
    print(f"[DEBUG VER] Usuario: {request.user.username}")

    # Obtener el país desde la URL
    country = _country_from_request(request)
    print(f"[DEBUG VER] País detectado: {country}")

    # Verificar que el documento pertenece a la empresa del usuario
    empresa = get_empresa_safe(request)
    if not empresa:
        print("[DEBUG VER] Usuario sin empresa asociada")
        from django.http import Http404

        raise Http404("Documento no encontrado")
    print(f"[DEBUG VER] Empresa del usuario: {empresa.nombre_taller}")

    # 🔒 SEGURIDAD: Filtrar por empresa desde el inicio para aislamiento multi-tenant
    # Verificar si el documento existe y pertenece a la empresa del usuario
    if not Documento.objects.filter(id=documento_id, empresa=empresa).exists():
        print(
            f"[DEBUG VER] ❌ Documento {documento_id} NO pertenece a la empresa {empresa.nombre_taller}"
        )
        from django.http import Http404

        raise Http404(f"Documento {documento_id} no encontrado")

    print(f"[DEBUG VER] ✅ Documento {documento_id} pertenece a la empresa {empresa.nombre_taller}")

    documento = get_object_or_404(
        Documento.objects.select_related(
            "cliente", "vehiculo", "tecnico_responsable", "empresa"
        ).prefetch_related(
            "lineas_repuesto__repuesto",
            "lineas_servicio__servicio",
            "lineas_otro_servicio__servicio_externo",
        ),
        id=documento_id,
        empresa=empresa,
    )
    print(f"[DEBUG VER] Documento encontrado: {documento.numero_documento}")

    # Obtener líneas del documento usando prefetch
    repuestos = documento.lineas_repuesto.all()
    servicios = documento.lineas_servicio.all()
    otros_servicios = documento.lineas_otro_servicio.all()

    print(f"[DEBUG VER] Repuestos encontrados: {repuestos.count()}")
    print(f"[DEBUG VER] Servicios encontrados: {servicios.count()}")
    print(f"[DEBUG VER] Otros servicios encontrados: {otros_servicios.count()}")
    for rep in repuestos:
        precio_rep = getattr(rep, "precio_unitario", getattr(rep, "precio", 0))
        cantidad_rep = getattr(rep, "cantidad", 1)
        print(
            f"[DEBUG VER]   - {getattr(rep, 'nombre', 'Repuesto')}: ${precio_rep} x {cantidad_rep} (ID: {rep.id})"
        )

    print(f"[DEBUG VER] Servicios encontrados: {servicios.count()}")
    for serv in servicios:
        precio_serv = getattr(serv, "precio_unitario", getattr(serv, "precio", 0))
        print(f"[DEBUG VER]   - {getattr(serv, 'nombre', 'Servicio')}: ${precio_serv}")

    print(f"[DEBUG VER] Otros servicios encontrados: {otros_servicios.count()}")
    for otro in otros_servicios:
        nombre_otro = getattr(otro, "nombre", getattr(otro, "nombre_servicio", "Otro servicio"))
        precio_otro = getattr(otro, "precio_cliente", getattr(otro, "precio", 0))
        print(
            f"[DEBUG VER]   - {nombre_otro} ({getattr(otro, 'empresa_externa', '')}): ${precio_otro}"
        )

    totales = calcular_totales(documento)
    print("DEBUG TOTAL:", totales)

    subtotal_repuestos = totales["total_repuestos"]
    subtotal_servicios = totales["total_servicios"]
    subtotal_otros_servicios = totales["total_otros"]
    subtotal = totales["subtotal"]
    iva = totales["iva"]
    total = totales["total"]

    print(
        f"[DEBUG VER] Totales calculados - Repuestos: ${subtotal_repuestos}, Servicios: ${subtotal_servicios}, Otros: ${subtotal_otros_servicios}, IVA: ${iva}, Total: ${total}"
    )
    print(
        f"[DEBUG VER] Tipos de datos - subtotal_repuestos: {type(subtotal_repuestos)}, iva: {type(iva)}, total: {type(total)}"
    )
    print(
        f"[DEBUG VER] Valores exactos - subtotal_repuestos: {subtotal_repuestos}, iva: {iva}, total: {total}"
    )

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "documentos/ver_documento_nuevo.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(
        request,
        template_name,
        {
            "documento": documento,
            "lineas_repuesto": repuestos,
            "lineas_servicio": servicios,
            "lineas_otro_servicio": otros_servicios,
            "repuestos": repuestos,  # Mantener compatibilidad
            "servicios": servicios,  # Mantener compatibilidad
            "otros_servicios": otros_servicios,  # Mantener compatibilidad
            "subtotal_repuestos": subtotal_repuestos,
            "subtotal_servicios": subtotal_servicios,
            "subtotal_otros_servicios": subtotal_otros_servicios,
            "subtotal": subtotal,
            "iva": iva,
            "total": total,
            "country": country,
        },
    )


@login_required
def lista_documentos(request):
    # Obtener el país desde la URL
    country = _country_from_request(request)

    # Filtrar documentos por empresa del usuario
    empresa = get_empresa_safe(request)
    if not empresa:
        return redirect("/")

    from django.db.models import Count, DecimalField, F, IntegerField, Sum, Value
    from django.db.models.functions import Coalesce

    documentos = (
        Documento.objects.filter(empresa=empresa)
        .select_related(
            "cliente", "vehiculo", "tecnico_responsable", "empresa"
        )  # Optimización para FKs
        .annotate(
            # CONTEOS de líneas (para mostrar en columnas)
            rep_count=Count("lineas_repuesto", distinct=True),
            serv_count=Count("lineas_servicio", distinct=True),
            otros_count=Count("lineas_otro_servicio", distinct=True),
            # SUMAS monetarias (para totales)
            sum_rep=Coalesce(
                Sum(
                    F("lineas_repuesto__cantidad")
                    * F("lineas_repuesto__precio_unitario")
                    * (1 - F("lineas_repuesto__descuento") / 100),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
            ),
            sum_serv=Coalesce(
                Sum(
                    F("lineas_servicio__cantidad")
                    * F("lineas_servicio__precio_unitario")
                    * (1 - F("lineas_servicio__descuento") / 100),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
            ),
            sum_out=Coalesce(
                Sum(
                    F("lineas_otro_servicio__precio_cliente") * F("lineas_otro_servicio__cantidad"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
            ),
        )
        .annotate(total_general_anotado=F("sum_rep") + F("sum_serv") + F("sum_out"))
        .order_by("-fecha_emision", "-id")  # Ordenar por fecha descendente
    )

    # Calcular totales para el dashboard - SOLO FACTURAS Y BOLETAS
    total_facturas = sum(
        doc.total_general_anotado
        for doc in documentos
        if doc.total_general_anotado and doc.tipo in ["FAC", "BOL"]
    )
    count_facturas = documentos.filter(tipo__in=["FAC", "BOL"]).count()

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "documentos/lista_documentos.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(
        request,
        template_name,
        {
            "documentos": documentos,
            "country": country,
            "total_facturas": total_facturas,
            "count_facturas": count_facturas,
        },
    )


@login_required
def editar_documento(request, documento_id):
    # Verificar que el documento pertenece a la empresa del usuario
    empresa = get_empresa_safe(request)
    if not empresa:
        return redirect("/")
    documento = get_object_or_404(
        Documento.objects.select_related(
            "cliente", "vehiculo", "tecnico_responsable"
        ).prefetch_related("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio"),
        id=documento_id,
        empresa=empresa,
    )

    if request.method == "POST":
        print(f"[DEBUG EDICIÓN] POST data recibido: {list(request.POST.keys())}")
        print(f"[DEBUG EDICIÓN] json_items: {request.POST.get('json_items')}")

        # Procesar mecánico nuevo si es necesario (igual que en crear_documento)
        post_data = request.POST.copy()
        mecanico_nombre = post_data.get("mecanico")
        if mecanico_nombre and not mecanico_nombre.isdigit():
            # Si el valor no es un ID, es un nombre nuevo o existente
            from taller.models.tecnico import Tecnico

            mecanico_obj, _ = Tecnico.objects.get_or_create(nombre=mecanico_nombre, empresa=empresa)
            post_data["mecanico"] = mecanico_obj.pk
            print(
                f"[DEBUG EDICIÓN] Mecánico creado/encontrado: {mecanico_obj.nombre} (ID: {mecanico_obj.pk})"
            )
        elif mecanico_nombre and mecanico_nombre.isdigit():
            # Si es un ID, mantenerlo como está pero validar que pertenece a la empresa
            try:
                from taller.models.tecnico import Tecnico

                mecanico_obj = Tecnico.objects.get(
                    pk=int(mecanico_nombre), empresa=empresa
                )  # 🔒 FILTRO EMPRESA
                post_data["mecanico"] = mecanico_obj.pk
            except Tecnico.DoesNotExist:
                pass

        form = DocumentoForm(post_data, instance=documento)
        if form.is_valid():
            print("[DEBUG EDICIÓN] Formulario válido")
            documento = form.save()
            json_items = request.POST.get("json_items")
            print(f"[DEBUG EDICIÓN] json_items recibido: {json_items}")
            if json_items is not None and json_items.strip() not in ["", "[]", "null"]:
                try:
                    items = json.loads(json_items)
                    print(f"[DEBUG EDICIÓN] Items parseados: {len(items)} items")
                    from taller.models.lineas_documento import (
                        LineaOtroServicio,
                        LineaRepuesto,
                        LineaServicio,
                    )

                    repuestos_anteriores = documento.lineas_repuesto.count()
                    servicios_anteriores = documento.lineas_servicio.count()
                    otros_servicios_anteriores = documento.lineas_otro_servicio.count()
                    documento.lineas_repuesto.all().delete()
                    documento.lineas_servicio.all().delete()
                    documento.lineas_otro_servicio.all().delete()
                    print(
                        f"[DEBUG EDICIÓN] Eliminados {repuestos_anteriores} repuestos, {servicios_anteriores} servicios y {otros_servicios_anteriores} otros servicios anteriores"
                    )
                    for item in items:
                        print(f"[DEBUG EDICIÓN] Procesando item: {item}")
                        tipo = item.get("tipo")
                        nombre = item.get("nombre", "").strip()
                        precio = float(item.get("precio", 0))
                        if tipo == "repuesto" and nombre and precio > 0:
                            LineaRepuesto.objects.create(
                                documento=documento,
                                codigo=item.get("partnumber", "").strip(),
                                nombre=nombre,
                                cantidad=int(item.get("cantidad", 1)),
                                precio_unitario=precio,
                                descuento=float(item.get("descuento", 0)),
                            )
                            print(f"[DEBUG EDICIÓN] ✅ Repuesto guardado: {nombre} (${precio})")
                        elif tipo == "servicio" and nombre and precio > 0:
                            LineaServicio.objects.create(
                                documento=documento,
                                codigo=item.get("partnumber", "").strip(),
                                nombre=nombre,
                                precio_unitario=precio,
                                cantidad=int(item.get("cantidad", 1)),
                                descuento=float(item.get("descuento", 0)),
                            )
                            print(f"[DEBUG EDICIÓN] ✅ Servicio guardado: {nombre} (${precio})")
                        elif tipo == "otro_servicio" and nombre and precio > 0:
                            # Buscar o crear el servicio en el catálogo por nombre localizado
                            from taller.servicios.models import Servicio, ServicioName

                            servicio_obj = Servicio.objects.filter(
                                names__label__iexact=nombre, names__language="es"
                            ).first()
                            if not servicio_obj:
                                from taller.servicios.models import SubcategoriaServicio

                                subcat = SubcategoriaServicio.objects.filter(
                                    code="especiales", country="CL"
                                ).first()
                                servicio_obj = Servicio.objects.create(
                                    subcategoria=subcat, country="CL", tipo="externo"
                                )
                                ServicioName.objects.create(
                                    servicio=servicio_obj,
                                    language="es",
                                    label=nombre,
                                    is_default=True,
                                )
                                print(
                                    f"[DEBUG EDICIÓN] ➕ Nuevo otro servicio creado en catálogo: {nombre}"
                                )
                            LineaOtroServicio.objects.create(
                                documento=documento,
                                servicio=servicio_obj,
                                nombre_servicio=nombre,
                                empresa_externa=item.get("empresa", "").strip(),
                                costo_interno=int(item.get("costo", 0)),
                                precio_cliente=int(precio),
                                observaciones=item.get("observaciones", "").strip(),
                            )
                            print(
                                f"[DEBUG EDICIÓN] ✅ Otro servicio guardado: {nombre} - {item.get('empresa', '')} (${precio})"
                            )
                        else:
                            print(
                                f"[DEBUG EDICIÓN] Item ignorado por datos incompletos o inválidos: {item}"
                            )
                except Exception as e:
                    print(f"❌ Error procesando json_items al editar: {e}")
                    import traceback

                    traceback.print_exc()
            else:
                print("[DEBUG EDICIÓN] json_items es None o vacío - no se recibieron items")

            # Recalcular totales del documento tras crear/modificar líneas
            documento.recompute_totals(persist=True)

            return redirect("documentos:editar_documento", documento_id=documento.id)
        else:
            print(f"[DEBUG EDICIÓN] Formulario inválido: {form.errors}")
    else:
        # GET request - crear formulario para edición
        form = DocumentoForm(instance=documento)

    # Obtener líneas del documento usando prefetch
    servicios = documento.lineas_servicio.all()
    repuestos = documento.lineas_repuesto.all()
    otros_servicios = documento.lineas_otro_servicio.all()
    print(f"[DEBUG EDITAR] Servicios encontrados: {servicios.count()}")
    for serv in servicios:
        precio_serv = getattr(serv, "precio_unitario", getattr(serv, "precio", 0))
        print(f"[DEBUG EDITAR]   - {getattr(serv, 'nombre', 'Servicio')}: ${precio_serv}")
    print(f"[DEBUG EDITAR] Otros servicios encontrados: {otros_servicios.count()}")
    for otro in otros_servicios:
        nombre_otro = getattr(otro, "nombre", getattr(otro, "nombre_servicio", "Otro servicio"))
        precio_otro = getattr(otro, "precio_cliente", getattr(otro, "precio", 0))
        print(
            f"[DEBUG EDITAR]   - {nombre_otro} ({getattr(otro, 'empresa_externa', '')}): ${precio_otro}"
        )

    from taller.utils.totales import totales_chile

    # Usar el nuevo helper de totales
    resumen = totales_chile(repuestos, servicios)
    subtotal_repuestos = resumen["subtotal_repuestos"]
    subtotal_servicios = resumen["subtotal_servicios"]
    iva = resumen["iva"]
    total = resumen["total"]
    subtotal = subtotal_repuestos + subtotal_servicios
    subtotal_otros_servicios = sum(
        getattr(o, "precio_cliente", getattr(o, "precio", 0)) for o in otros_servicios
    )

    # Cargar mecánicos activos del taller
    from taller.models.tecnico import Tecnico

    mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "documentos/editar_documento_nuevo.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(
        request,
        template_name,
        {
            "form": form,
            "documento": documento,  # Pasar documento al template
            "servicios": servicios,
            "repuestos": repuestos,
            "otros_servicios": otros_servicios,
            "subtotal_repuestos": subtotal_repuestos,
            "subtotal_servicios": subtotal_servicios,
            "subtotal_otros_servicios": subtotal_otros_servicios,
            "subtotal": subtotal,
            "iva": iva,
            "total": total,
            "editando": True,  # Indicar que estamos editando
            "mecanicos": mecanicos,
            "tecnicos": mecanicos,  # Alias para compatibilidad con templates
            "es_edicion": bool(documento.pk),
            "company_country": getattr(request, "company_country", None),  # viene del middleware
        },
    )


@login_required
def eliminar_documento(request, documento_id):
    # Verificar que el documento pertenece a la empresa del usuario
    try:
        empresa = request.user.empresa
        documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
    except AttributeError:
        # Si no tiene empresa asociada, no puede eliminar ningún documento
        from django.http import Http404

        raise Http404("Documento no encontrado")

    # Solo permitir eliminación si el usuario tiene permisos
    if request.method == "GET":
        try:
            numero_doc = documento.numero_documento
            tipo_doc = documento.tipo_documento
            documento.delete()
            from django.contrib import messages

            messages.success(
                request, f"Documento {tipo_doc} #{numero_doc} eliminado correctamente."
            )
        except Exception as e:
            from django.contrib import messages

            messages.error(request, f"Error al eliminar el documento: {str(e)}")

    return redirect("documentos:lista_documentos", country=empresa.pais.lower())


@csrf_exempt
def editar_detalle_documento(request):
    data = json.loads(request.body)
    detalle = get_object_or_404(DetalleDocumento, id=data["id"])
    campo = data["campo"]
    valor = float(data["valor"])

    if campo in ["cantidad", "precio_venta"]:
        setattr(detalle, campo, valor)
        detalle.save()
        subtotal = detalle.cantidad * detalle.precio_venta
        return JsonResponse({"valor": valor, "subtotal": int(subtotal)})

    return JsonResponse({"error": "Campo inválido"}, status=400)


def total_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    return JsonResponse(
        {
            "total_repuestos": documento.total_repuestos(),
            "total_servicios": documento.total_servicios(),
            "iva": documento.iva(),
            "total_general": documento.total_general(),
        }
    )


@require_GET
@login_required
@csrf_exempt
@csrf_exempt
def numero_documento_auto(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa

        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={"nombre_taller": f"Taller de {request.user.username}"},
        )

    tipo = request.GET.get("tipo")
    if not tipo:
        return JsonResponse({"error": "Tipo no proporcionado"}, status=400)

    # Filtrar por empresa para generar número correcto
    count = (
        Documento.objects.filter(tipo_documento=tipo, empresa=empresa).count() + 1
    )  # 🔒 FILTRO EMPRESA
    tipo_key = tipo.lower().replace(" ", "_")[:3].upper()
    numero = f"{tipo_key}-{count:05d}"

    return JsonResponse({"numero": numero})


@login_required
def exportar_documento_pdf(request, documento_id):
    """
    Exporta un documento en PDF usando el nuevo template futurista y
    la utilería centralizada DocumentoPDFExporter.
    """
    empresa = getattr(request.user, "empresa", None)
    # 🔒 SEGURIDAD: Filtrar por empresa desde el inicio para aislamiento multi-tenant
    if empresa is not None:
        queryset = Documento.objects.filter(empresa=empresa)
    else:
        queryset = Documento.objects.none()

    documento = get_object_or_404(queryset, id=documento_id)

    try:
        exporter = DocumentoPDFExporter(documento, request=request)
        return exporter.generar_response_pdf()
    except ImportError as exc:
        err_msg = f"PDF generation not available: {exc}"
        return HttpResponse(err_msg, status=500, content_type="text/plain; charset=utf-8")


def enviar_por_whatsapp(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)

    # Renderizar PDF y guardar archivo
    template = get_template("taller/documentos/documento_pdf.html")
    html_string = template.render({"documento": documento})
    # Importar weasyprint de forma perezosa (evita fallos en startup si no está instalado)
    try:
        from weasyprint import HTML
    except Exception as e:
        err_msg = f"PDF generation not available (weasyprint import failed): {e}"
        print(err_msg)
        return HttpResponse(err_msg, status=500, content_type="text/plain")

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # Guardar el archivo en /media/pdfs/
    nombre_archivo = f"documento_{documento.numero}.pdf"
    path_archivo = os.path.join(settings.MEDIA_ROOT, "pdfs", nombre_archivo)

    os.makedirs(os.path.dirname(path_archivo), exist_ok=True)
    with open(path_archivo, "wb") as f:
        f.write(pdf)

    # Preparar mensaje de WhatsApp
    telefono = documento.cliente.telefono.replace("+", "").replace(" ", "")
    url_pdf = request.build_absolute_uri(f"{settings.MEDIA_URL}pdfs/{nombre_archivo}")
    mensaje = f"Hola {documento.cliente.nombre}, puedes ver tu {documento.tipo} aquí: {url_pdf}"
    enlace_whatsapp = f"https://wa.me/56{telefono}?text={mensaje.replace(' ', '%20')}"

    return redirect(enlace_whatsapp)


def enviar_documento_whatsapp(request, documento_id):
    """
    Vista para enviar documento por WhatsApp
    """
    import re

    from django.http import JsonResponse

    # Use the Documento model imported at module level instead of re-importing it here
    # (the module-level import is present earlier in this file)

    try:
        documento = Documento.objects.get(id=documento_id, empresa=request.user.empresa)
    except Documento.DoesNotExist:
        return JsonResponse({"success": False, "error": "Documento no encontrado"}, status=404)

    # Verificar que el cliente tenga teléfono
    if not documento.cliente.telefono:
        return JsonResponse(
            {
                "success": False,
                "error": "El cliente no tiene número de teléfono registrado",
            }
        )

    # Limpiar y validar número de teléfono
    telefono = (
        documento.cliente.telefono.replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    # Validar formato chileno
    if not re.match(r"^(\+56|56)?[2-9]\d{8}$", telefono):
        return JsonResponse(
            {
                "success": False,
                "error": "Número de teléfono inválido. Debe ser un número chileno válido",
            }
        )

    # Formatear número para WhatsApp
    if not telefono.startswith("56"):
        telefono = "56" + telefono

    # Crear mensaje personalizado
    mensaje = f"""Hola {documento.cliente.nombre},

Adjunto encontrará el documento del taller.

📄 {documento.get_tipo_display()} #{documento.numero_documento}
🏢 {documento.empresa.nombre_taller}
📅 Fecha: {documento.fecha_emision.strftime('%d/%m/%Y')}
💰 Total: ${documento.total_general():,.0f}

Para ver el documento completo, visite:
{request.build_absolute_uri(f'/cl/documentos/{documento.id}/')}

¡Gracias por confiar en nuestros servicios!"""

    # Crear URL de WhatsApp (codificando el mensaje)
    from urllib.parse import quote

    mensaje_url = quote(mensaje, safe="")
    url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_url}"

    return JsonResponse(
        {
            "success": True,
            "url_whatsapp": url_whatsapp,
            "telefono": telefono,
            "mensaje": mensaje,
        }
    )
