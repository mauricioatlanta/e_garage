def country_context(request):
    return {
        "country_code": getattr(request, "country_code", None),
        "lang_code": getattr(request, "lang_code", None),
    }
