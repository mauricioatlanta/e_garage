# taller/documentos/views_ejemplo.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from taller.forms.documento_form import DocumentoForm
from taller.models.documento import Documento


@login_required
def documento_crear(request):
    empresa = getattr(request.user, "empresa", None)
    country = empresa.pais if empresa else "CL"

    if request.method == "POST":
        form = DocumentoForm(request.POST, user=request.user, empresa=empresa, country=country)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Documento creado.")
            return redirect("documentos:editar", pk=obj.pk)
    else:
        form = DocumentoForm(user=request.user, empresa=empresa, country=country)

    context = {
        "form": form,
        "country": country,
        "empresa_nombre": empresa.nombre_taller if empresa else "Mi Empresa",
        "empresa_moneda": (
            {
                "simbolo": "$" if empresa and empresa.pais == "CL" else "$",
                "codigo": "CLP" if empresa and empresa.pais == "CL" else "USD",
                "decimales": 0 if empresa and empresa.pais == "CL" else 2,
            }
            if empresa
            else {"simbolo": "$", "codigo": "CLP", "decimales": 0}
        ),
        "empresa_pais": empresa.pais if empresa else "CL",
    }

    return render(request, "taller/documentos/crear_ejemplo.html", context)


@login_required
def documento_editar(request, pk):
    empresa = getattr(request.user, "empresa", None)
    country = empresa.pais if empresa else "CL"
    obj = get_object_or_404(Documento, pk=pk, empresa=empresa)

    if request.method == "POST":
        form = DocumentoForm(
            request.POST,
            instance=obj,
            user=request.user,
            empresa=empresa,
            country=country,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Documento actualizado.")
            return redirect("documentos:editar", pk=obj.pk)
    else:
        form = DocumentoForm(instance=obj, user=request.user, empresa=empresa, country=country)

    context = {
        "form": form,
        "obj": obj,
        "country": country,
        "empresa_nombre": empresa.nombre_taller if empresa else "Mi Empresa",
        "empresa_moneda": (
            {
                "simbolo": "$" if empresa and empresa.pais == "CL" else "$",
                "codigo": "CLP" if empresa and empresa.pais == "CL" else "USD",
                "decimales": 0 if empresa and empresa.pais == "CL" else 2,
            }
            if empresa
            else {"simbolo": "$", "codigo": "CLP", "decimales": 0}
        ),
        "empresa_pais": empresa.pais if empresa else "CL",
    }

    return render(request, "taller/documentos/editar_ejemplo.html", context)


@login_required
def documento_ver_pdf(request, pk):
    """Vista para generar PDF del documento"""
    empresa = getattr(request.user, "empresa", None)
    country = empresa.pais if empresa else "CL"
    obj = get_object_or_404(Documento, pk=pk, empresa=empresa)

    context = {
        "obj": obj,
        "country": country,
        "pdf_mode": True,  # ← activa estilos de impresión
        "empresa_nombre": empresa.nombre_taller if empresa else "Mi Empresa",
        "empresa_moneda": (
            {
                "simbolo": "$" if empresa and empresa.pais == "CL" else "$",
                "codigo": "CLP" if empresa and empresa.pais == "CL" else "USD",
                "decimales": 0 if empresa and empresa.pais == "CL" else 2,
            }
            if empresa
            else {"simbolo": "$", "codigo": "CLP", "decimales": 0}
        ),
        "empresa_pais": empresa.pais if empresa else "CL",
        "empresa_direccion": getattr(empresa, "direccion", None) if empresa else None,
        "empresa_rut": getattr(empresa, "rut", None) if empresa else None,
        "empresa_ein": getattr(empresa, "ein", None) if empresa else None,
        "verification_code": (
            f"DOC-{obj.id}-{obj.fecha_emision.strftime('%Y%m%d')}"
            if obj.fecha_emision
            else f"DOC-{obj.id}"
        ),
        "verification_qr_url": None,  # Opcional: URL de imagen QR
    }

    return render(request, "taller/documentos/pdf_base.html", context)


@login_required
def documento_pdf_html(request, pk):
    """Vista para generar HTML optimizado para WeasyPrint/wkhtmltopdf"""
    empresa = getattr(request.user, "empresa", None)
    country = empresa.pais if empresa else "CL"
    obj = get_object_or_404(Documento, pk=pk, empresa=empresa)

    context = {
        "obj": obj,
        "country": country,
        "pdf_mode": True,  # ← activa estilos de impresión
        "empresa_nombre": empresa.nombre_taller if empresa else "Mi Empresa",
        "empresa_moneda": (
            {
                "simbolo": "$" if empresa and empresa.pais == "CL" else "$",
                "codigo": "CLP" if empresa and empresa.pais == "CL" else "USD",
                "decimales": 0 if empresa and empresa.pais == "CL" else 2,
            }
            if empresa
            else {"simbolo": "$", "codigo": "CLP", "decimales": 0}
        ),
        "empresa_pais": empresa.pais if empresa else "CL",
        "empresa_direccion": getattr(empresa, "direccion", None) if empresa else None,
        "empresa_rut": getattr(empresa, "rut", None) if empresa else None,
        "empresa_ein": getattr(empresa, "ein", None) if empresa else None,
        "verification_code": (
            f"DOC-{obj.id}-{obj.fecha_emision.strftime('%Y%m%d')}"
            if obj.fecha_emision
            else f"DOC-{obj.id}"
        ),
        "verification_qr_url": None,  # Opcional: URL de imagen QR
    }

    # Generar HTML limpio para PDF
    html = render_to_string("taller/documentos/pdf_base.html", context)

    # Para WeasyPrint, puedes retornar HTML directo
    # Para wkhtmltopdf, puedes usar: wkhtmltopdf --page-size A4 --margin-top 18mm --margin-right 14mm
    return HttpResponse(html, content_type="text/html; charset=utf-8")


@login_required
def documento_pdf_weasyprint(request, pk):
    """Ejemplo de vista que genera PDF con WeasyPrint"""
    empresa = getattr(request.user, "empresa", None)
    country = empresa.pais if empresa else "CL"
    obj = get_object_or_404(Documento, pk=pk, empresa=empresa)

    context = {
        "obj": obj,
        "country": country,
        "pdf_mode": True,  # ← activa estilos de impresión
        "empresa_nombre": empresa.nombre_taller if empresa else "Mi Empresa",
        "empresa_moneda": (
            {
                "simbolo": "$" if empresa and empresa.pais == "CL" else "$",
                "codigo": "CLP" if empresa and empresa.pais == "CL" else "USD",
                "decimales": 0 if empresa and empresa.pais == "CL" else 2,
            }
            if empresa
            else {"simbolo": "$", "codigo": "CLP", "decimales": 0}
        ),
        "empresa_pais": empresa.pais if empresa else "CL",
        "empresa_direccion": getattr(empresa, "direccion", None) if empresa else None,
        "empresa_rut": getattr(empresa, "rut", None) if empresa else None,
        "empresa_ein": getattr(empresa, "ein", None) if empresa else None,
        "verification_code": (
            f"DOC-{obj.id}-{obj.fecha_emision.strftime('%Y%m%d')}"
            if obj.fecha_emision
            else f"DOC-{obj.id}"
        ),
        "verification_qr_url": None,  # Opcional: URL de imagen QR
    }

    # Generar HTML para WeasyPrint
    html = render_to_string("taller/documentos/pdf_base.html", context)

    # Ejemplo de uso con WeasyPrint:
    # from weasyprint import HTML
    # pdf = HTML(string=html).write_pdf()
    # response = HttpResponse(pdf, content_type='application/pdf')
    # response['Content-Disposition'] = f'attachment; filename="documento_{pk}.pdf"'
    # return response

    # Por ahora retornamos HTML para preview
    return HttpResponse(html, content_type="text/html; charset=utf-8")


@login_required
def documento_pdf_wkhtmltopdf(request, pk):
    """Ejemplo de vista que genera PDF con wkhtmltopdf"""
    empresa = getattr(request.user, "empresa", None)
    country = empresa.pais if empresa else "CL"
    obj = get_object_or_404(Documento, pk=pk, empresa=empresa)

    # URLs absolutas para header y footer
    base_url = request.build_absolute_uri("/")
    header_url = request.build_absolute_uri(reverse("pdf:header", args=[pk]))
    footer_url = request.build_absolute_uri(reverse("pdf:footer", args=[pk]))

    context = {
        "obj": obj,
        "country": country,
        "pdf_mode": True,  # ← activa estilos de impresión
        "empresa_nombre": empresa.nombre_taller if empresa else "Mi Empresa",
        "empresa_moneda": (
            {
                "simbolo": "$" if empresa and empresa.pais == "CL" else "$",
                "codigo": "CLP" if empresa and empresa.pais == "CL" else "USD",
                "decimales": 0 if empresa and empresa.pais == "CL" else 2,
            }
            if empresa
            else {"simbolo": "$", "codigo": "CLP", "decimales": 0}
        ),
        "empresa_pais": empresa.pais if empresa else "CL",
        "empresa_direccion": getattr(empresa, "direccion", None) if empresa else None,
        "empresa_rut": getattr(empresa, "rut", None) if empresa else None,
        "empresa_ein": getattr(empresa, "ein", None) if empresa else None,
        "verification_code": (
            f"DOC-{obj.id}-{obj.fecha_emision.strftime('%Y%m%d')}"
            if obj.fecha_emision
            else f"DOC-{obj.id}"
        ),
        "verification_qr_url": None,  # Opcional: URL de imagen QR
        "header_url": header_url,
        "footer_url": footer_url,
    }

    # Generar HTML para wkhtmltopdf
    html = render_to_string("taller/documentos/pdf_base.html", context)

    # Ejemplo de comando wkhtmltopdf:
    # wkhtmltopdf \
    #   --margin-top 28mm --margin-bottom 22mm --margin-left 14mm --margin-right 14mm \
    #   --header-html "{header_url}" \
    #   --footer-html "{footer_url}" \
    #   "{base_url}documentos/{pk}/html/" \
    #   "/tmp/documento_{pk}.pdf"

    return HttpResponse(html, content_type="text/html; charset=utf-8")
