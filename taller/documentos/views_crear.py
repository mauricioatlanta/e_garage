import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)

from taller.models.clientes import Cliente
from taller.models.sequence import DocumentSequence
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio
from taller.utils.dal_helpers import get_template_by_country
from taller.documentos.utils.template_selector import template_crear

from .forms import DocumentoForm
from .formsets import OtroServicioFormSet, RepuestoFormSet, ServicioFormSet


from taller.documentos.utils.prefix import doc_prefix

def _prefix(tipo):
    """Mapea tipos de documento a prefijos de numeración"""
    return doc_prefix(tipo)


def build_context(request, form=None, rep_fs=None, serv_fs=None, otro_fs=None):
    """
    Usar SIEMPRE este builder en GET y en POST inválido para evitar
    'context' incompleto que deje el template 'en blanco'.
    """
    try:
        empresa = request.user.empresa
        country = getattr(empresa, "pais", "CL") if empresa else "CL"
    except AttributeError:
        country = "CL"

    ctx = {
        "form": form or DocumentoForm(user=request.user),
        "rep_fs": rep_fs or RepuestoFormSet(prefix="rep"),
        "serv_fs": serv_fs or ServicioFormSet(prefix="serv"),
        "otro_fs": otro_fs or OtroServicioFormSet(prefix="otr"),
        "country": country,
        "tecnicos": (
            Tecnico.objects.filter(empresa=empresa).order_by("nombre")
            if empresa
            else Tecnico.objects.none()
        ),
        "clientes": (
            Cliente.objects.filter(empresa=empresa).order_by("nombre")
            if empresa
            else Cliente.objects.none()
        ),
        "vehiculos": (
            Vehiculo.objects.filter(empresa=empresa).order_by("patente")
            if empresa
            else Vehiculo.objects.none()
        ),
        "servicios": (
            Servicio.objects.filter(empresa=empresa).order_by("nombre")
            if empresa
            else Servicio.objects.none()
        ),
        "today": timezone.now().date(),
    }
    return ctx


@login_required
@transaction.atomic
def crear_documento(request):
    """Vista robusta para crear documentos con formsets - NUNCA deja pantalla en blanco"""

    logger.debug("========== INICIO CREAR DOCUMENTO ==========")
    logger.debug(f"Usuario: {request.user.username}")
    logger.debug(f"Método: {request.method}")

    try:
        # Obtener empresa del usuario (común para GET y POST)
        try:
            empresa = request.user.empresa
            print(
                f"[DOC][DEBUG] Empresa obtenida: {empresa.nombre_taller if empresa else 'None'}"
            )
        except AttributeError:
            empresa = None
            logger.warning("Usuario sin empresa")

        if request.method == "POST":
            logger.debug("Procesando POST...")
            logger.debug(f"Datos recibidos: {dict(request.POST)}")

            # Crear formularios con datos POST
            doc_form = DocumentoForm(request.POST, user=request.user)
            rep_fs = RepuestoFormSet(request.POST, prefix="rep")
            serv_fs = ServicioFormSet(request.POST, prefix="serv")
            otro_fs = OtroServicioFormSet(request.POST, prefix="otr")

            # Configurar empresa para formsets
            for form in rep_fs.forms:
                form.empresa = empresa
            for form in serv_fs.forms:
                form.empresa = empresa
            for form in otro_fs.forms:
                form.empresa = empresa

            # Validar todos los formularios
            forms_valid = all(
                [
                    doc_form.is_valid(),
                    rep_fs.is_valid(),
                    serv_fs.is_valid(),
                    otro_fs.is_valid(),
                ]
            )

            logger.debug(f"Formularios válidos: {forms_valid}")

            if forms_valid:
                logger.debug("Todos los formularios son válidos, guardando...")

                try:
                    # Crear documento
                    doc = doc_form.save(commit=False)
                    doc.empresa = empresa

                    # Numeración automática
                    if not doc.numero:
                        n = DocumentSequence.next(empresa, doc.tipo)
                        doc.correlativo = n
                        pref = {"OT": "OT", "FAC": "F", "PRES": "P"}.get(doc.tipo, "D")
                        doc.numero = f"{pref}{n:03d}"
                        logger.debug(f"Número generado: {doc.numero}")

                    # Configurar campos automáticos
                    doc.country = getattr(empresa, "pais", "CL")
                    doc.moneda = (
                        getattr(
                            getattr(empresa, "configuracion", None), "moneda", "CLP"
                        )
                        or "CLP"
                    )
                    if not doc.estado:
                        doc.estado = "EMITIDO"  # default seguro

                    # Validar coherencia cliente-vehículo
                    cid = doc_form.cleaned_data.get("cliente").id
                    vid = (
                        doc_form.cleaned_data.get("vehiculo").id
                        if doc_form.cleaned_data.get("vehiculo")
                        else None
                    )
                    if (
                        vid
                        and not Vehiculo.objects.filter(
                            id=vid, cliente_id=cid, empresa=empresa
                        ).exists()
                    ):
                        doc_form.add_error(
                            "vehiculo",
                            "El vehículo no pertenece al cliente seleccionado.",
                        )
                        raise ValidationError(
                            "El vehículo no pertenece al cliente seleccionado."
                        )

                    # Configurar IVA para Chile
                    if getattr(doc, "country", "CL") == "CL":
                        doc.tax_rate_applied = 19

                    # Guardar documento
                    doc.save()
                    logger.debug(f"Documento guardado con ID: {doc.id}")

                    # Guardar líneas
                    rep_fs.instance = doc
                    rep_fs.save()
                    logger.debug("Líneas de repuestos guardadas")

                    serv_fs.instance = doc
                    serv_fs.save()
                    logger.debug("Líneas de servicios guardadas")

                    otro_fs.instance = doc
                    otro_fs.save()
                    logger.debug("Líneas de otros servicios guardadas")

                    # Recalcular totales en servidor (autoridad)
                    try:
                        doc.recalcular_totales()
                        doc.save(
                            update_fields=[
                                "neto_repuestos",
                                "neto_servicios",
                                "tax_amount",
                                "total",
                            ]
                        )
                        logger.debug(f"Totales recalculados: {doc.total}")
                    except Exception as e:
                        logger.warning(f"Error al recalcular totales: {e}")

                    messages.success(
                        request, f"Documento {doc.numero} creado correctamente."
                    )
                    url = reverse("taller:documentos:lista_documentos")
                    logger.debug(f"Redirect exitoso a: {url}")
                    return redirect(url)

                except Exception as e:
                    logger.error(f"Error al guardar documento: {e}", exc_info=True)
                    messages.error(request, f"Error al guardar documento: {str(e)}")
                    # Re-renderizar con contexto completo
                    ctx = build_context(request, doc_form, rep_fs, serv_fs, otro_fs)
                    return render(
                        request,
                        "taller/cl/es/documentos/crear_documento.html",
                        ctx,
                        status=500,
                    )

            # Si hay errores, re-render con errores visibles (nunca en blanco)
            logger.debug("Formularios inválidos, mostrando errores...")
            logger.debug(f"DOC ERR: {doc_form.errors.as_json() if doc_form.errors else 'N/A'}")
            logger.debug(f"REP ERR: {rep_fs.errors if rep_fs.errors else 'N/A'}")
            logger.debug(f"SERV ERR: {serv_fs.errors if serv_fs.errors else 'N/A'}")
            logger.debug(f"OTR ERR: {otro_fs.errors if otro_fs.errors else 'N/A'}")

            ctx = build_context(request, doc_form, rep_fs, serv_fs, otro_fs)
            template = template_crear(country)
            return render(request, template, ctx, status=400)

        # GET - Mostrar formularios vacíos
        logger.debug("Procesando GET...")
        ctx = build_context(request)
        template = template_crear(country)
        return render(request, template, ctx)

    except Exception as e:
        # En desarrollo, deja rastro y evita respuesta vacía
        logger.error(f"Error inesperado: {repr(e)}", exc_info=True)
        import traceback

        traceback.print_exc()
        messages.error(request, f"Error inesperado al crear documento: {str(e)}")
        ctx = build_context(request)
        template = template_crear(country)
        return render(request, template, ctx, status=500)


@login_required
def buscar_clientes_ajax(request):
    """Vista AJAX para buscar clientes por nombre o email"""
    if request.method == "GET":
        query = request.GET.get("q", "").strip()
        empresa = request.user.empresa

        if not query or len(query) < 2:
            return HttpResponse("[]", content_type="application/json")

        # Buscar clientes que coincidan con la consulta (nombre, apellido o teléfono)
        clientes = (
            Cliente.objects.filter(empresa=empresa)
            .filter(
                models.Q(nombre__icontains=query)
                | models.Q(apellido__icontains=query)
                | models.Q(telefono__icontains=query)
            )
            .order_by("nombre", "apellido")[:10]
        )  # Limitar a 10 resultados

        # Formatear resultados para JSON
        resultados = []
        for cliente in clientes:
            # Crear nombre completo
            nombre_completo = f"{cliente.nombre} {cliente.apellido}".strip()

            # Crear texto de búsqueda con información relevante
            info_adicional = []
            if cliente.telefono:
                info_adicional.append(f"📞 {cliente.telefono}")
            if cliente.email:
                info_adicional.append(f"📧 {cliente.email}")

            info_text = (
                " | ".join(info_adicional)
                if info_adicional
                else "Sin información adicional"
            )

            resultados.append(
                {
                    "id": cliente.id,
                    "nombre": cliente.nombre,
                    "apellido": cliente.apellido or "",
                    "nombre_completo": nombre_completo,
                    "email": cliente.email or "",
                    "telefono": cliente.telefono or "",
                    "text": f"{nombre_completo} ({info_text})",
                }
            )

        import json

        return HttpResponse(json.dumps(resultados), content_type="application/json")

    return HttpResponse("[]", content_type="application/json")
