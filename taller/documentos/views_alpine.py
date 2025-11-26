"""
Vista para crear documentos usando Alpine.js en el frontend.
Procesa JSON de repuestos/servicios enviados desde Alpine.js.
"""

import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from taller.documentos.forms import DocumentoForm
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.models.documento import Documento


@login_required
def crear_documento_alpine(request):
    """
    Vista para crear documentos usando Alpine.js en el frontend.

    Procesa:
    1. Formulario Django estándar para cabeceras (Cliente, Vehículo, etc.)
    2. JSON de repuestos y servicios desde Alpine.js
    3. Calcula totales automáticamente usando recompute_totals()
    """
    # 1. Obtener empresa del usuario (multi-tenant)
    try:
        empresa = request.user.empresa
        if not empresa:
            messages.error(request, "Usuario sin empresa asociada.")
            return redirect("dashboard")  # Ajustar según tu URL
    except AttributeError:
        messages.error(request, "Usuario sin empresa asociada.")
        return redirect("dashboard")

    # 2. Obtener configuración de impuestos según empresa
    country = empresa.pais or "CL"

    # Determinar tasa de impuesto según país
    if country == "CL":
        tasa = Decimal("19.0")  # IVA en Chile
    else:
        # USA/MX: intentar obtener de configuración o usar 0
        try:
            config_empresa = empresa.configuracion  # Si tienes relación
            tasa = getattr(config_empresa, "tasa_iva", Decimal("0.0"))
        except (AttributeError, Exception):
            tasa = Decimal("0.0")

    if request.method == "POST":
        # Crear formulario con datos POST
        form = DocumentoForm(request.POST, user=request.user, country=country)

        # Recuperar JSON strings de Alpine.js
        repuestos_json = request.POST.get("repuestos_data", "[]")
        servicios_json = request.POST.get("servicios_data", "[]")

        # Validar formulario
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Guardar Cabecera del Documento
                    doc = form.save(commit=False)
                    doc.empresa = empresa  # 🔒 Multi-tenant: asignar empresa
                    doc.tax_rate_applied = tasa
                    doc.country = country
                    doc.moneda = "USD" if country == "US" else "CLP"

                    # Generar número de documento si no existe
                    if not doc.numero:
                        doc.generar_numero_documento()

                    doc.save()  # Genera ID y número

                    # 2. Procesar Repuestos (JSON -> BD)
                    repuestos_data = json.loads(repuestos_json)
                    lineas_rep = []

                    for item in repuestos_data:
                        # Validar datos básicos
                        nombre = item.get("nombre", "").strip()
                        if not nombre:
                            continue  # Saltar líneas vacías

                        codigo = item.get("codigo", "").strip()
                        cantidad = int(item.get("cantidad", 1) or 1)
                        precio_unitario = Decimal(str(item.get("precio", 0) or 0))
                        descuento = Decimal(str(item.get("descuento", 0) or 0))
                        repuesto_id = item.get(
                            "repuesto_id"
                        )  # ✅ ID del repuesto si fue seleccionado del autocomplete

                        # Crear línea de repuesto
                        # Si viene repuesto_id, vincular con inventario (permite descontar stock)
                        linea = LineaRepuesto(
                            documento=doc,
                            codigo=codigo,
                            nombre=nombre,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            descuento=descuento,
                        )

                        # ✅ Vincular con repuesto si fue seleccionado del autocomplete
                        if repuesto_id:
                            try:
                                # Validar que el repuesto pertenece a la empresa (multi-tenant)
                                from taller.models.repuesto import Repuesto

                                repuesto = Repuesto.objects.get(id=repuesto_id, empresa=empresa)
                                linea.repuesto = repuesto
                                # Si no viene código, usar el del repuesto
                                if not codigo and repuesto.part_number:
                                    linea.codigo = repuesto.part_number
                            except Repuesto.DoesNotExist:
                                # Repuesto no encontrado o no pertenece a la empresa, ignorar FK
                                pass

                        lineas_rep.append(linea)

                    # Guardar todas las líneas de repuesto de una vez
                    if lineas_rep:
                        LineaRepuesto.objects.bulk_create(lineas_rep)

                    # 3. Procesar Servicios (JSON -> BD)
                    servicios_data = json.loads(servicios_json)
                    lineas_serv = []

                    for item in servicios_data:
                        # Validar datos básicos
                        nombre = item.get("nombre", "").strip()
                        if not nombre:
                            continue  # Saltar líneas vacías

                        cantidad = int(item.get("cantidad", 1) or 1)
                        precio_unitario = Decimal(str(item.get("precio", 0) or 0))
                        descuento = Decimal(str(item.get("descuento", 0) or 0))

                        # Crear línea de servicio
                        lineas_serv.append(
                            LineaServicio(
                                documento=doc,
                                nombre=nombre,
                                cantidad=cantidad,
                                precio_unitario=precio_unitario,
                                descuento=descuento,
                                # servicio_id=... si usas autocomplete y tienes FK
                            )
                        )

                    # Guardar todas las líneas de servicio de una vez
                    if lineas_serv:
                        LineaServicio.objects.bulk_create(lineas_serv)

                    # 4. Aplicar descuento general si existe
                    descuento_general = request.POST.get("descuento", "0")
                    if descuento_general:
                        try:
                            doc.descuento = Decimal(str(descuento_general))
                        except (ValueError, TypeError):
                            doc.descuento = Decimal("0")

                    # 5. Recalcular totales finales y guardar
                    doc.recompute_totals(persist=True)

                    messages.success(
                        request, f"Documento {doc.numero_documento} creado exitosamente."
                    )
                    return redirect("documentos:detalle_documento", pk=doc.pk)

            except json.JSONDecodeError:
                messages.error(request, "Error al procesar datos de repuestos/servicios.")
            except Exception as e:
                messages.error(request, f"Error guardando documento: {str(e)}")
                import traceback

                traceback.print_exc()
        else:
            # Formulario inválido
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        # GET: Mostrar formulario vacío
        form = DocumentoForm(user=request.user, country=country)

    # Preparar contexto para template
    context = {
        "form": form,
        "tasa_impuesto": float(tasa),  # Pasar como float para JavaScript
        "repuestos_json": "[]",  # Vacío si es nuevo documento
        "servicios_json": "[]",
    }

    return render(request, "taller/common/documentos/document_form_alpine_example.html", context)


@login_required
def editar_documento_alpine(request, documento_id):
    """
    Vista para editar documentos usando Alpine.js en el frontend.
    Similar a crear_documento_alpine pero carga datos existentes.
    """
    # 1. Obtener empresa del usuario (multi-tenant)
    try:
        empresa = request.user.empresa
        if not empresa:
            messages.error(request, "Usuario sin empresa asociada.")
            return redirect("dashboard")
    except AttributeError:
        messages.error(request, "Usuario sin empresa asociada.")
        return redirect("dashboard")

    # 2. Obtener documento (con filtro multi-tenant)
    documento = get_object_or_404(
        Documento.objects.select_related(
            "cliente", "vehiculo", "tecnico_responsable"
        ).prefetch_related("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio"),
        id=documento_id,
        empresa=empresa,  # 🔒 Filtro multi-tenant
    )

    # 3. Obtener configuración de impuestos
    country = empresa.pais or "CL"
    tasa = documento.tax_rate_applied or (Decimal("19.0") if country == "CL" else Decimal("0.0"))

    if request.method == "POST":
        form = DocumentoForm(request.POST, instance=documento, user=request.user, country=country)

        # Recuperar JSON strings de Alpine.js
        repuestos_json = request.POST.get("repuestos_data", "[]")
        servicios_json = request.POST.get("servicios_data", "[]")

        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Actualizar cabecera
                    doc = form.save(commit=False)
                    doc.empresa = empresa  # 🔒 Asegurar empresa
                    doc.save()

                    # 2. Eliminar líneas existentes
                    doc.lineas_repuesto.all().delete()
                    doc.lineas_servicio.all().delete()

                    # 3. Procesar nuevos repuestos (igual que en crear)
                    repuestos_data = json.loads(repuestos_json)
                    lineas_rep = []

                    for item in repuestos_data:
                        nombre = item.get("nombre", "").strip()
                        if not nombre:
                            continue

                        codigo = item.get("codigo", "").strip()
                        cantidad = int(item.get("cantidad", 1) or 1)
                        precio_unitario = Decimal(str(item.get("precio", 0) or 0))
                        descuento = Decimal(str(item.get("descuento", 0) or 0))
                        repuesto_id = item.get("repuesto_id")

                        linea = LineaRepuesto(
                            documento=doc,
                            codigo=codigo,
                            nombre=nombre,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            descuento=descuento,
                        )

                        # ✅ Vincular con repuesto si fue seleccionado del autocomplete
                        if repuesto_id:
                            try:
                                from taller.models.repuesto import Repuesto

                                repuesto = Repuesto.objects.get(id=repuesto_id, empresa=empresa)
                                linea.repuesto = repuesto
                                if not codigo and repuesto.part_number:
                                    linea.codigo = repuesto.part_number
                            except Repuesto.DoesNotExist:
                                pass

                        lineas_rep.append(linea)

                    if lineas_rep:
                        LineaRepuesto.objects.bulk_create(lineas_rep)

                    # 4. Procesar nuevos servicios (igual que en crear)
                    servicios_data = json.loads(servicios_json)
                    lineas_serv = []

                    for item in servicios_data:
                        nombre = item.get("nombre", "").strip()
                        if not nombre:
                            continue

                        lineas_serv.append(
                            LineaServicio(
                                documento=doc,
                                nombre=nombre,
                                cantidad=int(item.get("cantidad", 1) or 1),
                                precio_unitario=Decimal(str(item.get("precio", 0) or 0)),
                                descuento=Decimal(str(item.get("descuento", 0) or 0)),
                            )
                        )

                    if lineas_serv:
                        LineaServicio.objects.bulk_create(lineas_serv)

                    # 5. Aplicar descuento general
                    descuento_general = request.POST.get("descuento", "0")
                    if descuento_general:
                        try:
                            doc.descuento = Decimal(str(descuento_general))
                        except (ValueError, TypeError):
                            doc.descuento = Decimal("0")

                    # 6. Recalcular totales
                    doc.recompute_totals(persist=True)

                    messages.success(
                        request, f"Documento {doc.numero_documento} actualizado exitosamente."
                    )
                    return redirect("documentos:detalle_documento", pk=doc.pk)

            except Exception as e:
                messages.error(request, f"Error actualizando documento: {str(e)}")
                import traceback

                traceback.print_exc()
    else:
        # GET: Cargar datos existentes
        form = DocumentoForm(instance=documento, user=request.user, country=country)

        # Serializar repuestos y servicios para Alpine.js
        repuestos_json = json.dumps(
            [
                {
                    "id": linea.pk,
                    "repuesto_id": (
                        linea.repuesto_id if linea.repuesto else None
                    ),  # ✅ Incluir ID del repuesto
                    "codigo": linea.codigo
                    or (linea.repuesto.part_number if linea.repuesto else ""),
                    "nombre": linea.nombre or "",
                    "cantidad": linea.cantidad,
                    "precio": float(linea.precio_unitario),
                    "descuento": float(linea.descuento),
                }
                for linea in documento.lineas_repuesto.all()
            ]
        )

        servicios_json = json.dumps(
            [
                {
                    "id": linea.pk,
                    "nombre": linea.nombre or "",
                    "cantidad": linea.cantidad,
                    "precio": float(linea.precio_unitario),
                    "descuento": float(linea.descuento),
                }
                for linea in documento.lineas_servicio.all()
            ]
        )

    # Preparar contexto
    context = {
        "form": form,
        "tasa_impuesto": float(tasa),
        "repuestos_json": repuestos_json,
        "servicios_json": servicios_json,
    }

    return render(request, "taller/common/documentos/document_form_alpine_example.html", context)
