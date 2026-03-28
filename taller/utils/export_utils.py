"""
Utilidades para exportación de documentos a PDF, Excel y otros formatos
"""

import io
from datetime import datetime
from decimal import Decimal

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill

from django.apps import apps
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template

from taller.context_processors.company_branding_unified import company_branding
from taller.context_processors.company_header import company_header
from taller.models.company_settings import CompanySettings


class DocumentoPDFExporter:
    """Clase para exportar documentos a PDF con formato profesional"""

    def __init__(self, documento, request=None):
        self.documento = documento
        self.request = request

    def _get_empresa_config(self):
        """
        Obtiene la empresa y su configuración respetando los distintos nombres
        y módulos donde pueda estar declarada ConfiguracionEmpresa.
        """

        empresa = getattr(self.documento, "empresa", None)
        if not empresa:
            return None, None

        config_empresa = None

        # Primero probar atributos comunes en el modelo Empresa
        posibles_attrs = (
            "config",
            "configuracion",
            "configuracion_empresa",
            "settings",
            "ajustes",
        )
        for attr in posibles_attrs:
            conf = getattr(empresa, attr, None)
            if conf:
                config_empresa = conf
                break

        # Fallback: buscar el modelo via apps registry
        if config_empresa is None:
            try:
                ConfiguracionEmpresa = apps.get_model("taller", "ConfiguracionEmpresa")
            except LookupError:
                ConfiguracionEmpresa = None

            if ConfiguracionEmpresa is not None:
                config_empresa = ConfiguracionEmpresa.objects.filter(empresa=empresa).first()

        return empresa, config_empresa

    def generar_pdf(self):
        """Genera un PDF del documento completo"""
        # Template HTML para el PDF
        template = get_template("taller/documentos/pdf_template.html")

        empresa, config_empresa = self._get_empresa_config()

        branding_ctx = company_branding(self.request) if self.request else {}
        header_ctx = company_header(self.request) if self.request else {}

        company_settings = None
        request_user = getattr(self.request, "user", None) if self.request else None
        if request_user and request_user.is_authenticated:
            try:
                company_settings = CompanySettings.objects.get(user=request_user)
            except CompanySettings.DoesNotExist:
                pass
        if not company_settings and empresa and getattr(empresa, "user", None):
            try:
                company_settings = CompanySettings.objects.get(user=empresa.user)
            except CompanySettings.DoesNotExist:
                pass

        def _safe_logo_url(obj):
            logo_field = getattr(obj, "logo", None)
            if not logo_field:
                return ""
            url = getattr(logo_field, "url", "")
            return url or ""

        empresa_logo_url = _safe_logo_url(empresa) if empresa else ""
        config_logo_url = _safe_logo_url(config_empresa) if config_empresa else ""
        empresa_tagline = getattr(empresa, "lema", "") if empresa else ""
        config_tagline = getattr(config_empresa, "tagline", "") if config_empresa else ""
        settings_tagline = getattr(company_settings, "tagline", "") if company_settings else ""

        company_name = (
            (company_settings.company_name if company_settings else "")
            or branding_ctx.get("company_name")
            or (config_empresa.nombre_publico if config_empresa else "")
            or (getattr(empresa, "nombre_taller", "") if empresa else "")
            or (getattr(empresa, "empresa", "") if empresa else "")
            or "Taller sin nombre"
        )

        company_address = (
            header_ctx.get("COMPANY_ADDRESS")
            or (company_settings.address if company_settings else "")
            or (config_empresa.direccion if config_empresa else "")
            or (
                str(config_empresa.legal_address)
                if config_empresa and config_empresa.legal_address
                else ""
            )
            or (getattr(empresa, "direccion", "") if empresa else "")
            or ""
        )

        company_phone = (
            header_ctx.get("COMPANY_PHONE")
            or (company_settings.phone if company_settings else "")
            or (config_empresa.telefono if config_empresa else "")
            or (getattr(empresa, "telefono", "") if empresa else "")
            or ""
        )

        company_email = (
            header_ctx.get("COMPANY_EMAIL")
            or (company_settings.email if company_settings else "")
            or (config_empresa.email_contacto if config_empresa else "")
            or (getattr(empresa, "email", "") if empresa else "")
            or ""
        )

        company_site = (
            header_ctx.get("COMPANY_WEBSITE")
            or header_ctx.get("COMPANY_SITE")
            or (company_settings.website if company_settings else "")
            or (config_empresa.sitio_web if config_empresa else "")
            or (getattr(empresa, "sitio_web", "") if empresa else "")
            or ""
        )

        # Prefetch line items once to avoid multiple queries
        repuestos_qs = list(self.documento.lineas_repuesto.all())
        servicios_qs = list(self.documento.lineas_servicio.all())
        otros_servicios_qs = list(self.documento.lineas_otro_servicio.all())

        # Calcular totales usando la propiedad subtotal que ya considera descuentos
        total_repuestos = sum(Decimal(str(r.subtotal)) for r in repuestos_qs)
        total_servicios = sum(Decimal(str(s.subtotal)) for s in servicios_qs)
        total_otros_servicios = sum(Decimal(str(os.subtotal)) for os in otros_servicios_qs)

        # Contexto con todos los datos del documento
        context = {
            "documento": self.documento,
            "repuestos": repuestos_qs,
            "servicios": servicios_qs,
            "otros_servicios": otros_servicios_qs,
            "total_repuestos": total_repuestos,
            "total_servicios": total_servicios,
            "total_otros_servicios": total_otros_servicios,
            "fecha_generacion": datetime.now(),
            "empresa": empresa,
            "config_empresa": config_empresa,  # Agregar configuración de empresa
            "empresa_logo_url": empresa_logo_url,
            "config_logo_url": config_logo_url,
            "empresa_tagline": empresa_tagline,
            "config_tagline": config_tagline or settings_tagline,
            "company_tagline": branding_ctx.get("company_tagline")
            or settings_tagline
            or config_tagline
            or empresa_tagline,
            "company_name": company_name,
            "company_address": company_address,
            "company_phone": company_phone,
            "company_email": company_email,
            "company_site": company_site,
            "COMPANY_NAME": company_name,
            "COMPANY_TAGLINE": branding_ctx.get("company_tagline")
            or settings_tagline
            or config_tagline
            or empresa_tagline,
            "company_website": company_site,
            "company_address": company_address,
            "company_phone": company_phone,
            "company_email": company_email,
            "COMPANY_ADDRESS": company_address,
            "COMPANY_PHONE": company_phone,
            "COMPANY_EMAIL": company_email,
            "COMPANY_WEBSITE": company_site,
        }

        # Calcular totales
        subtotal = (
            context["total_repuestos"]
            + context["total_servicios"]
            + context["total_otros_servicios"]
        )
        # IVA (19% solo sobre repuestos según la lógica de negocio de Chile)
        iva = context["total_repuestos"] * Decimal("0.19") if self.documento.incluir_iva else 0
        total = subtotal + iva

        context.update(
            {
                "subtotal": subtotal,
                "iva": iva,
                "total": total,
            }
        )

        # Renderizar HTML
        base_url = None
        if self.request is not None:
            html_string = template.render(context, request=self.request)
            try:
                base_url = self.request.build_absolute_uri("/")
            except Exception:
                base_url = None
        else:
            html_string = template.render(context)
            base_url = str(getattr(settings, "BASE_DIR", "")) or None

        # Generar PDF con WeasyPrint (importar de forma perezosa)
        try:
            from weasyprint import HTML

            html = HTML(string=html_string, base_url=base_url)
            pdf_file = html.write_pdf()
            return pdf_file
        except Exception as e:  # pragma: no cover - optional dependency
            # Dejar que el llamador decida cómo manejar la ausencia de weasyprint
            raise ImportError(
                f"WeasyPrint is not available: {e}. Install with: pip install weasyprint"
            )

    def generar_response_pdf(self):
        """Genera una respuesta HTTP con el PDF"""
        try:
            pdf_file = self.generar_pdf()
        except ImportError as e:
            # Devolver un 500 informativo para evitar que el servidor explote en startup
            return HttpResponse(
                f"PDF generation not available: {e}",
                status=500,
                content_type="text/plain; charset=utf-8",
            )

        response = HttpResponse(pdf_file, content_type="application/pdf")
        filename = f"{self.documento.tipo_documento}_{self.documento.numero_documento}.pdf"

        disposition = "inline"
        if self.request:
            download_flag = self.request.GET.get("download")
            if download_flag in ("1", "true", "True", "yes"):
                disposition = "attachment"

        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'

        return response


class ReportesExcelExporter:
    """Clase para exportar reportes a Excel"""

    def __init__(self, empresa, fecha_inicio=None, fecha_fin=None):
        self.empresa = empresa
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin

    def exportar_rentabilidad_mensual(self):
        """Exporta reporte de rentabilidad mensual a Excel"""
        from taller.models.documento import Documento

        # Filtrar documentos
        documentos = Documento.objects.filter(empresa=self.empresa)
        if self.fecha_inicio and self.fecha_fin:
            documentos = documentos.filter(fecha__range=[self.fecha_inicio, self.fecha_fin])

        # Crear DataFrame
        data = []
        for doc in documentos:
            total_repuestos = sum(r.total for r in doc.repuestos.all())
            total_servicios = sum(s.precio for s in doc.servicios.all())
            total_otros_servicios = sum(os.precio_cliente for os in doc.otros_servicios.all())
            costos_externos = sum(os.costo_interno for os in doc.otros_servicios.all())
            ganancia_externa = sum(os.ganancia for os in doc.otros_servicios.all())

            subtotal = total_repuestos + total_servicios + total_otros_servicios
            total = subtotal * Decimal("1.19") if doc.incluir_iva else subtotal

            data.append(
                {
                    "Fecha": doc.fecha,
                    "Tipo Documento": doc.tipo_documento,
                    "Número": doc.numero_documento,
                    "Cliente": str(doc.cliente),
                    "Vehículo": str(doc.vehiculo) if doc.vehiculo else "",
                    "Total Repuestos": float(total_repuestos),
                    "Total Servicios Internos": float(total_servicios),
                    "Total Servicios Externos": float(total_otros_servicios),
                    "Costos Externos": float(costos_externos),
                    "Ganancia Servicios Externos": float(ganancia_externa),
                    "Subtotal": float(subtotal),
                    "Total con IVA": float(total),
                    "Margen Servicios Externos %": round(
                        (
                            (ganancia_externa / total_otros_servicios * 100)
                            if total_otros_servicios > 0
                            else 0
                        ),
                        2,
                    ),
                }
            )

        # Crear Excel
        df = pd.DataFrame(data)

        # Crear buffer
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Rentabilidad", index=False)

            # Obtener el workbook y worksheet
            workbook = writer.book
            worksheet = writer.sheets["Rentabilidad"]

            # Estilos
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="007bff", end_color="007bff", fill_type="solid")

            # Aplicar estilos a headers
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")

            # Ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        # Crear respuesta
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        filename = f'rentabilidad_{self.empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


class WhatsAppSender:
    """Utilidades para envío por WhatsApp"""

    @staticmethod
    def generar_enlace_whatsapp(telefono, mensaje, archivo_url=None):
        """Genera enlace de WhatsApp con mensaje predefinido"""
        import urllib.parse

        # Limpiar número de teléfono
        telefono_limpio = "".join(filter(str.isdigit, telefono))
        if telefono_limpio.startswith("9"):
            telefono_limpio = "56" + telefono_limpio
        elif not telefono_limpio.startswith("56"):
            telefono_limpio = "56" + telefono_limpio

        # Crear mensaje
        if archivo_url:
            mensaje_completo = f"{mensaje}\n\nPuedes descargar tu documento aquí: {archivo_url}"
        else:
            mensaje_completo = mensaje

        mensaje_encoded = urllib.parse.quote(mensaje_completo)

        return f"https://wa.me/{telefono_limpio}?text={mensaje_encoded}"


class EmailSender:
    """Utilidades para envío por email"""

    @staticmethod
    def enviar_documento_por_email(documento, email_destinatario, adjuntar_pdf=True):
        """Envía documento por email"""
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string

        # Generar PDF si se solicita
        pdf_content = None
        if adjuntar_pdf:
            exporter = DocumentoPDFExporter(documento)
            pdf_content = exporter.generar_pdf()

        # Preparar email
        subject = (
            f"{documento.tipo_documento} #{documento.numero_documento} - {documento.empresa.nombre}"
        )

        # Renderizar template del email
        email_context = {
            "documento": documento,
            "cliente": documento.cliente,
            "empresa": documento.empresa,
        }

        html_message = render_to_string("taller/emails/documento_email.html", email_context)
        text_message = render_to_string("taller/emails/documento_email.txt", email_context)

        # Crear email
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_destinatario],
        )

        if html_message:
            email.attach_alternative(html_message, "text/html")

        # Adjuntar PDF
        if pdf_content:
            filename = f"{documento.tipo_documento}_{documento.numero_documento}.pdf"
            email.attach(filename, pdf_content, "application/pdf")

        # Enviar
        return email.send()
