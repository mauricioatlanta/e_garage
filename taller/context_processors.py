"""
Context processors para eGarage
"""


def company_branding(request):
    """
    Context processor que agrega información de branding de la empresa
    a todos los templates
    """
    context = {}

    if request.user.is_authenticated:
        try:
            # Intentar obtener la empresa del usuario
            empresa = request.user.empresa
            config = getattr(empresa, "config", None)

            if config:
                # Información de la empresa
                context["COMPANY_NAME"] = config.nombre_publico or empresa.nombre_taller
                context["COMPANY_ADDRESS"] = config.direccion
                context["COMPANY_PHONE"] = config.telefono
                context["COMPANY_EMAIL"] = config.email_contacto
                context["COMPANY_WEBSITE"] = config.sitio_web
                context["COMPANY_TAX_RATE"] = config.tasa_impuesto
                context["COMPANY_LOGO"] = config.logo
                context["COMPANY_CURRENCY"] = config.moneda
                context["COMPANY_TAGLINE"] = config.tagline
                context["COMPANY_BRAND_COLOR"] = config.brand_color

                # Información adicional para templates
                context["company_name"] = context["COMPANY_NAME"]
                context["company_logo_url"] = config.logo.url if config.logo else None
                context["company_color"] = config.brand_color
                context["company_tagline"] = config.tagline

        except Exception:
            # Si no hay empresa o configuración, usar valores por defecto
            context["COMPANY_NAME"] = "eGarage Pro"
            context["company_name"] = "eGarage Pro"
            context["COMPANY_TAX_RATE"] = 0
            context["COMPANY_CURRENCY"] = "USD" if "/us/" in request.path else "CLP"
    else:
        # Usuario no autenticado
        context["COMPANY_NAME"] = "eGarage Pro"
        context["company_name"] = "eGarage Pro"
        context["COMPANY_TAX_RATE"] = 0
        context["COMPANY_CURRENCY"] = "USD" if "/us/" in request.path else "CLP"

    return context
