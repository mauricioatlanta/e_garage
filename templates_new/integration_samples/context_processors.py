def company_context(request):
    empresa = getattr(request.user, "empresa", None)
    country = getattr(empresa, "pais", "CL") if empresa else "CL"
    company_settings = getattr(empresa, "configuracion", None)
    return {
        "country": country,
        "company_settings": company_settings,
        "STATIC_VERSION": "dev",
    }
