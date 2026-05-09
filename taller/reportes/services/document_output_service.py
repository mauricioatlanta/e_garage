"""
Servicio de salida de documentos (Document Output Service)

Maneja la generación de PDFs y enlaces de WhatsApp para documentos.
Implementa la lógica de "The Fulfillment Loop" - el cliente recibe su comprobante.
"""

import logging
from urllib.parse import quote

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

log = logging.getLogger(__name__)


class DocumentOutputService:
    """
    Servicio dedicado para generar PDFs y enlaces de WhatsApp de documentos.

    Features:
    - Generación de PDF con WeasyPrint (HTML/CSS a PDF)
    - Multi-tenant seguro (usa logo, colores y datos de la empresa)
    - Formato de moneda según país (CL/US/MX)
    - Enlaces de WhatsApp pre-llenados
    - Thread-safe y optimizado
    """

    # Importar WeasyPrint de forma perezosa (evita fallos en startup)
    _weasyprint_available = None

    @staticmethod
    def _check_weasyprint():
        """Verifica si WeasyPrint está disponible"""
        if DocumentOutputService._weasyprint_available is True:
            return True

        try:
            from weasyprint import HTML  # noqa: F401
            from weasyprint.text.fonts import FontConfiguration  # noqa: F401

            DocumentOutputService._weasyprint_available = True
        except ImportError:
            DocumentOutputService._weasyprint_available = False
            log.warning(
                "[DocumentOutputService] WeasyPrint not available. Install with: pip install weasyprint"
            )
        return DocumentOutputService._weasyprint_available

    @staticmethod
    def _get_empresa_config(empresa, request=None):
        """
        Obtiene configuración de la empresa con fallbacks multi-tenant.

        Prioridad:
        1. CompanySettings (configuración por usuario)
        2. ConfiguracionEmpresa (configuración legacy)
        3. Datos directos de Empresa
        """
        config = {}

        # Intentar obtener CompanySettings (nuevo sistema)
        try:
            from taller.models.company_settings import CompanySettings

            company_settings = CompanySettings.objects.filter(user=empresa.user).first()
            if company_settings:
                config["logo"] = company_settings.logo
                config["nombre"] = company_settings.company_name or empresa.nombre_taller
                config["tagline"] = company_settings.tagline or ""
                config["direccion"] = company_settings.address or empresa.direccion or ""
                config["telefono"] = company_settings.phone or empresa.telefono or ""
                config["email"] = company_settings.email or empresa.email or ""
                config["website"] = company_settings.website or ""
                config["primary_color"] = company_settings.primary_color or "#0d6efd"
                config["secondary_color"] = company_settings.secondary_color or "#6c757d"
                config["tax_id"] = company_settings.tax_id or ""
                return config
        except Exception as e:
            log.debug(f"[DocumentOutputService] CompanySettings no disponible: {e}")

        # Intentar obtener ConfiguracionEmpresa (legacy)
        try:
            config_empresa = getattr(empresa, "config", None)
            if config_empresa:
                config["logo"] = config_empresa.logo
                config["nombre"] = config_empresa.nombre_publico or empresa.nombre_taller
                config["tagline"] = config_empresa.tagline or ""
                config["direccion"] = (
                    getattr(config_empresa, "direccion", "") or empresa.direccion or ""
                )
                config["telefono"] = config_empresa.telefono or empresa.telefono or ""
                config["email"] = config_empresa.email_contacto or empresa.email or ""
                config["website"] = getattr(config_empresa, "sitio_web", "") or ""
                config["primary_color"] = getattr(config_empresa, "brand_color", "#0d6efd")
                config["secondary_color"] = "#6c757d"
                config["tax_id"] = (
                    getattr(config_empresa, "rut", "") or getattr(config_empresa, "ein", "") or ""
                )
                return config
        except Exception as e:
            log.debug(f"[DocumentOutputService] ConfiguracionEmpresa no disponible: {e}")

        # Fallback: usar datos directos de Empresa
        config["logo"] = empresa.logo
        config["nombre"] = empresa.nombre_taller
        config["tagline"] = ""
        config["direccion"] = empresa.direccion or ""
        config["telefono"] = empresa.telefono or ""
        config["email"] = empresa.email or ""
        config["website"] = ""
        config["primary_color"] = "#0d6efd"
        config["secondary_color"] = "#6c757d"
        config["tax_id"] = ""

        return config

    @staticmethod
    def _get_currency_config(empresa):
        """Obtiene configuración de moneda según país"""
        pais = (empresa.pais or "CL").upper()

        if pais == "US":
            return {
                "symbol": "US$",
                "code": "USD",
                "decimals": 2,
                "thousands_separator": ",",
                "decimal_separator": ".",
            }
        elif pais == "MX":
            return {
                "symbol": "MX$",
                "code": "MXN",
                "decimals": 2,
                "thousands_separator": ",",
                "decimal_separator": ".",
            }
        else:  # CL (Chile)
            return {
                "symbol": "$",
                "code": "CLP",
                "decimals": 0,
                "thousands_separator": ".",
                "decimal_separator": ",",
            }

    @staticmethod
    def generate_pdf(documento, request=None):
        """
        Genera un objeto PDF en memoria (bytes).

        Args:
            documento: Instancia de Documento
            request: HttpRequest (opcional, necesario para URLs absolutas de imágenes)

        Returns:
            tuple: (pdf_bytes, filename)

        Raises:
            ImportError: Si WeasyPrint no está disponible
            Exception: Si hay error en la generación
        """
        if not DocumentOutputService._check_weasyprint():
            raise ImportError("WeasyPrint is not available. Install with: pip install weasyprint")

        empresa = documento.empresa
        config = DocumentOutputService._get_empresa_config(empresa, request)
        currency = DocumentOutputService._get_currency_config(empresa)

        # Obtener cliente y vehículo
        cliente = documento.cliente
        vehiculo = getattr(documento, "vehiculo", None)

        # Prefetch líneas de documento para optimizar queries
        lineas_repuesto = list(documento.lineas_repuesto.select_related("repuesto").all())
        lineas_servicio = list(documento.lineas_servicio.all())
        lineas_otro_servicio = list(documento.lineas_otro_servicio.all())

        # Datos para el template
        context = {
            "doc": documento,
            "empresa": empresa,
            "cliente": cliente,
            "vehiculo": vehiculo,
            "lineas_repuesto": lineas_repuesto,
            "lineas_servicio": lineas_servicio,
            "lineas_otro_servicio": lineas_otro_servicio,
            "config": config,
            "currency": currency,
            # Helpers para formato
            "MONEDA_SYMBOL": currency["symbol"],
            "MONEDA_CODE": currency["code"],
            # Fecha formateada según país
            "fecha_formateada": documento.fecha_emision.strftime("%d/%m/%Y"),
        }

        # Renderizar HTML
        # Usamos un template específico para impresión (limpio, optimizado para PDF)
        try:
            html_string = render_to_string(
                "taller/documentos/pdf/invoice_template.html", context, request=request
            )
        except Exception as e:
            log.error(f"[DocumentOutputService] Error renderizando template: {e}", exc_info=True)
            raise

        # Generar PDF con WeasyPrint
        try:
            from weasyprint import HTML
            from weasyprint.text.fonts import FontConfiguration

            # Configuración de fuentes
            font_config = FontConfiguration()

            # Base URL para cargar imágenes/logos (vital para servidores)
            base_url = None
            if request:
                try:
                    base_url = request.build_absolute_uri("/")
                except Exception:
                    base_url = None
            elif hasattr(settings, "BASE_URL"):
                base_url = settings.BASE_URL
            else:
                # Fallback: usar MEDIA_URL si está disponible
                base_url = getattr(settings, "MEDIA_URL", None)

            # Crear objeto HTML y generar PDF
            html = HTML(string=html_string, base_url=base_url)
            pdf_bytes = html.write_pdf(font_config=font_config)

            # Generar nombre de archivo
            nombre_cliente = slugify(cliente.nombre) if cliente else "cliente"
            tipo_doc = documento.tipo or "DOC"
            numero_doc = documento.numero or str(documento.id)
            filename = f"{tipo_doc}_{numero_doc}_{nombre_cliente}.pdf"

            log.info(f"[DocumentOutputService] PDF generado: {filename}")
            return pdf_bytes, filename

        except Exception as e:
            log.error(f"[DocumentOutputService] Error generando PDF: {e}", exc_info=True)
            raise

    @staticmethod
    def generate_whatsapp_link(documento, request=None, pdf_url=None):
        """
        Genera un enlace 'wa.me' con un mensaje pre-llenado.

        Args:
            documento: Instancia de Documento
            request: HttpRequest (opcional, para generar URL de PDF)
            pdf_url: URL pública del PDF (opcional, si no se proporciona se intenta generar)

        Returns:
            str: URL de WhatsApp con mensaje pre-llenado, o None si no hay teléfono
        """
        cliente = documento.cliente
        telefono = getattr(cliente, "telefono", None) or getattr(cliente, "phone", None)

        if not telefono:
            log.warning(
                f"[DocumentOutputService] Cliente {cliente.id} no tiene teléfono registrado"
            )
            return None

        # Limpiar teléfono (eliminar caracteres no numéricos)
        # El formato debe ser internacional sin + ni espacios para wa.me
        telefono_limpio = "".join(filter(str.isdigit, str(telefono)))

        # Si el teléfono no empieza con código de país, intentar inferirlo
        # Formato esperado: +56912345678 o 56912345678 o 912345678
        if telefono_limpio.startswith("9") and len(telefono_limpio) == 9:
            # Formato chileno sin código de país: agregar 56
            telefono_limpio = "56" + telefono_limpio
        elif not telefono_limpio.startswith("56") and len(telefono_limpio) >= 8:
            # Si no tiene código de país y tiene al menos 8 dígitos, agregar 56 (Chile por defecto)
            # En el futuro, esto podría detectarse según empresa.pais
            telefono_limpio = "56" + telefono_limpio

        # Obtener datos de la empresa para el mensaje
        empresa = documento.empresa
        config = DocumentOutputService._get_empresa_config(empresa, request)
        nombre_empresa = config.get("nombre", empresa.nombre_taller)

        # Obtener configuración de empresa (plantilla WhatsApp y datos bancarios)
        company_settings = None
        datos_bancarios = None
        plantilla_whatsapp = None
        try:
            from taller.models.company_settings import CompanySettings

            company_settings = CompanySettings.objects.filter(user=empresa.user).first()
            if company_settings:
                if company_settings.bank_details:
                    datos_bancarios = company_settings.bank_details
                if company_settings.whatsapp_template:
                    plantilla_whatsapp = company_settings.whatsapp_template
        except Exception:
            pass

        # Obtener tipo de documento formateado
        tipo_doc = documento.get_tipo_display() or documento.tipo
        numero_doc = documento.numero_documento or documento.numero or str(documento.id)

        # Formatear total según moneda
        currency = DocumentOutputService._get_currency_config(empresa)
        total_formateado = (
            f"{currency['symbol']}{documento.total:,.{currency['decimals']}f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        if currency["decimals"] == 0:
            total_formateado = f"{currency['symbol']}{int(documento.total):,}".replace(",", ".")

        # Generar URL pública del presupuesto (si tiene UUID) o URL del PDF
        # Prioridad: URL pública del presupuesto (si tiene UUID) > URL privada del PDF
        public_url = None
        pdf_url = None

        if request:
            try:
                from django.urls import reverse

                # Intentar URL pública primero (si el documento tiene UUID y es un presupuesto)
                if hasattr(documento, "uuid") and documento.uuid and documento.tipo == "PRES":
                    try:
                        # URL pública del presupuesto (sin autenticación, con botón de aprobación)
                        public_url = request.build_absolute_uri(
                            reverse("publico:ver_presupuesto", kwargs={"uuid": documento.uuid})
                        )
                    except Exception:
                        pass

                # URL del PDF (siempre disponible)
                try:
                    pdf_url = request.build_absolute_uri(
                        reverse("documentos:descargar_pdf", kwargs={"pk": documento.id})
                    )
                except Exception:
                    pass
            except Exception as e:
                log.debug(f"[DocumentOutputService] No se pudo generar URLs: {e}")

        # Construir mensaje personalizado
        # Prioridad: Plantilla personalizada > Mensaje por defecto
        mensaje = None
        if plantilla_whatsapp:
            try:
                # Usar plantilla personalizada con variables
                vehiculo_display = ""
                vehiculo = getattr(documento, "vehiculo", None)
                if vehiculo:
                    marca = getattr(vehiculo, "marca", None)
                    modelo = getattr(vehiculo, "modelo", None)
                    patente = getattr(vehiculo, "patente", "")
                    if marca and modelo:
                        vehiculo_display = f"{marca} {modelo} ({patente})"
                    elif marca:
                        vehiculo_display = f"{marca} ({patente})"
                    else:
                        vehiculo_display = patente or "N/A"

                # URL a usar (prioridad: public_url > pdf_url > "")
                url_display = public_url or pdf_url or ""

                # Reemplazar variables en la plantilla
                mensaje = plantilla_whatsapp.format(
                    cliente=cliente.nombre,
                    vehiculo=vehiculo_display,
                    url=url_display,
                    tipo_doc=tipo_doc,
                    numero_doc=numero_doc,
                    total=total_formateado,
                    empresa=nombre_empresa,
                )
            except (KeyError, ValueError) as e:
                # Si hay error en el formato (variables faltantes o sintaxis incorrecta),
                # usar mensaje por defecto y registrar el error
                log.warning(
                    f"[DocumentOutputService] Error en plantilla WhatsApp personalizada: {e}. "
                    "Usando mensaje por defecto."
                )
                mensaje = None  # Forzar uso de mensaje por defecto

        if not mensaje:
            # Mensaje por defecto (comportamiento original)
            mensaje_partes = [
                f"¡Hola {cliente.nombre}! 👋",
                f"",
                f"Te enviamos tu *{tipo_doc} N°{numero_doc}* de *{nombre_empresa}*.",
                f"",
                f"💰 Total: *{total_formateado}*",
            ]

            # Agregar información del vehículo si está disponible
            vehiculo = getattr(documento, "vehiculo", None)
            if vehiculo:
                mensaje_partes.append(
                    f"🚗 Vehículo: {vehiculo.marca} {vehiculo.modelo} ({vehiculo.patente})"
                )
                mensaje_partes.append("")

            # Agregar link público del presupuesto (si está disponible) o PDF
            if public_url:
                mensaje_partes.append("📄 Puedes revisarlo y aprobarlo aquí:")
                mensaje_partes.append(public_url)
                mensaje_partes.append("")
            elif pdf_url:
                mensaje_partes.append("📄 Puedes descargarlo aquí:")
                mensaje_partes.append(pdf_url)
                mensaje_partes.append("")

            # Agregar datos bancarios si están configurados
            if datos_bancarios:
                mensaje_partes.append("💳 *Datos para transferencia:*")
                mensaje_partes.append(datos_bancarios)
                mensaje_partes.append("")

            mensaje_partes.append("¡Gracias por confiar en nosotros! 🚗✨")
            mensaje = "\n".join(mensaje_partes)

        # Codificar mensaje para URL
        mensaje_encoded = quote(mensaje)

        # Construir URL de WhatsApp
        whatsapp_url = f"https://wa.me/{telefono_limpio}?text={mensaje_encoded}"

        log.info(f"[DocumentOutputService] Enlace WhatsApp generado para {cliente.nombre}")
        return whatsapp_url

    @staticmethod
    def generate_whatsapp_link_comprobante(documento, request=None):
        """
        Genera un enlace de WhatsApp para que el cliente envíe el comprobante de pago al taller.

        Args:
            documento: Instancia de Documento
            request: HttpRequest (opcional, para generar URL)

        Returns:
            str: URL de WhatsApp con mensaje pre-llenado para enviar comprobante al taller
        """
        # Obtener teléfono del TALLER (no del cliente)
        empresa = documento.empresa
        config = DocumentOutputService._get_empresa_config(empresa, request)

        # Intentar obtener teléfono del taller desde CompanySettings o Empresa
        telefono = config.get("telefono") or getattr(empresa, "telefono", None)

        if not telefono:
            log.warning(
                f"[DocumentOutputService] Taller {empresa.id} no tiene teléfono registrado para recibir comprobantes"
            )
            return None

        # Limpiar teléfono
        telefono_limpio = "".join(filter(str.isdigit, str(telefono)))
        if telefono_limpio.startswith("9") and len(telefono_limpio) == 9:
            telefono_limpio = "56" + telefono_limpio
        elif not telefono_limpio.startswith("56") and len(telefono_limpio) >= 8:
            telefono_limpio = "56" + telefono_limpio

        # Obtener datos de la empresa
        nombre_empresa = config.get("nombre", empresa.nombre_taller)
        cliente = documento.cliente

        # Obtener tipo y número de documento
        tipo_doc = documento.get_tipo_display() or documento.tipo
        numero_doc = documento.numero_documento or documento.numero or str(documento.id)

        # Formatear total según moneda
        currency = DocumentOutputService._get_currency_config(empresa)
        total_formateado = (
            f"{currency['symbol']}{documento.total:,.{currency['decimals']}f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        if currency["decimals"] == 0:
            total_formateado = f"{currency['symbol']}{int(documento.total):,}".replace(",", ".")

        # Mensaje para enviar comprobante
        mensaje_partes = [
            f"Hola {nombre_empresa}! 👋",
            f"",
            f"Les envío el comprobante de pago del {tipo_doc} N°{numero_doc}.",
            f"",
            f"📋 Detalles:",
            f"• Cliente: {cliente.nombre} {cliente.apellido or ''}",
            f"• Monto: {total_formateado}",
            f"• Fecha de pago: {timezone.now().strftime('%d/%m/%Y')}",
            f"",
            f"Por favor confirmen la recepción del pago. 🙏",
        ]

        mensaje = "\n".join(mensaje_partes)
        mensaje_encoded = quote(mensaje)

        whatsapp_url = f"https://wa.me/{telefono_limpio}?text={mensaje_encoded}"

        log.info(
            f"[DocumentOutputService] Enlace WhatsApp comprobante generado para enviar a {nombre_empresa}"
        )
        return whatsapp_url
